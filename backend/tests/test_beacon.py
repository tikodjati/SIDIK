import json

import fitz
import pytest

from app.core import layer1_visual as l1
from app.core import naskah
from app.db import models

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
    "klasifikasi": "KONFIDENSIAL",
}


def _setup_copy(client):
    r = client.post("/api/v1/recipients", json=RECIPIENT).json()
    d = client.post("/api/v1/documents", json=DOCUMENT).json()
    res = client.post(f"/api/v1/documents/{d['id']}/copies", json={"recipient_id": r["id"]})
    assert res.status_code == 201
    return res.json()


def test_layer1_pdf_embeds_canary_beacon():
    """Memverifikasi bahwa layer1_visual menyematkan OpenAction beacon ke dalam PDF ISO 32000."""
    url = "https://sidik.tniad.mil.id/api/v1/beacon/88219"
    layout = l1.spike_layout()
    pdf_bytes = l1.render_pdf(layout, frame=None, delta_pt=0.75, beacon_url=url)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    catalog_xref = doc.pdf_catalog()
    catalog_keys = doc.xref_get_keys(catalog_xref)

    # Memastikan OpenAction tersimpan di Catalog
    assert "OpenAction" in catalog_keys
    action_str = doc.xref_get_key(catalog_xref, "OpenAction")[1]
    assert url in action_str

    # Memastikan tautan mikro 1x1 disematkan
    page = doc[0]
    links = list(page.get_links())
    assert any(link.get("uri") == url for link in links)
    doc.close()


def test_naskah_copy_pdf_passes_beacon():
    """Memverifikasi fungsi copy_pdf dari naskah meneruskan beacon_url."""
    url = "https://sidik.tniad.mil.id/api/v1/beacon/99912"
    pdf_bytes = naskah.copy_pdf(
        copy_id=99912,
        delta_pt=0.75,
        beacon_url=url,
    )
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    catalog_str = doc.xref_get_key(doc.pdf_catalog(), "OpenAction")[1]
    assert url in catalog_str
    doc.close()


def test_beacon_trigger_endpoint_anonymous(anon, client, session):
    """Pemicuan suar via GET /api/v1/beacon/{copy_id} dapat diakses publik tanpa login."""
    copy = _setup_copy(client)
    copy_id = copy["copy_id"]

    headers = {
        "x-forwarded-for": "103.145.22.8, 192.168.1.1",
        "user-agent": "Adobe Acrobat Reader DC 2026 (Windows NT 10.0)",
    }

    # Anonim (eksternal / peretas) membuka file PDF yang memicu beacon GET
    res = anon.get(f"/api/v1/beacon/{copy_id}", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/gif"
    assert res.content.startswith(b"GIF89a")

    # Pastikan tercatat di pangkalan data
    hits = session.query(models.BeaconHit).filter_by(copy_id=copy_id).all()
    assert len(hits) == 1
    assert hits[0].ip_address == "103.145.22.8"
    assert "Adobe Acrobat" in hits[0].user_agent

    # Pastikan tercatat di Buku Besar Audit (Ed25519)
    ledger_entries = session.query(models.LedgerEntry).all()
    beacon_events = [
        json.loads(e.body)
        for e in ledger_entries
        if json.loads(e.body).get("event") == "BEACON_TRIGGERED"
    ]
    assert len(beacon_events) == 1
    event_data = beacon_events[0]["data"]
    assert event_data["copy_id"] == copy_id
    assert event_data["ip_address"] == "103.145.22.8"
    assert event_data["recipient_nrp"] == "1102003912"


def test_beacon_trigger_nonexistent_copy_is_stealthy(anon):
    """Bila copy_id tidak valid, tetap kembalikan 1x1 GIF agar tidak membocorkan struktur."""
    res = anon.get("/api/v1/beacon/99999999")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/gif"


def test_beacon_hits_rbac(anon, login_as, client):
    """Daftar beacon hits hanya boleh diakses oleh INVESTIGATOR atau ADMIN."""
    _setup_copy(client)

    # Anon ditolak 401
    assert anon.get("/api/v1/beacon/hits").status_code == 401

    # Distributor ditolak 403
    distributor = login_as("distributor")
    assert distributor.get("/api/v1/beacon/hits").status_code == 403

    # Investigator diizinkan 200
    investigator = login_as("investigator")
    res = investigator.get("/api/v1/beacon/hits")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_beacon_simulate_creates_hit_and_ledger(login_as, client):
    """Simulasi suar oleh investigator mencatat hit dan event ledger."""
    copy = _setup_copy(client)
    investigator = login_as("investigator")

    payload = {
        "ip_address": "185.220.101.5",  # Tor exit node
        "user_agent": "curl/7.88.1 (DarkWeb Exfiltrator)",
        "referer": "https://breached-forum.onion/threads/1908",
    }
    res = investigator.post(f"/api/v1/beacon/{copy['copy_id']}/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ip_address"] == "185.220.101.5"
    assert data["copy_id"] == copy["copy_id"]
    assert data["document_nomor"] == "ST/412/OPS-SIB/X/2026"
    assert data["recipient_nama"] == "Hendro Wicaksono"

    # Verifikasi muncul di GET /api/v1/beacon/hits
    hits_res = investigator.get("/api/v1/beacon/hits")
    assert hits_res.status_code == 200
    hits = hits_res.json()
    assert len(hits) >= 1
    assert hits[0]["ip_address"] == "185.220.101.5"
