"""Data demo Lapis 4 (honey-record) dari baris perintah.

Jalankan dari backend/ (atau: docker compose exec api python -m scripts.personnel ...):
  python -m scripts.personnel seed           # data personel demo + honey-record tertanam
  python -m scripts.personnel hoax-samples   # dua dump hoaks untuk demo + korpus publiknya

`seed` sama dengan tombol "Isi data demo" di halaman Data Personel; sekali saja per basis data.
`hoax-samples` menulis ke <data>/test_leaks/:
  - dump_hoaks_daur_ulang.csv: identitas dari "data publik lama" (rekaan) dengan kolom bergaya
    militer; korpusnya didaftarkan, jadi verifier menyimpulkan DAUR ULANG.
  - dump_hoaks_rekaan.csv: NIK acak berformat tidak valid; verifier menyimpulkan REKAAN.
Semua data rekaan; jangan dicampur dengan data sungguhan.
"""

import argparse
import csv
import io
import random
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core import layer4_honeyrecord as l4
from app.core import layer4_store as store
from app.core.audit_ledger import append_event, get_signer
from app.db import get_engine
from app.db.models import PublicCorpus

CORPUS_LABEL = "Data publik lama 2021 (DEMO)"


def seed(args: argparse.Namespace) -> None:
    with Session(get_engine()) as session:
        try:
            rows, sentinels = store.seed_personnel(session, args.count)
        except ValueError as exc:
            raise SystemExit(f"dilewati: {exc}") from exc
        append_event(session, get_signer(), "PERSONNEL_SEEDED", {"rows": rows}, "cli")
        session.commit()
    print(f"{rows} baris personel demo, {sentinels} di antaranya honey-record tertanam")


def _csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def hoax_samples(_: argparse.Namespace) -> None:
    out = Path(settings.data_dir) / "test_leaks"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2021)

    # "data publik lama": warga sipil rekaan (bukan personel kita)
    public = [l4.make_persona(rng) for _ in range(300)]
    public_csv = _csv([{"nama": p.nama, "nik": p.nik, "no_hp": p.no_hp} for p in public])
    with Session(get_engine()) as session:
        if session.scalar(select(PublicCorpus).where(PublicCorpus.label == CORPUS_LABEL)) is None:
            corpus = store.register_corpus(
                session, CORPUS_LABEL, "Contoh korpus untuk demo verifier", public_csv
            )
            append_event(
                session, get_signer(), "CORPUS_REGISTERED",
                {"corpus_id": corpus.id, "label": CORPUS_LABEL, "entries": corpus.entries}, "cli",
            )
            session.commit()

    # hoaks 1: data publik itu diberi "header" militer seolah bocoran TNI AD
    recycled = [
        {"NRP": f"{rng.randint(1, 3)}{rng.randint(10**8, 10**9 - 1)}", "NAMA": p.nama.upper(),
         "PANGKAT": rng.choice(("SERDA", "KOPDA", "LETTU")), "SATUAN": rng.choice(l4.SATUAN),
         "NIK": p.nik, "HP": p.no_hp}
        for p in public[:200]
    ]
    (out / "dump_hoaks_daur_ulang.csv").write_text(_csv(recycled), encoding="utf-8")

    # hoaks 2: data dikarang asal (NIK acak tanpa struktur yang benar)
    fabricated = [
        {"nrp": f"{rng.randint(10**9, 10**10 - 1)}", "nama": f"Personel {i}",
         "nik": f"{rng.randint(10**15, 10**16 - 1)}",
         "hp": "08" + "".join(str(rng.randint(0, 9)) for _ in range(10))}
        for i in range(150)
    ]
    (out / "dump_hoaks_rekaan.csv").write_text(_csv(fabricated), encoding="utf-8")
    print(f"ditulis: {out / 'dump_hoaks_daur_ulang.csv'}")
    print(f"ditulis: {out / 'dump_hoaks_rekaan.csv'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--count", type=int, default=400)
    s.set_defaults(func=seed)
    sub.add_parser("hoax-samples").set_defaults(func=hoax_samples)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
