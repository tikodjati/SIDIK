"""Buku besar audit: hash chain SHA-256 + tanda tangan Ed25519.

entry_hash(n) = SHA-256(entry_hash(n-1) || body(n)); tanda tangan atas entry_hash.
Mengubah, menghapus, atau menyisipkan entri mana pun memutus rantai atau tanda tangan, dan
`verify_chain` melaporkan entri pertama yang bermasalah. Pemotongan ekor rantai tidak dapat
dideteksi tanpa jangkar eksternal; karena itu `verify_chain` mengembalikan `head_hash` untuk
dicatat/dicetak berkala. Kunci tanda tangan di berkas PEM (prototipe); HSM adalah roadmap.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import LedgerEntry

GENESIS_HASH = "0" * 64
_LEDGER_LOCK_KEY = 7342001  # kunci advisory lock PostgreSQL untuk penulisan ledger


def _key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()[:16]


class LedgerKeyMismatch(RuntimeError):
    """Kunci penandatangan di server ini berbeda dengan kunci yang menandatangani ujung rantai.

    Terjadi bila beberapa server memakai database yang sama tetapi kunci berbeda; entri baru
    tak akan bisa diverifikasi oleh server lain, jadi penulisan ditolak."""


class Signer:
    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private = private_key
        self.public_key = private_key.public_key()
        self.key_id = _key_id(self.public_key)

    def sign(self, data: bytes) -> bytes:
        return self._private.sign(data)

    @classmethod
    def load_or_create(cls, path: str | Path, create: bool = True) -> "Signer":
        """Muat kunci dari PEM; buat baru bila belum ada dan `create` (hanya pengembangan)."""
        path = Path(path)
        if not path.exists() and not create:
            raise FileNotFoundError(
                f"kunci ledger {path} tidak ada; minta salinan kunci tim (jangan dibuat baru)"
            )
        if path.exists():
            key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError(f"{path} bukan kunci Ed25519")
            return cls(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        key = Ed25519PrivateKey.generate()
        path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # sistem berkas tanpa izin POSIX
        return cls(key)


@lru_cache(maxsize=1)
def get_signer() -> Signer:
    from app.config import settings

    return Signer.load_or_create(settings.signing_key_path, settings.signing_key_autocreate)


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _entry_hash(prev_hash: str, body: str) -> str:
    return hashlib.sha256(bytes.fromhex(prev_hash) + body.encode("utf-8")).hexdigest()


def append_event(
    session: Session, signer: Signer, event: str, data: dict, actor: str
) -> LedgerEntry:
    """Tambah satu entri ke ujung rantai. Tidak commit: ikut transaksi pemanggil, sehingga
    perubahan bisnis dan catatan auditnya atomik.

    Penulis diserialkan dengan advisory lock PostgreSQL (dilepas saat commit/rollback) dan nomor
    urut ditentukan di sini (last.seq + 1), bukan oleh sequence database: sequence "terbakar"
    saat transaksi dibatalkan dan akan tampak sebagai entri hilang. SELECT ... FOR UPDATE pada
    baris terakhir tidak cukup, karena dua penulis dapat membaca ujung rantai yang sama."""
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _LEDGER_LOCK_KEY})
    last = session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq.desc()).limit(1)).first()
    if last is not None and last.key_id != signer.key_id:
        raise LedgerKeyMismatch(
            f"kunci ledger server ini ({signer.key_id}) berbeda dengan kunci rantai "
            f"({last.key_id}); pakai berkas kunci yang sama dengan anggota tim lain"
        )
    prev_hash = last.entry_hash if last else GENESIS_HASH
    body = canonical_json(
        {"event": event, "actor": actor, "at": datetime.now(UTC).isoformat(), "data": data}
    )
    entry_hash = _entry_hash(prev_hash, body)
    entry = LedgerEntry(
        seq=last.seq + 1 if last else 1,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        body=body,
        signature=signer.sign(bytes.fromhex(entry_hash)).hex(),
        key_id=signer.key_id,
    )
    session.add(entry)
    session.flush()
    return entry


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    entries: int
    head_seq: int | None
    head_hash: str | None
    bad_seq: int | None = None
    reason: str | None = None


def verify_chain(session: Session, public_keys: dict[str, Ed25519PublicKey]) -> VerifyResult:
    """Periksa seluruh rantai dari awal; berhenti di entri pertama yang bermasalah."""
    prev_hash, prev_seq, count = GENESIS_HASH, None, 0
    for entry in session.scalars(select(LedgerEntry).order_by(LedgerEntry.seq)):
        reason = None
        if prev_seq is not None and entry.seq != prev_seq + 1:
            reason = "nomor urut tidak berurutan (entri hilang atau disisipkan)"
        elif entry.prev_hash != prev_hash:
            reason = "prev_hash tidak cocok dengan entri sebelumnya"
        elif _entry_hash(entry.prev_hash, entry.body) != entry.entry_hash:
            reason = "isi entri telah diubah (hash tidak cocok)"
        elif entry.key_id not in public_keys:
            reason = f"kunci penandatangan {entry.key_id} tidak dikenal"
        else:
            try:
                public_keys[entry.key_id].verify(
                    bytes.fromhex(entry.signature), bytes.fromhex(entry.entry_hash)
                )
            except (InvalidSignature, ValueError):
                reason = "tanda tangan tidak valid"
        if reason:
            return VerifyResult(False, count, prev_seq, prev_hash, entry.seq, reason)
        prev_hash, prev_seq, count = entry.entry_hash, entry.seq, count + 1
    return VerifyResult(True, count, prev_seq, prev_hash if count else None)
