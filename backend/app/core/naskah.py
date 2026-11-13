"""Naskah terpadu: satu PDF salinan membawa Lapis 1 (spasi antar-kata) dan Lapis 2 (pilihan kata).
Format rata kanan-kiri seperti naskah dinas; baris akhir paragraf rata kiri.

Pemenggalan baris dikunci memakai varian terlebar tiap slot, jadi semua salinan punya baris
dan jumlah kata per baris yang sama; yang berbeda hanya kata varian dan spasinya. Akibatnya:
- teks yang disalin dari PDF (atau diketik ulang dari kertas) membawa Lapis 2;
- foto PDF membawa keduanya. Dari foto, kata varian dibaca dengan pencocokan bentuk 2D
  (tanpa OCR), lalu teks salinan yang tepat dipakai sebagai referensi untuk mengukur spasi.
Bukti kedua lapis digabung dalam satu dekode. Bila tiap lapis sendiri terbaca tetapi menunjuk
salinan berbeda, hasilnya ditolak (tanda manipulasi).
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np
import pymupdf

from app.core import layer1_visual as l1
from app.core import vision_extractor as vx
from app.core.layer2_semantic import (
    FRAME_BITS,
    HoneyToken,
    Slot,
    demo_template,
    variant_indices,
    variant_scores,
)
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload

FONT_SIZE, LEADING = 9.5, 11.5
Piece = str | int | HoneyToken  # teks tetap, indeks slot, atau honey-token (Lapis 3)
Token = tuple[Piece, ...]  # satu kata cetak (mis. ("akurat", ".") = varian + tanda baca)

# Kunci skor Lapis 2 digeser kelipatan FRAME_BITS agar tak bertabrakan dengan kunci Lapis 1
# tetapi tetap jatuh pada bit frame yang sama di decode_scores (n mod FRAME_BITS).
L2_KEY_OFFSET = FRAME_BITS * 10_000

# Pencocokan bentuk kata varian (dikalibrasi dengan foto simulasi; docs/SPIKE_LAYER1_HASIL.md).
PAD_PT = 1.5  # bingkai putih kiri-kanan templat: "dimaksud" tak cocok di dalam "dimaksudkan"
SEARCH_PX = 30  # jendela pencarian horizontal di sekitar posisi perkiraan
MIN_MATCH = 0.5  # korelasi minimum agar kata dianggap terlihat
MIN_MARGIN = 0.03  # selisih minimum varian terbaik dengan pesaingnya


@dataclass(frozen=True)
class Structure:
    lines: tuple[tuple[Token, ...], ...]
    baselines: tuple[float, ...]
    justified: tuple[bool, ...]  # rata kanan-kiri: semua baris kecuali baris akhir paragraf


def _piece_width(piece: Piece, widest: bool) -> float:
    if isinstance(piece, HoneyToken):  # digit selebar sama: nilai token tak mengubah lebar
        return pymupdf.get_text_length(piece.placeholder, l1.FONT, FONT_SIZE)
    if isinstance(piece, str):
        return pymupdf.get_text_length(piece, l1.FONT, FONT_SIZE)
    variants = demo_template().slots[piece].variants
    if not widest:
        return pymupdf.get_text_length(variants[0], l1.FONT, FONT_SIZE)
    return max(pymupdf.get_text_length(v, l1.FONT, FONT_SIZE) for v in variants)


def _paragraphs() -> list[list[Token]]:
    """Template -> paragraf -> token. Slot yang menempel tanda baca jadi satu token."""
    paragraphs: list[list[Token]] = [[]]
    current: list[Piece] = []

    def flush() -> None:
        if current:
            paragraphs[-1].append(tuple(current))
            current.clear()

    for part in demo_template().parts:
        if isinstance(part, Slot):
            current.append(part.index)
            continue
        if isinstance(part, HoneyToken):
            current.append(part)
            continue
        for m in re.finditer(r"\n|[ \t]+|[^\s]+", part):
            text = m.group()
            if text == "\n":
                flush()
                paragraphs.append([])
            elif text.isspace():
                flush()
            else:
                current.append(text)
    flush()
    while paragraphs and not paragraphs[0]:
        paragraphs.pop(0)
    while paragraphs and not paragraphs[-1]:
        paragraphs.pop()
    return paragraphs


@lru_cache(maxsize=1)
def structure() -> Structure:
    """Baris terkunci: dipatahkan memakai lebar varian terlebar, jadi muat untuk salinan mana pun.
    Jeda antar-paragraf setengah baris agar baris tambahan akibat varian terlebar tetap muat."""
    space = pymupdf.get_text_length(" ", l1.FONT, FONT_SIZE)
    lines: list[tuple[Token, ...]] = []
    baselines: list[float] = []
    justified: list[bool] = []
    y = l1.MARGIN_T + FONT_SIZE
    for paragraph in _paragraphs():
        if not paragraph:
            y += LEADING / 2
            continue
        current: list[Token] = []
        width = 0.0
        for token in paragraph:
            if sum(isinstance(p, int) for p in token) > 1:
                raise ValueError(f"satu kata memuat lebih dari satu slot: {token}")
            w = sum(_piece_width(p, widest=True) for p in token)
            if current and width + space + w > l1.MAX_LINE_W:
                lines.append(tuple(current))
                baselines.append(y)
                justified.append(True)
                y += LEADING
                current, width = [], 0.0
            width = w if not current else width + space + w
            current.append(token)
        lines.append(tuple(current))
        baselines.append(y)
        justified.append(False)  # baris akhir paragraf (dan judul) tetap rata kiri
        y += LEADING
    if y - LEADING > l1.PAGE_H - l1.MARGIN_T:
        raise ValueError(f"naskah tidak muat satu halaman pada {FONT_SIZE} pt")
    return Structure(tuple(lines), tuple(baselines), tuple(justified))


def _token_text(
    token: Token, choice: tuple[int, ...] | dict[int, int], tokens: tuple[str, ...] | None = None
) -> str:
    slots = demo_template().slots

    def text(p: Piece) -> str:
        if isinstance(p, str):
            return p
        if isinstance(p, HoneyToken):
            return tokens[p.index] if tokens else p.placeholder
        return slots[p].variants[choice[p]]

    return "".join(text(p) for p in token)


@lru_cache(maxsize=8)
def layout_for(choice: tuple[int, ...], tokens: tuple[str, ...] | None = None) -> l1.Layout:
    """Tata letak salinan dengan varian terpilih tiap slot dan nilai honey-token (posisi baris
    sama untuk semua salinan)."""
    st = structure()
    lines = tuple(tuple(_token_text(t, choice, tokens) for t in line) for line in st.lines)
    return l1.Layout("naskah", lines, st.baselines, FONT_SIZE, LEADING, st.justified)


def generic_layout() -> l1.Layout:
    """Varian pertama di semua slot: referensi penyelarasan foto dan PDF kontrol."""
    return layout_for(tuple(0 for _ in demo_template().slots))


def copy_choice(copy_id: int) -> tuple[int, ...]:
    return variant_indices(demo_template(), encode_payload(copy_id))


def copy_pdf(
    copy_id: int,
    delta_pt: float,
    tokens: tuple[str, ...] | None = None,
    beacon_url: str | None = None,
) -> bytes:
    """PDF salinan: varian kata (Lapis 2), modulasi spasi (Lapis 1), honey-token (Lapis 3,
    nilai dari registri), dan suar pelacak aktif (Canary Token) untuk `copy_id`."""
    layout = layout_for(copy_choice(copy_id), tokens)
    return l1.render_pdf(layout, encode_payload(copy_id), delta_pt, beacon_url=beacon_url)


@lru_cache(maxsize=1024)
def _word_template(text: str, dpi: int, pad_pt: float = PAD_PT) -> np.ndarray:
    """Render satu kata berbingkai putih, dipotong setinggi pita baris, sedikit diburamkan.
    `pad_pt` = 0 untuk satu digit di tengah angka (tetangganya digit, bukan putih)."""
    k = dpi / 72
    width = pymupdf.get_text_length(text, l1.FONT, FONT_SIZE) + 2 * pad_pt
    base = FONT_SIZE * 1.3
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=FONT_SIZE * 2)
    page.insert_text((pad_pt, base), text, fontname=l1.FONT, fontsize=FONT_SIZE)
    img = l1.rasterize_gray(doc.tobytes(), dpi)
    crop = img[int((base - 0.8 * FONT_SIZE) * k) : int((base + 0.3 * FONT_SIZE) * k)]
    return cv2.GaussianBlur(crop.astype(np.float32), (0, 0), 1.0)


def read_variants(
    flat: np.ndarray, tracked: list[tuple[int, int] | None], dpi: int
) -> dict[int, int]:
    """Varian tiap slot yang terlihat tegas di foto, {indeks slot: indeks varian}.

    Kata dicari dari kiri ke kanan tiap baris; posisi kata berikut diperkirakan dari letak kata
    yang baru ditemukan (lebar varian berbeda menggeser kata sesudahnya). Kata tetap juga
    dicocokkan, hanya untuk menjaga perkiraan posisi."""
    k = dpi / 72
    pad_px = PAD_PT * k
    slots = demo_template().slots
    generic = generic_layout()
    lines = structure().lines
    src = cv2.GaussianBlur(flat.astype(np.float32), (0, 0), 1.0)
    chosen: dict[int, int] = {}
    for li, rows in enumerate(tracked):
        if rows is None:
            continue
        y0, y1 = max(0, rows[0] - 12), min(src.shape[0], rows[1] + 12)
        carry = 0.0  # geseran posisi kata terhadap tata letak generik (px)
        for ti, token in enumerate(lines[li]):
            slot = next((p for p in token if isinstance(p, int)), None)
            n_options = len(slots[slot].variants) if slot is not None else 1
            g_start, g_end = (v * k for v in generic.spans[li][ti])
            found = []
            for j in range(n_options):
                text = _token_text(token, {slot: j} if slot is not None else {})
                tpl = _word_template(text, dpi)
                x0 = int(max(0, g_start + carry - pad_px - SEARCH_PX))
                x1 = int(min(src.shape[1], g_start + carry - pad_px + tpl.shape[1] + SEARCH_PX))
                region = src[y0:y1, x0:x1]
                if region.shape[0] < tpl.shape[0] or region.shape[1] < tpl.shape[1]:
                    continue
                res = cv2.matchTemplate(region, tpl, cv2.TM_CCOEFF_NORMED)
                _, score, _, loc = cv2.minMaxLoc(res)
                start = x0 + loc[0] + pad_px
                found.append((score, j, start, start + tpl.shape[1] - 2 * pad_px))
            if not found:
                continue
            found.sort(reverse=True)
            score, j, start, end = found[0]
            if score < MIN_MATCH:
                continue
            if slot is not None and (len(found) == 1 or score - found[1][0] >= MIN_MARGIN):
                chosen[slot] = j
            carry = end - g_end
    return chosen


TOKEN_SEARCH_PX = 45  # jendela pencarian kata ber-token (posisi dari tata letak varian terbaca)
DIGIT_SEARCH_PX = 4  # sisa geser per digit setelah kata ber-token ditemukan
DIGIT_MIN_MARGIN = 0.05  # digit terbaik harus jelas lebih cocok dari digit lain


def read_tokens(
    flat: np.ndarray,
    tracked: list[tuple[int, int] | None],
    choice: dict[int, int],
    dpi: int,
) -> dict[int, str]:
    """Nilai honey-token yang terbaca tegas dari foto, {indeks token: nilai seperti tercetak}.

    Tanpa OCR: kata ber-token dicari dulu (bentuk angka nol sebagai pengganti), lalu tiap digit
    acak dicocokkan ke bentuk 0-9 pada posisinya (digit selebar sama). Token dengan satu digit
    saja yang ragu dilewati, jadi pembacaan yang salah tak menghasilkan nilai."""
    k = dpi / 72
    pad_px = PAD_PT * k
    layout = layout_for(tuple(choice.get(i, 0) for i in range(len(demo_template().slots))))
    src = cv2.GaussianBlur(flat.astype(np.float32), (0, 0), 1.0)
    digits = {d: _word_template(d, dpi, 0.0) for d in "0123456789"}
    out: dict[int, str] = {}
    for li, rows in enumerate(tracked):
        if rows is None:
            continue
        y0, y1 = max(0, rows[0] - 12), min(src.shape[0], rows[1] + 12)
        for ti, word in enumerate(structure().lines[li]):
            token = next((p for p in word if isinstance(p, HoneyToken)), None)
            if token is None:
                continue
            text = _token_text(word, choice)
            tpl = _word_template(text, dpi)
            start = layout.spans[li][ti][0] * k
            x0 = int(max(0, start - pad_px - TOKEN_SEARCH_PX))
            x1 = int(min(src.shape[1], start - pad_px + tpl.shape[1] + TOKEN_SEARCH_PX))
            region = src[y0:y1, x0:x1]
            if region.shape[0] < tpl.shape[0] or region.shape[1] < tpl.shape[1]:
                continue
            score, loc = cv2.minMaxLoc(cv2.matchTemplate(region, tpl, cv2.TM_CCOEFF_NORMED))[1::2]
            if score < MIN_MATCH:
                continue
            found = x0 + loc[0] + pad_px  # awal kata pada foto (px)
            prefix = "".join(p for p in word[: word.index(token)] if isinstance(p, str))
            value = list(token.placeholder)
            for ci, ch in enumerate(token.pattern):
                if ch != "#":
                    continue
                before = prefix + token.placeholder[:ci]
                cx = found + pymupdf.get_text_length(before, l1.FONT, FONT_SIZE) * k
                cell = src[y0:y1, int(cx - DIGIT_SEARCH_PX) : int(cx + digits["0"].shape[1]
                                                                   + DIGIT_SEARCH_PX)]
                if cell.shape[1] < digits["0"].shape[1] or cell.shape[0] < digits["0"].shape[0]:
                    break
                ranked = sorted(
                    ((cv2.matchTemplate(cell, t, cv2.TM_CCOEFF_NORMED).max(), d)
                     for d, t in digits.items()),
                    reverse=True,
                )
                if ranked[0][0] < MIN_MATCH or ranked[0][0] - ranked[1][0] < DIGIT_MIN_MARGIN:
                    break
                value[ci] = ranked[0][1]
            else:
                out[token.index] = "".join(value)
    return out


def _decode(scores: dict[int, float]) -> tuple[int, int] | None:
    try:
        return decode_scores(scores)
    except PayloadDecodeError:
        return None


@dataclass(frozen=True)
class NaskahResult:
    aligned: np.ndarray
    layer1_scores: dict[int, float]
    layer2_scores: dict[int, float]
    layer1_total: int
    layer2_total: int
    layer1_decoded: tuple[int, int] | None
    layer2_decoded: tuple[int, int] | None
    decoded: tuple[int, int] | None  # gabungan; None bila tak cukup atau bertentangan
    conflict: bool
    tokens: dict[int, str]  # honey-token Lapis 3 yang terbaca, {indeks: nilai}

    @property
    def observed(self) -> int:
        return len(self.layer1_scores) + len(self.layer2_scores)


def analyse_aligned(aligned: np.ndarray, delta_pt: float, dpi: int) -> NaskahResult:
    """Baca kedua lapis dari foto yang sudah diselaraskan ke tata letak generik."""
    generic = generic_layout()
    flat = vx.flatten_illumination(aligned)
    geom = vx.locate_rows(flat, generic, dpi, flattened=True)
    tracked = vx.track_lines(flat, generic, dpi, geom)
    chosen = read_variants(flat, tracked, dpi)
    template = demo_template()
    l2 = variant_scores(template, chosen)
    tokens = read_tokens(flat, tracked, chosen, dpi)
    layout = layout_for(
        tuple(chosen.get(i, 0) for i in range(len(template.slots))),
        tuple(tokens.get(t.index, t.placeholder) for t in template.tokens),
    )
    l1_scores = vx.measure_slot_scores(aligned, layout, delta_pt, dpi, geom, tracked)

    combined = {**l1_scores, **{n + L2_KEY_OFFSET: s for n, s in l2.items()}}
    d1, d2, dc = _decode(l1_scores), _decode(l2), _decode(combined)
    singles = [d for d in (d1, d2) if d is not None]
    conflict = any(d != singles[0] for d in singles) or (
        dc is not None and any(d != dc for d in singles)
    )
    return NaskahResult(
        aligned, l1_scores, l2, layout.total_slots, template.capacity_bits,
        d1, d2, None if conflict else dc, conflict, tokens,
    )


def decode_naskah_photo(
    gray: np.ndarray, delta_pt: float, dpi: int, max_tries: int = 3
) -> NaskahResult | None:
    """Analisis foto PDF salinan. Kandidat penyelarasan dicoba berurutan; berhenti pada yang
    terdekode atau bertentangan (bukti dimanipulasi). None bila kertas/teks tak ditemukan."""
    best: NaskahResult | None = None
    candidates: Iterator[np.ndarray] = vx.align_candidates(gray, generic_layout(), dpi, max_tries)
    for aligned in candidates:
        result = analyse_aligned(aligned, delta_pt, dpi)
        if result.decoded is not None or result.conflict:
            return result
        if best is None or result.observed > best.observed:
            best = result
    return best
