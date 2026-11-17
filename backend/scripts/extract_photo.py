"""Ekstrak payload dari foto asli (spike: Lapis 1; naskah: Lapis 1 + 2).

Jalankan dari backend/:
  python -m scripts.extract_photo FOTO... [--delta 0.3] [--copy-id 0x51D1C0DE] [--out DIR]

Jika --delta tidak diberikan, diambil dari nama berkas (mis. "uji_d0.5_foto1.jpg" -> 0.5).
Foto harus memuat seluruh halaman (4 sudut kertas terlihat), kertas lebih terang dari meja.
"""

import argparse
import re
import time
from pathlib import Path

import cv2
import numpy as np

from app.core import layer1_visual as l1
from app.core import naskah
from app.core.payload import encode_payload
from app.core.vision_extractor import decode_photo, reference_flat
from scripts.make_test_pages import COPY_ID

DPI = 300


def _report_naskah(path: Path, gray: np.ndarray, delta: float, copy_id: int, started: float):
    found = naskah.decode_naskah_photo(gray, delta, DPI)
    elapsed = time.perf_counter() - started
    if found is None:
        print(f"{path.name}: kertas tidak ditemukan")
        return

    def show(d):
        return "-" if d is None else f"0x{d[0]:08X}"

    if found.decoded:
        verdict = "COCOK" if found.decoded[0] == copy_id else "SALAH (id berbeda)"
    else:
        verdict = "DITOLAK (bertentangan)" if found.conflict else "GAGAL (bukti tidak cukup)"
    print(
        f"{path.name} [{elapsed:.1f} dtk]: L1 {len(found.layer1_scores)}/{found.layer1_total} "
        f"-> {show(found.layer1_decoded)}, L2 {len(found.layer2_scores)}/{found.layer2_total} "
        f"-> {show(found.layer2_decoded)}, gabungan {show(found.decoded)} -> {verdict}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="+", type=Path)
    ap.add_argument("--delta", type=float)
    ap.add_argument("--copy-id", type=lambda s: int(s, 0), default=COPY_ID)
    ap.add_argument("--out", type=Path, help="simpan citra hasil pelurusan untuk diperiksa")
    ap.add_argument(
        "--layout", choices=("spike", "naskah"), default="spike",
        help="spike = halaman uji kata acak (foto uji lama); naskah = PDF salinan dari dashboard",
    )
    a = ap.parse_args()
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)

    layout = naskah.generic_layout() if a.layout == "naskah" else l1.spike_layout()
    reference_flat(layout, DPI)  # render referensi sekali (di server ini terjadi saat start)
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
        started = time.perf_counter()
        if a.layout == "naskah":
            _report_naskah(path, gray, delta, a.copy_id, started)
            continue
        found = decode_photo(gray, layout, delta, DPI)
        elapsed = time.perf_counter() - started
        if found is None:
            print(f"{path.name}: kertas tidak ditemukan "
                  "(kontras kertas-meja kurang / sudut terpotong)")
            continue
        flat, scores, geom, decoded = found.aligned, found.scores, found.geom, found.decoded
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
            f"{path.name} [{elapsed:.1f} dtk]: slot {len(scores)}/{layout.total_slots}, "
            f"skala {geom.scale:.3f} skor-baris {geom.score:.2f}, "
            f"slot-BER {ber:.3f} (vs id uji), {result}"
        )


if __name__ == "__main__":
    main()
