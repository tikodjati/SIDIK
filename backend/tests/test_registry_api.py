import json

from sqlalchemy import text as sql

RECIPIENT = {
    "nrp": "1102003912",
    "nama": "Hendro Wicaksono",
    "pangkat": "Kolonel Inf",
    "jabatan": "Asintel Kasdam",
    "satuan": "Kodam Jaya",
}
DOCUMENT = {
    "nomor": "ST/412/OPS-SIB/X/2026",
    "judul": "Kesiapsiagaan Siber",
    "klasifikasi": "KONFIDENSIAL",  # langsung terbit; RAHASIA diuji di test_four_eyes
}


def _setup(client, recipient=RECIPIENT):
    r = client.post("/api/v1/recipients", json=recipient).json()
    d = client.post("/api/v1/documents", json=DOCUMENT).json()
    return r, d


def _issue(client, document_id, recipient_id):
    res = client.post(
        f"/api/v1/documents/{document_id}/copies", json={"recipient_id": recipient_id}
    )
    assert res.status_code == 201, res.text
    return res.json()


def _intake(client, text, **extra):
    res = client.post("/api/v1/intake/text", json={"text": text, **extra})
    assert res.status_code == 200, res.text
    return res.json()


def test_partial_retype_identifies_the_recipient(client):
    r, d = _setup(client)
    copy = _issue(client, d["id"], r["id"])
    lines = copy["text"].splitlines()
    excerpt = "\n".join(lines[: int(len(lines) * 0.8)]).upper()  # 80% dari atas, huruf besar

    result = _intake(client, excerpt, case_ref="KASUS-001")

    assert result["status"] == "IDENTIFIED"
    att = result["attribution"]
    assert att["copy_id"] == copy["copy_id"]
    assert att["recipient"]["nrp"] == "1102003912"
    assert att["document_nomor"] == DOCUMENT["nomor"]
    assert result["ledger"]["seq"] > copy["ledger_seq"]


def test_decoded_but_unregistered_copy_is_not_attributed(client):
    _setup(client)
    forged = client.post("/api/v1/layer2/watermark", json={"copy_id": 424242}).json()["text"]
    result = _intake(client, forged)
    assert result["status"] == "UNREGISTERED"
    assert result["attribution"] is None


def test_insufficient_evidence_is_rejected_and_still_logged(client):
    _setup(client)
    before = len(client.get("/api/v1/ledger").json())
    result = _intake(client, "Rapat membahas anggaran kantin.")
    assert result["status"] == "INSUFFICIENT_FORENSIC_ARTIFACTS"
    assert result["attribution"] is None
    assert len(client.get("/api/v1/ledger").json()) == before + 1


def test_ledger_never_stores_the_evidence_text_only_its_hash(client):
    r, d = _setup(client)
    copy = _issue(client, d["id"], r["id"])
    secret = "KALIMAT-BUKTI-RAHASIA " + copy["text"]
    _intake(client, secret, case_ref="K1")
    last = client.get("/api/v1/ledger").json()[-1]
    body = json.loads(last["body"])
    assert "KALIMAT-BUKTI-RAHASIA" not in last["body"]
    assert len(body["data"]["evidence_sha256"]) == 64
    assert body["event"] == "LEAK_INTAKE_TEXT" and body["data"]["case_ref"] == "K1"


def test_logged_in_user_is_recorded_as_actor(client):
    r, d = _setup(client)
    _issue(client, d["id"], r["id"])
    entries = [json.loads(e["body"]) for e in client.get("/api/v1/ledger").json()]
    issued = next(b for b in entries if b["event"] == "COPY_ISSUED")
    assert issued["actor"] == "admin"


def test_copy_ids_are_random_distinct_and_bound_to_recipients(client):
    r1, d = _setup(client)
    r2 = client.post("/api/v1/recipients", json={**RECIPIENT, "nrp": "2200000001"}).json()
    c1, c2 = _issue(client, d["id"], r1["id"]), _issue(client, d["id"], r2["id"])
    assert c1["copy_id"] != c2["copy_id"] and c1["text"] != c2["text"]
    assert abs(c1["copy_id"] - c2["copy_id"]) != 1  # bukan berurutan


def test_registry_conflicts_and_not_found(client):
    r, d = _setup(client)
    assert client.post("/api/v1/recipients", json=RECIPIENT).status_code == 409
    assert client.post("/api/v1/documents", json=DOCUMENT).status_code == 409
    _issue(client, d["id"], r["id"])
    dup = client.post(f"/api/v1/documents/{d['id']}/copies", json={"recipient_id": r["id"]})
    assert dup.status_code == 409
    missing = client.post("/api/v1/documents/999/copies", json={"recipient_id": r["id"]})
    assert missing.status_code == 404


def test_verify_endpoint_ok_then_detects_database_tampering(client, engine):
    r, d = _setup(client)
    _issue(client, d["id"], r["id"])
    _intake(client, "teks bebas tanpa varian")
    ok = client.get("/api/v1/ledger/verify").json()
    assert ok["ok"] and ok["entries"] == 3  # login, penerbitan salinan, intake

    with engine.begin() as conn:  # admin DB mengubah catatan penerbitan
        conn.execute(sql("UPDATE ledger_entries SET body = replace(body, 'COPY_ISSUED', 'X') "
                         "WHERE seq = 2"))
    bad = client.get("/api/v1/ledger/verify").json()
    assert not bad["ok"] and bad["bad_seq"] == 2


def test_lists_documents_and_copies_with_names(client):
    r, d = _setup(client)
    copy = _issue(client, d["id"], r["id"])
    docs = client.get("/api/v1/documents").json()
    copies = client.get("/api/v1/copies").json()
    assert [x["nomor"] for x in docs] == [DOCUMENT["nomor"]]
    assert copies[0]["copy_id"] == copy["copy_id"]
    assert (copies[0]["recipient_nama"], copies[0]["document_nomor"]) == (
        RECIPIENT["nama"],
        DOCUMENT["nomor"],
    )


def test_copy_text_is_reproducible_and_404_for_unknown(client):
    r, d = _setup(client)
    copy = _issue(client, d["id"], r["id"])
    again = client.get(f"/api/v1/copies/{copy['copy_id']}/text").json()
    assert again["text"] == copy["text"]
    assert client.get("/api/v1/copies/12345/text").status_code == 404


def test_ledger_can_be_listed_newest_first(client):
    r, d = _setup(client)
    _issue(client, d["id"], r["id"])
    _intake(client, "teks bebas")
    seqs = [e["seq"] for e in client.get("/api/v1/ledger?newest_first=true").json()]
    assert seqs == [3, 2, 1]
