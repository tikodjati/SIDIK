"""Lapis 1 (visual): modulasi spasi antar-kata secara diferensial.

Setiap baris punya WORDS_PER_LINE kata, jadi WORDS_PER_LINE-1 spasi. Spasi dikelompokkan
berpasangan (g0, g1): bit 1 -> g0 +delta, g1 -delta; bit 0 sebaliknya. Lebar baris tetap,
jadi tata letak tidak bergeser. Bit ke-n slot disimpan di bit payload (n mod jumlah_bit),
sehingga payload berulang beberapa kali dan hasil ekstraksi digabung (soft vote).

Akibatnya kata ke-(2p+1) bergeser +/-delta terhadap render tanpa modulasi, sedangkan kata
genap tidak bergeser. Dekoder (vision_extractor) mendaftarkan tiap kata ke render referensi
dan membaca bit dari pergeseran kata ganjil terhadap rata-rata dua tetangganya.
"""

import random
from functools import lru_cache

import numpy as np
import pymupdf

PAGE_W, PAGE_H = 595.0, 842.0
MARGIN_L, MARGIN_T = 56.0, 56.0
FONT, FONT_SIZE, LEADING = "helv", 10.0, 13.0
WORDS_PER_LINE = 13
PAIRS_PER_LINE = (WORDS_PER_LINE - 1) // 2
LINES = 56

_VOCAB = (
    "pasukan satuan komando laporan operasi wilayah jaringan naskah dinas tugas sasaran "
    "daerah markas sistem data kode unit tim pos awak alat sandi rahasia kirim terima "
    "salinan cetak arsip surat nomor tanggal dasar maksud tujuan unsur giat rencana"
).split()
MAX_LINE_W = PAGE_W - 2 * MARGIN_L


@lru_cache(maxsize=4)
def build_lines(seed: int = 7) -> list[list[str]]:
    """Template master deterministik (stand-in naskah dinas untuk spike); semua baris muat."""
    rng = random.Random(seed)
    space = pymupdf.get_text_length(" ", FONT, FONT_SIZE)
    lines: list[list[str]] = []
    while len(lines) < LINES:
        words = [rng.choice(_VOCAB) for _ in range(WORDS_PER_LINE)]
        width = sum(pymupdf.get_text_length(w, FONT, FONT_SIZE) for w in words)
        if width + space * (WORDS_PER_LINE - 1) + 2.0 <= MAX_LINE_W:
            lines.append(words)
    return lines


def baseline_y(line: int) -> float:
    return MARGIN_T + FONT_SIZE + line * LEADING


def word_spans(line: int, seed: int = 7) -> list[tuple[float, float]]:
    """Rentang x (pt) tiap kata pada render tanpa modulasi."""
    space = pymupdf.get_text_length(" ", FONT, FONT_SIZE)
    x, spans = MARGIN_L, []
    for word in build_lines(seed)[line]:
        width = pymupdf.get_text_length(word, FONT, FONT_SIZE)
        spans.append((x, x + width))
        x += width + space
    return spans


def _gap_shifts(frame: bytes | None, delta_pt: float) -> np.ndarray:
    shifts = np.zeros((LINES, WORDS_PER_LINE - 1))
    if frame is None:
        return shifts
    bits = np.unpackbits(np.frombuffer(frame, dtype=np.uint8))
    for li in range(LINES):
        for pi in range(PAIRS_PER_LINE):
            s = 1.0 if bits[(li * PAIRS_PER_LINE + pi) % len(bits)] else -1.0
            shifts[li, 2 * pi] = s * delta_pt
            shifts[li, 2 * pi + 1] = -s * delta_pt
    return shifts


def render_pdf(frame: bytes | None, delta_pt: float, seed: int = 7) -> bytes:
    """Render template; `frame=None` menghasilkan referensi tanpa modulasi."""
    lines = build_lines(seed)
    shifts = _gap_shifts(frame, delta_pt)
    space = pymupdf.get_text_length(" ", FONT, FONT_SIZE)
    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    for li, words in enumerate(lines):
        x, y = MARGIN_L, baseline_y(li)
        for wi, word in enumerate(words):
            page.insert_text((x, y), word, fontname=FONT, fontsize=FONT_SIZE)
            x += pymupdf.get_text_length(word, FONT, FONT_SIZE) + space
            if wi < WORDS_PER_LINE - 1:
                x += shifts[li, wi]
    return doc.tobytes()


def rasterize_gray(pdf: bytes, dpi: int) -> np.ndarray:
    page = pymupdf.open(stream=pdf, filetype="pdf")[0]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    rows = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
    return rows[:, : pix.width].copy()
