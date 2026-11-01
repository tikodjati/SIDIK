"""Buat PDF uji Lapis 1 untuk dicetak/ditampilkan lalu difoto.

Jalankan dari backend/:  python -m scripts.make_test_pages
Keluaran: data/watermarked_outputs/uji_foto/uji_d<delta>.pdf (+ kontrol tanpa modulasi).
"""

import argparse
from pathlib import Path

from app.core import layer1_visual as l1
from app.core.payload import encode_payload

COPY_ID = 0x51D1C0DE
OUT = Path(__file__).resolve().parents[2] / "data" / "watermarked_outputs" / "uji_foto"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--deltas", type=float, nargs="+", default=[0.3, 0.5])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    frame = encode_payload(COPY_ID)
    for d in a.deltas:
        (OUT / f"uji_d{d}.pdf").write_bytes(l1.render_pdf(frame, d))
    (OUT / "kontrol_tanpa_modulasi.pdf").write_bytes(l1.render_pdf(None, 0))
    print(f"copy_id uji = 0x{COPY_ID:08X}\nPDF ditulis ke: {OUT}")
