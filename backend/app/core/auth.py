"""Primitif autentikasi: hash kata sandi (scrypt) dan token sesi.

Tanpa dependensi luar agar tetap air-gapped. Parameter scrypt ikut tersimpan di hash, jadi
biayanya bisa dinaikkan nanti tanpa memutus hash lama. Token sesi hanya disimpan dalam bentuk
hash: kebocoran isi tabel sesi tidak memberi sesi yang bisa dipakai.
"""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime

SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
_MAXMEM = 128 * 1024 * 1024


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    encoded = [base64.b64encode(x).decode("ascii") for x in (salt, digest)]
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encoded[0]}${encoded[1]}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return False
        actual = _scrypt(password, base64.b64decode(salt), int(n), int(r), int(p))
        return hmac.compare_digest(actual, base64.b64decode(digest))
    except ValueError:
        return False


def burn_verification_time(password: str) -> None:
    """Lakukan kerja setara verifikasi saat tak ada hash untuk dibandingkan."""
    _scrypt(password, b"sidik-dummy-salt", SCRYPT_N, SCRYPT_R, SCRYPT_P)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("ascii", "ignore")).hexdigest()


def utc(value: datetime) -> datetime:
    """Samakan datetime dari DB ke UTC sadar-zona (SQLite mengembalikan datetime naif)."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value
