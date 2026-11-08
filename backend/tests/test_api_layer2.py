def test_watermark_then_extract_roundtrip(client):
    wm = client.post("/api/v1/layer2/watermark", json={"copy_id": 123456789, "flags": 3})
    assert wm.status_code == 200
    body = wm.json()
    assert body["capacity_bits"] >= 104
    res = client.post("/api/v1/layer2/extract", json={"text": body["text"]}).json()
    assert res["status"] == "IDENTIFIED"
    assert (res["copy_id"], res["flags"]) == (123456789, 3)


def test_extract_refuses_unrelated_text(client):
    res = client.post("/api/v1/layer2/extract", json={"text": "Rapat membahas anggaran kantin."})
    assert res.status_code == 200
    assert res.json()["status"] == "INSUFFICIENT_FORENSIC_ARTIFACTS"
    assert res.json()["copy_id"] is None


def test_watermark_validates_copy_id(client):
    assert client.post("/api/v1/layer2/watermark", json={"copy_id": -1}).status_code == 422
    assert client.post("/api/v1/layer2/watermark", json={"copy_id": 2**32}).status_code == 422
