# SIDIK — Sistem Identifikasi Dokumen dan Investigasi Kebocoran

Kartika Cyber Hackathon · kategori **Defensive Shield**.

SIDIK memberi setiap salinan dokumen dan setiap ekspor data **identitas penerimanya sendiri** yang tidak
kasat mata. Bila salinan itu bocor (difoto, diketik ulang, diparafrase, atau datanya diunggah ke forum
gelap), SIDIK menunjuk salinan sumbernya. Bila buktinya tidak cukup, SIDIK **menolak menebak**.

## Empat lapis perlindungan

| Lapis | Penanda | Tahan terhadap | Bukti dibaca dari |
| :-: | :--- | :--- | :--- |
| 1 | Spasi antar-kata digeser berpasangan ±0,5 pt (naskah tetap rata kanan-kiri) | Foto HP miring, foto layar, scan, potongan setengah halaman, cap, tanda tangan, lipatan | Foto/scan (tanpa OCR) |
| 2 | Pilihan kata varian Tata Naskah Dinas + Reed-Solomon | Salin-tempel, ketik ulang, salah ketik, kutipan sebagian | Teks dan foto |
| 3 | Angka fakta fiktif unik per penerima (honey-token) | Parafrase total, kolusi 2–3 orang | Teks dan foto |
| 4 | Persona fiktif di basis data dan di setiap ekspor (honey-record) | SQL injection, ekspor yang dibocorkan, klaim hoaks | Dump CSV/SQL/JSON/teks |

Lapis 1 dan 2 digabung dalam **satu dekode**. Bila keduanya menunjuk salinan berbeda, hasilnya ditolak
sebagai bukti bertentangan.

Fitur pendukung:
- **Pemeriksa klaim (anti-psywar)**: membedakan kebocoran asli, daur ulang data publik lama, dan data
  rekaan; juga mengukur kemiripan dokumen dengan naskah resmi.
- **Persetujuan ganda (four-eyes)** untuk salinan naskah RAHASIA/SANGAT RAHASIA.
- **RBAC** tiga peran.
- **Audit trail**: rantai hash SHA-256 bertanda tangan Ed25519, *append-only*, dan bisa diverifikasi.

## Hasil uji (ringkas)

| Uji | Hasil |
| :--- | :--- |
| Foto HP asli halaman uji (11 foto, miring sampai 35°) | 6/7 teridentifikasi, 4/4 kontrol ditolak, **0 salah** |
| Foto potongan, cap, tanda tangan, lipat empat (simulasi) | Semua teridentifikasi, **0 salah**; potongan 3 baris ditolak |
| Ketik ulang 62% naskah / parafrase + 2 angka fakta | Teridentifikasi |
| Kolusi 2 salinan | Keduanya teridentifikasi, penerima lain tidak tertuduh |
| Dump ekspor, dump tabel, dan hoaks | Terlacak ke ekspor/akun, ke "akses langsung DB", atau ditandai DAUR ULANG / REKAAN |
| Tes otomatis | 231 lulus |

Rincian: [proposal Bagian 2.7](Documents/PROPOSAL_DAN_SPESIFIKASI_SIDIK.md) ·
[Lapis 1](docs/SPIKE_LAYER1_HASIL.md) · [Lapis 2](docs/HASIL_LAPIS2.md) ·
[Lapis 3](docs/HASIL_LAPIS3.md) · [Lapis 4](docs/HASIL_LAPIS4.md) ·
[tanggapan issue/gap](docs/TANGGAPAN_ISSUE_GAP.md)

## Menjalankan

Butuh Docker. Panduan lengkap (dengan atau tanpa Docker, database bersama tim, dan masalah umum):
[docs/PANDUAN_MENJALANKAN.md](docs/PANDUAN_MENJALANKAN.md).

```bash
docker compose up --build -d
```

```bash
docker compose exec api python -m scripts.users seed-demo
```

Perintah kedua membuat akun `admin`, `distributor`, dan `investigator`, dengan sandi di
`data/keys/demo_users.txt`. Jalankan sekali saja, dan hanya pada database lokal.

Setelah itu:
- Web: http://localhost:3000
- API dan dokumentasi interaktif: http://localhost:8000/docs
- Data demo Lapis 4: halaman **Data Personel → Isi data demo**, lalu
  `docker compose exec api python -m scripts.personnel hoax-samples`

Urutan demo 3 menit: [docs/PANDUAN_DEMO_DASHBOARD.md](docs/PANDUAN_DEMO_DASHBOARD.md) ·
peran dan akun: [docs/AUTENTIKASI_RBAC.md](docs/AUTENTIKASI_RBAC.md)

## Struktur

```
backend/    FastAPI (Python 3.12/3.13): app/core = mesin forensik, app/api = endpoint, tests/
frontend/   Next.js 16 + Tailwind v4: dashboard taktis
data/       master_templates (template naskah, di-commit); keys, test_leaks (lokal, diabaikan git)
docs/       keputusan arsitektur, hasil uji per lapis, panduan, openapi.json
Documents/  proposal dan strategi penilaian
```

Template naskah (`data/master_templates/naskah_demo.txt`) bisa diubah tanpa menyentuh kode:
- `{a|b}` atau `{a|b|c|d}` = varian kata (1 atau 2 bit)
- `[[1##.###]]` = honey-token

Validator otomatis menolak template yang tidak aman.

## Batasan (dicatat apa adanya)

- **Butuh template.** Belum *blind watermarking* untuk PDF bebas. Kamus varian di naskah demo belum
  disahkan ahli Jukminu.
- **Kutipan sangat pendek** tanpa angka token, dan foto 2–3 baris, tidak bisa diatribusi. Ini batas
  matematis, dan sistem menolak menebak.
- **Kolusi** andal untuk 2–3 orang. Kode Tardos, HSM, radar OSINT, dan konektor SISFO masih roadmap.
- **Analisis foto** 10–30 detik per foto.

Penjelasan dan alasan setiap batasan: [docs/TANGGAPAN_ISSUE_GAP.md](docs/TANGGAPAN_ISSUE_GAP.md).

## Untuk pengembang

- **Tes backend**: `cd backend && python -m pytest -q` (dan `ruff check .`). Tes frontend: `pnpm lint`
  dan `npx tsc --noEmit`.
- **Kontrak API**: setelah mengubah endpoint, jalankan `cd backend && python -m scripts.export_openapi`,
  lalu `cd frontend && pnpm gen:api`.
- **Alur tim**: `main` dilindungi; satu fitur = satu branch + PR; commit konvensional (`feat:`, `fix:`,
  `docs:`). CI menjalankan lint, test, dan build.
