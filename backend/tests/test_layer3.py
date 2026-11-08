"""Lapis 3: honey-token (angka fiktif per salinan) dan anti-kolusi."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import layer3_honeytoken as l3
from app.core.layer2_semantic import TemplateError, demo_template, parse_template
from app.db.models import HoneyTokenRow


def _recipient_and_doc(client, nrp: str, nomor: str) -> tuple[int, int]:
    r = client.post(
        "/api/v1/recipients",
        json={"nrp": nrp, "nama": f"Personel {nrp}", "pangkat": "Mayor Inf",
              "jabatan": "Kasi Intel", "satuan": "Kodam Jaya"},
    ).json()
    d = client.post(
        "/api/v1/documents", json={"nomor": nomor, "judul": "Uji Lapis 3"}
    ).json()
    return r["id"], d["id"]


def _issue(client, nrp: str) -> dict:
    rid, did = _recipient_and_doc(client, nrp, f"ST/L3/{nrp}/XI/2026")
    return client.post(f"/api/v1/documents/{did}/copies", json={"recipient_id": rid}).json()


def _tokens_of(engine, copy: dict) -> list[str]:
    """Nilai token salinan menurut registri, urut indeks token."""
    with Session(engine) as s:
        rows = s.scalars(
            select(HoneyTokenRow)
            .where(HoneyTokenRow.copy_id == copy["copy_id"])
            .order_by(HoneyTokenRow.token_index)
        )
        return [r.value for r in rows]


def _intake(client, text: str) -> dict:
    res = client.post("/api/v1/intake/text", json={"text": text, "case_ref": "K-L3"})
    assert res.status_code == 200, res.text
    return res.json()


def test_demo_template_has_six_tokens_with_enough_random_digits():
    tokens = demo_template().tokens
    assert len(tokens) == 6
    assert all(t.pattern.count("#") >= 5 for t in tokens)


def test_token_with_too_few_random_digits_is_rejected():
    with pytest.raises(TemplateError):
        parse_template("Nomor [[###]] saja.")


def test_issued_copies_get_distinct_tokens_printed_in_their_text(client, engine):
    a, b = _issue(client, "11000001"), _issue(client, "11000002")
    ta, tb = _tokens_of(engine, a), _tokens_of(engine, b)
    assert len(set(ta)) == 6 and not set(ta) & set(tb)
    assert all(v in a["text"] for v in ta)
    # teks salinan dirender ulang dengan token yang sama (disimpan, bukan diacak ulang)
    again = client.get(f"/api/v1/copies/{a['copy_id']}/text").json()["text"]
    assert again == a["text"] and _tokens_of(engine, a) == ta


def test_paraphrase_keeping_two_facts_identifies_the_copy(client, engine):
    """Kalimat ditulis ulang total (tanpa kata varian), tetapi dua angka faktanya dikutip."""
    copy = _issue(client, "11000003")
    freq, reg = _tokens_of(engine, copy)[:2]
    leak = (
        f"Info A1: satuan disuruh memonitor jaringan di {freq.replace('.', ',')} MHz, "
        f"teknisi cek perangkat nomor REG-AL-{reg}. Jangan disebar."
    )
    body = _intake(client, leak)
    assert body["status"] == "IDENTIFIED"
    assert body["attribution"]["copy_id"] == copy["copy_id"]
    assert {t["token_index"] for t in body["tokens"]} == {0, 1}
    assert all(t["confirmed"] for t in body["tokens"])


def test_single_token_is_only_an_indication(client, engine):
    copy = _issue(client, "11000004")
    body = _intake(client, f"katanya ada gudang di blok {_tokens_of(engine, copy)[2]}")
    assert body["status"] == "INSUFFICIENT_FORENSIC_ARTIFACTS"
    assert body["attribution"] is None and body["attributions"] == []
    assert [t["copy_id"] for t in body["tokens"]] == [copy["copy_id"]]
    assert body["tokens"][0]["confirmed"] is False


def test_collusion_mixing_two_copies_names_both_and_no_innocent(client, engine):
    a, b, innocent = (_issue(client, n) for n in ("11000005", "11000006", "11000007"))
    ta, tb = _tokens_of(engine, a), _tokens_of(engine, b)
    leak = " ".join([ta[0], tb[1], ta[2], tb[3], ta[4], tb[5]])
    body = _intake(client, f"rangkuman: {leak}")
    assert body["status"] == "COLLUSION_SUSPECTED"
    assert {x["copy_id"] for x in body["attributions"]} == {a["copy_id"], b["copy_id"]}
    assert innocent["copy_id"] not in {t["copy_id"] for t in body["tokens"]}
    last = json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])
    assert last["data"]["status"] == "COLLUSION_SUSPECTED"
    assert last["data"]["copy_ids"] == sorted([a["copy_id"], b["copy_id"]])


def test_full_text_with_tokens_still_identified_by_both_layers(client):
    copy = _issue(client, "11000008")
    body = _intake(client, copy["text"])
    assert body["status"] == "IDENTIFIED"
    layers = {r["layer"]: r for r in body["layers"]}
    assert layers["L2_KATA"]["decoded_alone"] and layers["L3_TOKEN"]["decoded_alone"]
    assert len(body["tokens"]) == 6


def test_numbers_that_are_not_issued_tokens_match_nothing(client):
    _issue(client, "11000009")
    body = _intake(client, "Nomor KEP/882/IX/2026, pukul 05.30, frekuensi 100.000 MHz, 12345")
    assert body["tokens"] == [] and body["status"] == "INSUFFICIENT_FORENSIC_ARTIFACTS"


def test_numbers_in_ignores_separators():
    assert l3.numbers_in("143.275 MHz, 143,275 dan REG-AL-48271.") == {"143275", "48271"}


def test_judge_counts_distinct_tokens_and_honours_other_layers():
    hits = [l3.TokenHit(0, "1", 7), l3.TokenHit(0, "1", 7), l3.TokenHit(1, "2", 8)]
    assert l3.judge(hits, None) == l3.Verdict((), (7, 8))  # token sama dua kali = satu token
    assert l3.judge(hits, 8) == l3.Verdict((8,), (7,))  # 1 token + lapis lain = teridentifikasi
