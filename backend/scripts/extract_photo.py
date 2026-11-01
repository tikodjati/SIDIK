"""Ekstrak payload Lapis 1 dari foto asli.

Jalankan dari backend/:
  python -m scripts.extract_photo FOTO... [--delta 0.3] [--copy-id 0x51D1C0DE] [--out DIR]

Jika --delta tidak diberikan, diambil dari nama berkas (mis. "uji_d0.5_foto1.jpg" -> 0.5).
Foto harus memuat seluruh halaman (4 sudut kertas terlihat), kertas lebih terang dari meja.
"""

import argparse
import re
from pathlib import Path

import cv2
import numpy as np

from app.core import layer1_visual as l1
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload
from app.core.vision_extractor import (
    locate_rows,
    measure_slot_scores,
    rectify_by_text,
    rectify_page,
    refine_alignment,
)
from scripts.make_test_pages import COPY_ID

DPI = 300


MAX_TRIES = 8


def analyse(gray, page_size, delta):
    """Cari kandidat penyelarasan (3 cara awal x 4 rotasi x dengan/tanpa tahap affine), urutkan
    menurut korelasi ECC kasar, lalu coba dekode berurutan; pakai yang pertama berhasil.
    Jika tidak ada, kembalikan percobaan dengan slot terbaca terbanyak."""
    candidates = []
    for k in range(4):
        g = np.ascontiguousarray(np.rot90(gray, k))
        for rectifier in (
            lambda im: rectify_page(im, page_size),
            lambda im: rectify_by_text(im, page_size, DPI),
            lambda im: rectify_by_text(im, page_size, DPI, method="minrect"),
        ):
            try:
                flat = rectifier(g)
            except (ValueError, cv2.error):
                continue
            for affine in (True, False):
                rough, cc = refine_alignment(flat, DPI, factors=(8,), affine_first=affine)
                candidates.append((cc, rough))
    best = None
    for _, rough in sorted(candidates, key=lambda c: -c[0])[:MAX_TRIES]:
        aligned, _ = refine_alignment(rough, DPI, factors=(4, 2))
        geom = locate_rows(aligned, DPI)
        scores = measure_slot_scores(aligned, delta, DPI, geom)
        info = (len(scores), aligned, scores, geom)
        try:
            return (*info, decode_scores(scores))
        except PayloadDecodeError:
            if best is None or info[0] > best[0]:
                best = (*info, None)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="+", type=Path)
    ap.add_argument("--delta", type=float)
    ap.add_argument("--copy-id", type=lambda s: int(s, 0), default=COPY_ID)
    ap.add_argument("--out", type=Path, help="simpan citra hasil pelurusan untuk diperiksa")
    a = ap.parse_args()
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)

    ref_page = l1.rasterize_gray(l1.render_pdf(None, 0), DPI)
    page_size = (ref_page.shape[1], ref_page.shape[0])
    expected_bits = np.unpackbits(np.frombuffer(encode_payload(a.copy_id), dtype=np.uint8))

    for path in a.photos:
        m = re.search(r"d(\d+\.\d+)", path.name)
        delta = a.delta or (float(m.group(1)) if m else None)
        if delta is None:
            print(f"{path.name}: beri --delta atau namai berkas dengan 'd0.3'")
            continue
        gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            print(f"{path.name}: tidak bisa dibaca")
            continue
        found = analyse(gray, page_size, delta)
        if found is None:
            print(f"{path.name}: kertas tidak ditemukan "
                  "(kontras kertas-meja kurang / sudut terpotong)")
            continue
        ok_lines, flat, scores, geom, decoded = found
        if a.out:
            small = cv2.resize(flat, None, fx=0.4, fy=0.4)
            cv2.imwrite(str(a.out / f"{path.stem}_lurus.jpg"), small)
        errs = sum(
            (s > 0) != bool(expected_bits[n % len(expected_bits)]) for n, s in scores.items()
        )
        ber = errs / max(len(scores), 1)
        if decoded:
            copy_id, flags = decoded
            verdict = "COCOK" if copy_id == a.copy_id else "SALAH (id berbeda)"
            result = f"copy_id=0x{copy_id:08X} flags={flags} -> {verdict}"
        else:
            result = "GAGAL (bukti tidak cukup; sistem menolak menebak)"
        print(
            f"{path.name}: slot terbaca {ok_lines}/{l1.LINES * l1.PAIRS_PER_LINE}, "
            f"skala {geom.scale:.3f} skor-baris {geom.score:.2f}, "
            f"slot-BER {ber:.3f} (vs id uji), {result}"
        )


if __name__ == "__main__":
    main()
