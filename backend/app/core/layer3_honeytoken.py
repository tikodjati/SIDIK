"""Lapis 3 (honey-token): angka fiktif yang berbeda per salinan, mis. frekuensi, nomor registrasi,
dan koordinat di naskah.

Nilai diacak saat salinan diterbitkan dan disimpan di registri (unik global), jadi tak bisa
ditebak dari copy_id dan tak butuh kunci rahasia tambahan. Angka ini adalah fakta yang biasanya
tetap dikutip walau kalimatnya diparafrase total, sehingga melengkapi Lapis 1 (spasi) dan Lapis 2
(pilihan kata).

Anti-kolusi: bila beberapa penerima menggabungkan salinannya, token tiap salinan yang ikut muncul
di bocoran menunjuk salinan itu masing-masing. Kebijakan nol salah tuduh: satu salinan baru
dinyatakan teridentifikasi bila >= 2 tokennya cocok, atau Lapis 1/2 menunjuk salinan yang sama.
Satu token saja hanya indikasi.
"""

import re
import secrets
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.layer2_semantic import Template
from app.db.models import Copy, HoneyTokenRow

MIN_TOKENS_ALONE = 2  # token cocok minimal agar satu salinan teridentifikasi tanpa lapis lain
_NUMBER = re.compile(r"\d(?:[.,:/\-]?\d)*")  # angka bertanda baca: 143.275, 143,275, 06.12345


def digits_of(value: str) -> str:
    return re.sub(r"\D", "", value)


def numbers_in(text: str) -> set[str]:
    """Semua angka di teks bukti, hanya digitnya (tahan '143.275' vs '143,275' vs '143275')."""
    return {digits_of(m.group()) for m in _NUMBER.finditer(text)}


def _fill(pattern: str) -> str:
    return "".join(str(secrets.randbelow(10)) if c == "#" else c for c in pattern)


def ensure_tokens(session: Session, copy: Copy, template: Template) -> tuple[str, ...]:
    """Nilai honey-token salinan, urut indeks token. Token yang belum ada (salinan baru, atau
    salinan lama sebelum Lapis 3) dibuat sekarang: acak dan unik terhadap semua token terbit."""
    have = {row.token_index: row.value for row in copy.tokens}
    for token in template.tokens:
        if token.index in have:
            continue
        for _ in range(100):
            value = _fill(token.pattern)
            taken = session.scalar(
                select(HoneyTokenRow.id).where(HoneyTokenRow.digits == digits_of(value))
            )
            if taken is None:
                break
        else:
            raise RuntimeError(f"ruang nilai token '{token.pattern}' hampir habis")
        copy.tokens.append(
            HoneyTokenRow(token_index=token.index, value=value, digits=digits_of(value))
        )
        have[token.index] = value
    session.flush()
    return tuple(have[t.index] for t in template.tokens)


@dataclass(frozen=True)
class TokenHit:
    token_index: int
    value: str
    copy_id: int


def lookup(session: Session, digit_strings: Iterable[str]) -> list[TokenHit]:
    """Token terbit yang angkanya muncul di bukti."""
    wanted = {d for d in digit_strings if d}
    if not wanted:
        return []
    rows = session.scalars(select(HoneyTokenRow).where(HoneyTokenRow.digits.in_(wanted)))
    return sorted(
        (TokenHit(r.token_index, r.value, r.copy_id) for r in rows),
        key=lambda h: (h.copy_id, h.token_index),
    )


@dataclass(frozen=True)
class Verdict:
    identified: tuple[int, ...]  # salinan dengan bukti cukup (>= 2 token, atau lapis 1/2)
    indicated: tuple[int, ...]  # hanya 1 token dan tak dikonfirmasi lapis lain


def judge(hits: list[TokenHit], decoded_copy: int | None) -> Verdict:
    """Gabungkan token dengan hasil dekode Lapis 1/2 (`decoded_copy` = salinan terdaftar hasil
    dekode, atau None). Lebih dari satu salinan teridentifikasi = indikasi kolusi."""
    per_copy = Counter({c: 0 for c in {h.copy_id for h in hits}})
    for copy_id, _ in {(h.copy_id, h.token_index) for h in hits}:
        per_copy[copy_id] += 1
    strong = {c for c, n in per_copy.items() if n >= MIN_TOKENS_ALONE}
    if decoded_copy is not None:
        strong.add(decoded_copy)
    weak = {c for c in per_copy if c not in strong}
    return Verdict(tuple(sorted(strong)), tuple(sorted(weak)))
