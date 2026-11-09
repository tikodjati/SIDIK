"""Lapis 1 (visual): modulasi spasi antar-kata secara diferensial.

Spasi tiap baris dikelompokkan berpasangan (g0, g1): bit 1 -> g0 +delta, g1 -delta; bit 0
sebaliknya. Lebar baris tetap, jadi tata letak tidak bergeser. Bit ke-n slot disimpan di bit
payload (n mod jumlah_bit), sehingga payload berulang beberapa kali dan hasil ekstraksi
digabung (soft vote).

Akibatnya kata ke-(2p+1) bergeser +/-delta terhadap render tanpa modulasi, sedangkan kata
genap tidak bergeser. Dekoder (vision_extractor) mendaftarkan tiap kata ke render referensi
dan membaca bit dari pergeseran kata ganjil terhadap rata-rata dua tetangganya.

Tata letak (`Layout`) menentukan kata per baris, posisi baris, dan perataan (kiri, atau kanan-kiri
untuk naskah dinas): `spike_layout` (halaman kata
acak dari spike, dipakai untuk regresi foto uji) dan tata letak naskah dinas di `app.core.naskah`
(PDF salinan yang juga membawa Lapis 2).
"""

import random
from dataclasses import dataclass
from functools import cached_property, lru_cache

import numpy as np
import pymupdf

PAGE_W, PAGE_H = 595.0, 842.0
MARGIN_L, MARGIN_T = 56.0, 56.0
FONT = "helv"
MAX_LINE_W = PAGE_W - 2 * MARGIN_L


@dataclass(frozen=True)
class Layout:
    name: str
    lines: tuple[tuple[str, ...], ...]
    baselines: tuple[float, ...]  # pt dari atas halaman
    font_size: float
    leading: float
    # baris rata kanan-kiri (naskah dinas); None = semua rata kiri
    justified: tuple[bool, ...] | None = None

    @cached_property
    def gaps(self) -> tuple[float, ...]:
        """Lebar spasi dasar tiap baris (pt) sebelum modulasi: spasi biasa, atau pada baris rata
        kanan-kiri dilebarkan merata sampai kata terakhir menyentuh margin kanan."""
        space = pymupdf.get_text_length(" ", FONT, self.font_size)
        out = []
        for li, words in enumerate(self.lines):
            if self.justified and self.justified[li] and len(words) > 1:
                ink = sum(pymupdf.get_text_length(w, FONT, self.font_size) for w in words)
                out.append(max(space, (MAX_LINE_W - ink) / (len(words) - 1)))
            else:
                out.append(space)
        return tuple(out)

    @cached_property
    def spans(self) -> tuple[tuple[tuple[float, float], ...], ...]:
        """Rentang x (pt) tiap kata pada render tanpa modulasi."""
        out = []
        for li, words in enumerate(self.lines):
            x, spans = MARGIN_L, []
            for word in words:
                width = pymupdf.get_text_length(word, FONT, self.font_size)
                spans.append((x, x + width))
                x += width + self.gaps[li]
            out.append(tuple(spans))
        return tuple(out)

    def pairs(self, line: int) -> int:
        return (len(self.lines[line]) - 1) // 2

    @cached_property
    def slot_base(self) -> tuple[int, ...]:
        """Nomor slot pertama tiap baris (slot berurutan dari atas ke bawah)."""
        base, out = 0, []
        for li in range(len(self.lines)):
            out.append(base)
            base += self.pairs(li)
        return tuple(out)

    @property
    def total_slots(self) -> int:
        return self.slot_base[-1] + self.pairs(len(self.lines) - 1)


_VOCAB = (
    "pasukan satuan komando laporan operasi wilayah jaringan naskah dinas tugas sasaran "
    "daerah markas sistem data kode unit tim pos awak alat sandi rahasia kirim terima "
    "salinan cetak arsip surat nomor tanggal dasar maksud tujuan unsur giat rencana"
).split()


@lru_cache(maxsize=2)
def spike_layout(seed: int = 7) -> Layout:
    """Halaman uji spike: 56 baris x 13 kata acak (semua baris muat). Foto uji tim memakai ini."""
    font_size, leading, n_lines, n_words = 10.0, 13.0, 56, 13
    rng = random.Random(seed)
    space = pymupdf.get_text_length(" ", FONT, font_size)
    lines: list[tuple[str, ...]] = []
    while len(lines) < n_lines:
        words = tuple(rng.choice(_VOCAB) for _ in range(n_words))
        width = sum(pymupdf.get_text_length(w, FONT, font_size) for w in words)
        if width + space * (n_words - 1) + 2.0 <= MAX_LINE_W:
            lines.append(words)
    baselines = tuple(MARGIN_T + font_size + i * leading for i in range(n_lines))
    return Layout("spike", tuple(lines), baselines, font_size, leading)


def _gap_shifts(layout: Layout, frame: bytes | None, delta_pt: float) -> list[list[float]]:
    shifts = [[0.0] * max(len(words) - 1, 0) for words in layout.lines]
    if frame is None:
        return shifts
    bits = np.unpackbits(np.frombuffer(frame, dtype=np.uint8))
    for li in range(len(layout.lines)):
        for p in range(layout.pairs(li)):
            s = 1.0 if bits[(layout.slot_base[li] + p) % len(bits)] else -1.0
            shifts[li][2 * p] = s * delta_pt
            shifts[li][2 * p + 1] = -s * delta_pt
    return shifts


def render_pdf(layout: Layout, frame: bytes | None, delta_pt: float) -> bytes:
    """Render tata letak; `frame=None` menghasilkan referensi tanpa modulasi. Pada baris rata
    kanan-kiri modulasi ditambahkan di atas spasi yang sudah dilebarkan (pasangan +/-delta tak
    mengubah lebar baris, jadi margin kanan tetap lurus)."""
    shifts = _gap_shifts(layout, frame, delta_pt)
    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    for li, words in enumerate(layout.lines):
        x, y = MARGIN_L, layout.baselines[li]
        for wi, word in enumerate(words):
            page.insert_text((x, y), word, fontname=FONT, fontsize=layout.font_size)
            x += pymupdf.get_text_length(word, FONT, layout.font_size) + layout.gaps[li]
            if wi < len(words) - 1:
                x += shifts[li][wi]
    return doc.tobytes()


def rasterize_gray(pdf: bytes, dpi: int) -> np.ndarray:
    page = pymupdf.open(stream=pdf, filetype="pdf")[0]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    rows = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
    return rows[:, : pix.width].copy()
