import json
import random

import cv2
import pytest

from app.core import layer1_visual as l1
from scripts.spike_layer1 import simulate_camera

DPI = 300


def _setup_copy(client) -> dict:
    r = client.post(
        "/api/v1/recipients",
        json={"nrp": "1102003912", "nama": "Hendro", "pangkat": "Kolonel Inf",
              "jabatan": "Asintel", "satuan": "Kodam Jaya"},
    ).json()
    d = client.post(
        "/api/v1/documents",
        json={"nomor": "ST/FOTO/XI/2026", "judul": "Uji Foto", "klasifikasi": "RAHASIA"},
    ).json()
    res = client.post(f"/api/v1/documents/{d['id']}/copies", json={"recipient_id": r["id"]})
    return res.json()


def _photo_of(pdf: bytes, seed: int = 4) -> bytes:
    """Foto simulasi: kertas di meja, miring 20 derajat, bayangan, blur, JPEG."""
    page = l1.rasterize_gray(pdf, DPI)
    photo = simulate_camera(page, 2400, 20, 0.8, 85, random.Random(seed))
    return cv2.imencode(".jpg", photo, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


def _upload(client, data: bytes, content_type: str = "image/jpeg", case_ref: str = "K-FOTO"):
    return client.post(
        "/api/v1/intake/photo",
        files={"photo": ("bukti.jpg", data, content_type)},
        data={"case_ref": case_ref},
    )


@pytest.fixture(scope="module")
def unmodulated_photo() -> bytes:
    return _photo_of(l1.render_pdf(l1.naskah_layout(), None, 0))


def test_copy_pdf_download_is_a_pdf_and_is_logged(client):
    copy = _setup_copy(client)
    res = client.get(f"/api/v1/copies/{copy['copy_id']}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
    assert f"salinan_{copy['copy_id']:08X}.pdf" in res.headers["content-disposition"]
    last = json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])
    assert last["event"] == "COPY_EXPORTED" and last["data"]["copy_id"] == copy["copy_id"]


def test_photo_of_downloaded_pdf_identifies_the_recipient(client):
    copy = _setup_copy(client)
    pdf = client.get(f"/api/v1/copies/{copy['copy_id']}/pdf").content
    res = _upload(client, _photo_of(pdf))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "IDENTIFIED"
    assert body["attribution"]["copy_id"] == copy["copy_id"]
    assert body["attribution"]["recipient"]["nrp"] == "1102003912"
    assert body["aligned_preview"]  # citra pelurusan untuk ditampilkan
    last = json.loads(client.get("/api/v1/ledger?newest_first=true").json()[0]["body"])
    assert last["event"] == "LEAK_INTAKE_PHOTO" and last["data"]["case_ref"] == "K-FOTO"
    assert len(last["data"]["evidence_sha256"]) == 64


def test_photo_of_page_without_watermark_is_refused(client, unmodulated_photo):
    _setup_copy(client)
    body = _upload(client, unmodulated_photo).json()
    assert body["status"] == "INSUFFICIENT_FORENSIC_ARTIFACTS"
    assert body["attribution"] is None


def test_photo_of_unregistered_copy_is_not_attributed(client):
    _setup_copy(client)
    from app.config import settings
    from app.core.payload import encode_payload

    forged = l1.render_pdf(l1.naskah_layout(), encode_payload(424242), settings.layer1_delta_pt)
    body = _upload(client, _photo_of(forged)).json()
    assert body["status"] == "UNREGISTERED" and body["attribution"] is None


def test_photo_upload_rejects_bad_type_size_and_garbage(client, monkeypatch):
    from app.config import settings

    assert _upload(client, b"%PDF-1.7", "application/pdf").status_code == 415
    assert _upload(client, b"bukan gambar", "image/jpeg").status_code == 422
    monkeypatch.setattr(settings, "max_photo_mb", 1)
    assert _upload(client, b"\xff" * (1024 * 1024 + 1)).status_code == 413
