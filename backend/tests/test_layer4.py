"""Lapis 4: honey-record (ekspor data personel bersisip baris palsu) dan pemeriksa klaim dump."""

import csv
import io
import json
import random

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import layer4_honeyrecord as l4
from app.db.models import CorpusFingerprint, HoneyRecord, Personnel


@pytest.fixture
def seeded(client):
    res = client.post("/api/v1/personnel/seed-demo?count=200")
    assert res.status_code == 201, res.text
    return res.json()


def _export(client, satuan: str | None = None, purpose: str = "Rekap bulanan") -> tuple[int, str]:
    res = client.post("/api/v1/personnel/exports", json={"satuan": satuan, "purpose": purpose})
    assert res.status_code == 200, res.text
    return int(res.headers["x-export-id"]), res.text


def _dump(client, text: str, name: str = "dump.csv") -> dict:
    res = client.post(
        "/api/v1/intake/dump",
        files={"file": (name, text.encode(), "text/csv")},
        data={"case_ref": "K-DUMP"},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def _to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _export_sentinels(engine, export_id: int) -> set[str]:
    with Session(engine) as s:
        return set(s.scalars(select(HoneyRecord.nik).where(HoneyRecord.export_id == export_id)))


def test_seed_plants_honey_records_and_runs_only_once(client, seeded, engine):
    assert seeded["rows"] == 200 + seeded["honey_records"] and seeded["honey_records"] >= 4
    with Session(engine) as s:
        planted = set(s.scalars(select(HoneyRecord.nik).where(HoneyRecord.export_id.is_(None))))
        in_table = set(s.scalars(select(Personnel.nik)))
    assert planted and planted <= in_table  # tertanam di tabel personel, tak bisa dibedakan
    assert client.post("/api/v1/personnel/seed-demo").status_code == 409


def test_export_mixes_in_unique_honey_records_and_is_logged(client, seeded, engine):
    a_id, a = _export(client)
    b_id, b = _export(client)
    a_sent, b_sent = _export_sentinels(engine, a_id), _export_sentinels(engine, b_id)
    assert len(a_sent) >= 3 and not a_sent & b_sent
    niks = [r["nik"] for r in _rows(a)]
    assert a_sent <= set(niks) and niks[-len(a_sent):] != sorted(a_sent)  # tidak di ujung
    last = json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])
    assert last["event"] == "DATA_EXPORTED" and last["data"]["export_id"] == b_id
    assert [e["id"] for e in client.get("/api/v1/personnel/exports").json()] == [b_id, a_id]


def test_leaked_export_is_traced_to_that_export(client, seeded):
    export_id, text = _export(client, purpose="Kebutuhan rapat")
    body = _dump(client, text)
    assert body["status"] == "AUTHENTIC_LEAK"
    proven = [s for s in body["sources"] if s["proven"]]
    assert [s["export"]["id"] for s in proven] == [export_id]  # bukan "DB langsung"
    assert proven[0]["export"]["username"] == "admin"
    last = json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])
    assert last["event"] == "LEAK_INTAKE_DUMP" and last["data"]["export_ids"] == [export_id]


def test_partial_leak_with_two_honey_rows_is_enough(client, seeded, engine):
    export_id, text = _export(client)
    sentinels = _export_sentinels(engine, export_id)
    rows = _rows(text)
    picked = [r for r in rows if r["nik"] in sentinels][:2] + [
        r for r in rows if r["nik"] not in sentinels
    ][:20]
    body = _dump(client, _to_csv(picked))
    assert body["status"] == "AUTHENTIC_LEAK"
    assert [s["export"]["id"] for s in body["sources"] if s["proven"]] == [export_id]


def test_single_honey_value_alone_is_only_an_indication(client, seeded, engine):
    export_id, _ = _export(client)
    nik = sorted(_export_sentinels(engine, export_id))[0]
    body = _dump(client, f"nik\n{nik}\n")
    assert body["status"] != "AUTHENTIC_LEAK"
    assert [(s["export"]["id"], s["proven"]) for s in body["sources"]] == [(export_id, False)]


def test_merged_dump_of_two_exports_names_both(client, seeded):
    a_id, a = _export(client, purpose="Ekspor A")
    b_id, b = _export(client, purpose="Ekspor B")
    body = _dump(client, a + b)
    proven = {s["export"]["id"] for s in body["sources"] if s["proven"]}
    assert body["status"] == "AUTHENTIC_LEAK" and proven == {a_id, b_id}


def test_direct_database_dump_is_traced_to_the_database(client, seeded, engine):
    """SQL injection: tabel personel dicuri langsung (bukan lewat ekspor)."""
    with Session(engine) as s:
        rows = s.execute(select(Personnel.nrp, Personnel.nik, Personnel.no_hp)).all()
    sql = "\n".join(
        f"INSERT INTO personnel VALUES ('{a}', '{b}', '+62{c[1:]}');" for a, b, c in rows
    )
    body = _dump(client, sql, "dump.sql")
    assert body["status"] == "AUTHENTIC_LEAK"
    assert [s["export"] for s in body["sources"] if s["proven"]] == [None]


def _public_dataset(n: int = 120) -> list[l4.Persona]:
    rng = random.Random(77)
    return [l4.make_persona(rng) for _ in range(n)]


def test_recycled_public_data_is_flagged_and_corpus_keeps_only_hashes(client, seeded, engine):
    public = _public_dataset()
    corpus_csv = _to_csv([{"nama": p.nama, "nik": p.nik, "hp": p.no_hp} for p in public])
    res = client.post(
        "/api/v1/corpora",
        files={"file": ("publik.csv", corpus_csv.encode(), "text/csv")},
        data={"label": "Data publik uji", "note": "uji"},
    )
    assert res.status_code == 201, res.text
    with Session(engine) as s:
        stored = set(s.scalars(select(CorpusFingerprint.fp)))
    assert public[0].nik not in stored and l4.fingerprint(public[0].nik) in stored

    hoax = _to_csv([{"NRP": "3" + p.nik[:9], "NAMA": p.nama, "NIK": p.nik} for p in public[:80]])
    body = _dump(client, hoax)
    assert body["status"] == "RECYCLED_PUBLIC" and body["corpus_label"] == "Data publik uji"
    assert body["sources"] == []


def test_fabricated_dump_is_flagged(client, seeded):
    rng = random.Random(5)
    rows = [{"nik": f"{rng.randint(10**15, 10**16 - 1)}"} for _ in range(60)]
    body = _dump(client, _to_csv(rows))
    assert body["status"] == "FABRICATED" and body["invalid_ratio"] >= 0.3


def test_valid_but_unknown_identities_are_not_ours(client, seeded):
    body = _dump(client, "\n".join(p.nik for p in _public_dataset(50)))
    assert body["status"] == "NOT_FROM_OUR_DB" and body["personnel_ratio"] == 0


def test_dump_without_identifiers(client, seeded):
    assert _dump(client, "username,password\nbudi,rahasia\n")["status"] == "INSUFFICIENT_DATA"


def test_roles(login_as, seeded):
    investigator, distributor = login_as("investigator"), login_as("distributor")
    req = {"satuan": None, "purpose": "uji peran"}
    assert investigator.post("/api/v1/personnel/exports", json=req).status_code == 403
    assert distributor.post("/api/v1/personnel/exports", json=req).status_code == 200
    files = {"file": ("d.csv", b"x", "text/csv")}
    assert distributor.post("/api/v1/intake/dump", files=files).status_code == 403
    assert distributor.post("/api/v1/personnel/seed-demo").status_code == 403


def test_extract_identifiers_from_sql_json_and_phone_formats():
    text = (
        "INSERT INTO t VALUES ('3171014503991234','+62 812-3456-7890');\n"
        '{"nik": "3171014503991235", "hp": "6281234567891", "nrp": "1990012345"}\n'
        "3171014503991236 0812 3456 7892"
    )
    ids = l4.extract_identifiers(text)
    assert ids.niks == {"3171014503991234", "3171014503991235", "3171014503991236"}
    assert ids.phones == {"081234567890", "081234567891", "081234567892"}
    assert ids.nrps == {"1990012345"}


def test_nik_structure_check():
    rng = random.Random(1)
    assert all(l4.nik_valid(l4.make_persona(rng).nik) for _ in range(200))
    assert not l4.nik_valid("0000000000000000")
    assert not l4.nik_valid("3171001301990001")  # kecamatan 00
    assert not l4.nik_valid("3171011399000001")  # bulan 99
