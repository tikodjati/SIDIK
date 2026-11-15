"""Skenario demo untuk paket juri: akun, data, dan bahan uji siap pakai.

Dijalankan DI DALAM container oleh mulai.sh / mulai.cmd:
  docker compose exec -T app python -m scripts.demo_juri

Membuat akun juri (sandi terdokumentasi, khusus basis data lokal paket ini), tiga penerima, satu
naskah RAHASIA dengan persetujuan ganda, data personel demo (Lapis 4), lalu menulis bahan uji
(foto, teks, dump) ke <data>/bahan_uji. Aman dijalankan ulang: bila akun juri sudah ada, tidak
membuat apa pun lagi.

PENGAMAN: menolak berjalan kecuali SIDIK_DEMO_ALLOW=1 (hanya diatur di docker-compose paket juri)
dan basis datanya adalah container `db` lokal. Sandi di berkas ini publik, jadi jangan pernah
dipakai pada basis data bersama atau layanan yang dijangkau publik.
"""

import json
import os
import random
import sys
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener

import cv2
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core import layer1_visual as l1
from app.db import get_engine
from app.db.models import HoneyTokenRow, User
from app.models.auth_models import UserCreate
from scripts.personnel import hoax_samples
from scripts.spike_layer1 import simulate_camera
from scripts.users import _create

API = "http://127.0.0.1:8000"
PASSWORD = "Juri-SIDIK-2026"  # publik; hanya untuk basis data lokal paket juri
USERS = {
    "juri1": ("Juri 1", "admin"),
    "juri2": ("Juri 2", "admin"),
    "distributor": ("Kapten Inf Dedi Saputra", "distributor"),
    "investigator": ("Mayor Inf Teguh Wibowo", "investigator"),
}
RECIPIENTS = [
    {"nrp": "1102003912", "nama": "Hendro Prasetyo", "pangkat": "Kolonel Inf",
     "jabatan": "Asintel Kasdam Jaya", "satuan": "Kodam Jaya"},
    {"nrp": "1102004417", "nama": "Budi Hartono", "pangkat": "Letkol Inf",
     "jabatan": "Kasiops Korem 051", "satuan": "Korem 051/Wijayakarta"},
    {"nrp": "1102005328", "nama": "Andi Nugraha", "pangkat": "Mayor Chb",
     "jabatan": "Kasubsatgas Siber", "satuan": "Hubdam Jaya"},
]  # fmt: skip


class Api:
    """Klien HTTP minimal (tanpa dependensi tambahan) yang membawa cookie sesi."""

    def __init__(self) -> None:
        self._open = build_opener(HTTPCookieProcessor(CookieJar())).open

    def call(self, method: str, path: str, body: dict | None = None) -> bytes:
        data = json.dumps(body).encode() if body is not None else None
        req = Request(API + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})  # fmt: skip
        with self._open(req, timeout=180) as resp:
            return resp.read()

    def json(self, method: str, path: str, body: dict | None = None):
        raw = self.call(method, path, body)
        return json.loads(raw) if raw else None

    def login(self, username: str) -> "Api":
        self.call("POST", "/api/v1/auth/login", {"username": username, "password": PASSWORD})
        return self


def guard() -> None:
    url = settings.database_url
    if os.environ.get("SIDIK_DEMO_ALLOW") != "1" or "@db:" not in url:
        sys.exit(
            "Ditolak: skenario ini hanya untuk basis data lokal paket juri "
            "(SIDIK_DEMO_ALLOW=1 dan host `db`). Sandinya publik."
        )


def tokens_of(session: Session, copy_id: int) -> list[str]:
    rows = session.scalars(
        select(HoneyTokenRow).where(HoneyTokenRow.copy_id == copy_id)
        .order_by(HoneyTokenRow.token_index)
    )  # fmt: skip
    return [r.value for r in rows]


def simulate_leak(text: str, fraction: float, typo: float, rng: random.Random) -> str:
    """Sama dengan simulasi di dashboard: potongan dari atas, huruf kapital, salah ketik."""
    lines = text.split("\n")
    out = "\n".join(lines[: max(1, round(len(lines) * fraction))]).upper()
    return "".join(ch for ch in out if not (ch.isalpha() and rng.random() < typo))


def write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8", newline="\n")
    else:
        path.write_bytes(content)


def main() -> None:
    guard()
    with Session(get_engine()) as session:
        if session.scalar(select(User).where(User.username == "juri1")) is not None:
            print("Data demo juri sudah ada, tidak ada yang dibuat ulang.")
            return
        for username, (name, role) in USERS.items():
            _create(session, UserCreate(username=username, full_name=name, role=role,
                                        password=PASSWORD))  # fmt: skip
        session.commit()

    out = Path(settings.data_dir) / "bahan_uji"
    dist = Api().login("distributor")
    approver = Api().login("juri2")
    admin = Api().login("juri1")

    rec = [dist.json("POST", "/api/v1/recipients", r) for r in RECIPIENTS]
    doc = dist.json("POST", "/api/v1/documents", {
        "nomor": "ST/412/OPS-SIB/X/2026", "judul": "Kesiapsiagaan Siber KTT Internasional",
        "klasifikasi": "RAHASIA"})  # fmt: skip
    copies = [dist.json("POST", f"/api/v1/documents/{doc['id']}/copies",
                        {"recipient_id": r["id"]}) for r in rec]  # fmt: skip
    # Salinan ketiga sengaja dibiarkan MENUNGGU PERSETUJUAN agar juri bisa mencoba persetujuan
    # ganda sendiri (pengaju tidak boleh menyetujui salinannya).
    for c in copies[:2]:
        approver.call("POST", f"/api/v1/copies/{c['copy_id']}/approve")

    hendro, budi = copies[0]["copy_id"], copies[1]["copy_id"]
    pdf_h = dist.call("GET", f"/api/v1/copies/{hendro}/pdf")
    pdf_b = dist.call("GET", f"/api/v1/copies/{budi}/pdf")
    write(out / "04_salinan_pdf" / "salinan_hendro.pdf", pdf_h)
    write(out / "04_salinan_pdf" / "salinan_budi.pdf", pdf_b)

    # Foto ponsel simulasi (miring, bayangan, blur, JPEG) dan dua pemotongnya.
    page = l1.rasterize_gray(pdf_h, 300)
    photo = simulate_camera(page, 2400, 22, 0.8, 85, random.Random(7))
    h = photo.shape[0]
    jpeg = [cv2.IMWRITE_JPEG_QUALITY, 85]
    for name, img in (
        ("foto_01_miring.jpg", photo),
        ("foto_02_potongan_atas.jpg", photo[: int(h * 0.55)]),
        ("foto_03_potongan_3_baris.jpg", photo[int(h * 0.28) : int(h * 0.36)]),
    ):
        folder = out / "01_foto"
        folder.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(folder / name), img, jpeg)

    with Session(get_engine()) as session:
        th, tb = tokens_of(session, hendro), tokens_of(session, budi)
    text_h = admin.json("GET", f"/api/v1/copies/{hendro}/text")["text"]
    write(out / "02_teks" / "teks_01_ketik_ulang.txt",
          simulate_leak(text_h, 0.7, 0.01, random.Random(3)))  # fmt: skip
    write(out / "02_teks" / "teks_02_parafrase.txt",
          "Info A1, jangan disebar: semua satuan diminta terus memantau jaringan militer di "
          f"frekuensi {th[0].replace('.', ',')} MHz, dan perangkat REG-AL-{th[1]} wajib dicek "
          "teknisi sebelum pertemuan KTT.")  # fmt: skip
    write(out / "02_teks" / "teks_03_kolusi.txt",
          f"Rangkuman gabungan: pantau {th[0]} MHz, cek REG-AL-{th[1]}, laporan lewat "
          f"KOM-{tb[3]}, dokumen lama dimusnahkan via PK-{tb[4]}.")  # fmt: skip
    write(out / "02_teks" / "teks_04_terlalu_pendek.txt",
          "Katanya Kodam Jaya lagi siaga satu untuk KTT.")

    # Lapis 4: data personel (honey-record), sampel dump hoaks, dan ekspor "yang bocor".
    admin.call("POST", "/api/v1/personnel/seed-demo")
    hoax_samples(None)
    leaks = Path(settings.data_dir) / "test_leaks"
    write(out / "03_dump" / "dump_01_hoaks_daur_ulang.csv",
          (leaks / "dump_hoaks_daur_ulang.csv").read_bytes())  # fmt: skip
    write(out / "03_dump" / "dump_02_hoaks_rekaan.csv",
          (leaks / "dump_hoaks_rekaan.csv").read_bytes())  # fmt: skip
    export = dist.call("POST", "/api/v1/personnel/exports", {
        "satuan": "Yonif 201/Jaya Yudha", "purpose": "Rekap kesiapan pengamanan KTT"})  # fmt: skip
    write(out / "03_dump" / "dump_03_bocor_asli.csv", export)

    print("Data demo juri siap. Akun: juri1, juri2 (admin), distributor, investigator.")


if __name__ == "__main__":
    main()
