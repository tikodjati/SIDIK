"""Four-eyes principle: salinan naskah RAHASIA/SANGAT RAHASIA baru terbit setelah disetujui admin
lain, dan salinan yang tak pernah diedarkan tidak boleh diatribusikan."""

import json

import pytest


def _setup(client, klasifikasi: str, nrp: str = "1102003912") -> tuple[int, int]:
    r = client.post(
        "/api/v1/recipients",
        json={"nrp": nrp, "nama": "Hendro", "pangkat": "Kolonel Inf",
              "jabatan": "Asintel", "satuan": "Kodam Jaya"},
    ).json()
    d = client.post(
        "/api/v1/documents",
        json={"nomor": f"ST/{klasifikasi}/{nrp}", "judul": "Uji", "klasifikasi": klasifikasi},
    ).json()
    return d["id"], r["id"]


def _request(client, klasifikasi: str = "RAHASIA", nrp: str = "1102003912") -> dict:
    doc, rec = _setup(client, klasifikasi, nrp)
    res = client.post(f"/api/v1/documents/{doc}/copies", json={"recipient_id": rec})
    assert res.status_code == 201, res.text
    return res.json()


def _last_event(client) -> dict:
    return json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])


@pytest.mark.parametrize("klasifikasi", ["RAHASIA", "SANGAT RAHASIA"])
def test_classified_copy_is_pending_and_cannot_be_downloaded(login_as, klasifikasi):
    distributor, admin = login_as("distributor"), login_as("admin")
    copy = _request(distributor, klasifikasi)
    assert copy["status"] == "PENDING" and copy["text"] is None
    assert _last_event(admin)["event"] == "COPY_REQUESTED"
    assert distributor.get(f"/api/v1/copies/{copy['copy_id']}/pdf").status_code == 409
    assert admin.get(f"/api/v1/copies/{copy['copy_id']}/text").status_code == 409


def test_unclassified_copy_is_issued_immediately(client):
    copy = _request(client, "KONFIDENSIAL")
    assert copy["status"] == "ISSUED" and copy["text"]


def test_requester_cannot_approve_own_copy(login_as):
    admin = login_as("admin")
    copy = _request(admin)
    res = admin.post(f"/api/v1/copies/{copy['copy_id']}/approve")
    assert res.status_code == 403 and "four-eyes" in res.json()["detail"]


def test_second_admin_approves_then_copy_is_released_and_logged(login_as):
    distributor, approver = login_as("distributor"), login_as("admin", "perwira.sandi")
    copy = _request(distributor)
    assert distributor.post(f"/api/v1/copies/{copy['copy_id']}/approve").status_code == 403
    res = approver.post(f"/api/v1/copies/{copy['copy_id']}/approve")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "ISSUED" and body["requested_by"] == "distributor"
    assert body["approved_by"] == "perwira.sandi"
    assert distributor.get(f"/api/v1/copies/{copy['copy_id']}/pdf").status_code == 200
    event = _last_event(approver)
    assert event["event"] == "COPY_EXPORTED"  # unduhan PDF tercatat setelah persetujuan
    events = [json.loads(e["body"]) for e in approver.get("/api/v1/ledger").json()]
    approved = next(e for e in events if e["event"] == "COPY_APPROVED")
    assert approved["actor"] == "perwira.sandi"
    assert approved["data"]["requested_by"] == "distributor"
    # sudah disetujui: tak bisa disetujui ulang
    assert approver.post(f"/api/v1/copies/{copy['copy_id']}/approve").status_code == 409


def test_rejected_copy_is_never_released_and_can_be_requested_again(login_as):
    distributor, approver = login_as("distributor"), login_as("admin", "perwira.sandi")
    copy = _request(distributor)
    res = approver.post(f"/api/v1/copies/{copy['copy_id']}/reject", json={"reason": "tidak perlu"})
    assert res.status_code == 200 and res.json()["status"] == "REJECTED"
    assert _last_event(approver)["data"]["reason"] == "tidak perlu"
    assert distributor.get(f"/api/v1/copies/{copy['copy_id']}/pdf").status_code == 409
    listed = {c["copy_id"]: c["status"] for c in distributor.get("/api/v1/copies").json()}
    assert listed[copy["copy_id"]] == "REJECTED"
    again = distributor.post(
        f"/api/v1/documents/{copy['document_id']}/copies",
        json={"recipient_id": copy["recipient_id"]},
    )
    assert again.status_code == 201 and again.json()["status"] == "PENDING"


def test_copy_that_was_never_released_is_not_attributed(login_as, engine):
    """Teks salinan yang masih menunggu persetujuan (mis. bocor dari dalam sistem) tak boleh
    menuduh penerimanya: ia belum pernah memegang salinan itu."""
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from app.core.layer2_semantic import demo_template, encode_text
    from app.core.payload import encode_payload
    from app.db.models import HoneyTokenRow

    distributor, investigator = login_as("distributor"), login_as("investigator")
    copy = _request(distributor)
    with Session(engine) as s:
        tokens = tuple(
            s.scalars(
                select(HoneyTokenRow.value)
                .where(HoneyTokenRow.copy_id == copy["copy_id"])
                .order_by(HoneyTokenRow.token_index)
            )
        )
    text = encode_text(demo_template(), encode_payload(copy["copy_id"]), tokens)
    body = investigator.post("/api/v1/intake/text", json={"text": text}).json()
    assert body["status"] == "UNREGISTERED" and body["attributions"] == []
    assert body["tokens"] == []
