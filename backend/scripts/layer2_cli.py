"""CLI sederhana untuk mencoba Lapis 2 tanpa menjalankan server.

Jalankan dari backend/:
  python -m scripts.layer2_cli watermark 1001 -o salinan_1001.txt
  python -m scripts.layer2_cli extract bukti.txt
"""

import argparse
from pathlib import Path

from app.core.layer2_semantic import demo_template, encode_text, extract_scores
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    wm = sub.add_parser("watermark", help="buat naskah untuk satu salinan")
    wm.add_argument("copy_id", type=int)
    wm.add_argument("-o", "--out", type=Path, help="simpan ke berkas (default: cetak ke layar)")
    ex = sub.add_parser("extract", help="baca identitas salinan dari teks bukti")
    ex.add_argument("file", type=Path)
    a = ap.parse_args()
    template = demo_template()

    if a.cmd == "watermark":
        text = encode_text(template, encode_payload(a.copy_id))
        if a.out:
            a.out.write_text(text, encoding="utf-8")
            print(f"ditulis: {a.out} ({template.capacity_bits} bit, {len(template.slots)} slot)")
        else:
            print(text)
        return

    scores = extract_scores(template, a.file.read_text(encoding="utf-8"))
    print(f"bit terbaca: {len(scores)} dari {template.capacity_bits}")
    try:
        copy_id, _ = decode_scores(scores)
        print(f"TERIDENTIFIKASI: salinan {copy_id}")
    except PayloadDecodeError:
        print("BUKTI TIDAK CUKUP (sistem menolak menebak)")


if __name__ == "__main__":
    main()
