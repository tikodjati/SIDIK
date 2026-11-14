# Deploy SIDIK sebagai satu layanan

Selain `docker compose` untuk pengembangan lokal ([PANDUAN_MENJALANKAN.md](PANDUAN_MENJALANKAN.md)),
SIDIK bisa dijalankan sebagai **satu container** yang melayani web dan API di satu alamat. Bentuk ini
dipakai untuk versi uji yang dibuka lewat URL tanpa clone atau Docker.

```
Pengguna → https://ALAMAT   (satu container: web Next.js + API FastAPI)
              └─ Next meneruskan /api/* ke API di dalam container → PostgreSQL
```

Karena web dan API berada di satu domain, cookie sesi (`SameSite=Strict`) tetap terkirim dan tidak
ada urusan CORS.

## Isi paket

| Berkas | Fungsi |
| :--- | :--- |
| `deploy/hf/Dockerfile` | Dua tahap: membangun frontend, lalu image runtime Python + Node. Berjalan sebagai user 1000. |
| `deploy/hf/start.sh` | Migrasi skema, memuat kunci ledger, lalu menyalakan API (internal) dan web (publik). |
| `deploy/make_hf_space.py` | Merakit folder siap-push (`deploy/_hf_space_out/`) dari repo ini. Tidak menyalin `.env`, kunci, atau database. |

Merakit paket (dari akar repo):

```bash
python deploy/make_hf_space.py
```

Folder hasilnya berisi `Dockerfile` di akarnya, jadi bisa dibangun langsung oleh layanan hosting
yang mendukung Docker.

## Variabel lingkungan

Nilai rahasia diisi lewat fitur *secrets* layanan hosting, tidak pernah ditulis di berkas repo.

| Variabel | Wajib | Keterangan |
| :--- | :-: | :--- |
| `SIDIK_DATABASE_URL` | ya | Connection string PostgreSQL. Pakai database **terpisah** dari lingkungan lain (pengembangan, tim). |
| `SIDIK_SIGNING_KEY_PEM` | ya | Kunci ledger Ed25519 (PEM satu baris, `\n` literal). Buat dengan `python -m scripts.ledger_key`. |
| `SIDIK_COOKIE_SECURE` | – | `true` (sudah diatur di image) karena dilayani lewat HTTPS. |
| `SIDIK_WORKERS` | – | Jumlah worker API (bawaan 2). |
| `BACKEND_URL`, `NEXT_PUBLIC_API_URL` | – | Ditanam saat build image (`http://127.0.0.1:8000` dan `/`). |

Kunci ledger menandatangani seluruh audit trail. Kunci yang sama harus dipakai sepanjang umur
database tersebut: kunci berbeda membuat penulisan ledger ditolak. Jangan membuat ulang kunci untuk
database yang sudah berisi entri.

## Kapasitas (hasil ukur)

- Satu analisis foto memakai memori puncak sekitar **520 MB** dan sekitar **30 detik**. Seluruh
  container (web + API, 2 worker) sekitar **740 MB** saat satu analisis berjalan, sehingga layanan
  dengan RAM 512 MB tidak memadai.
- Unggahan foto sampai 15 MB dan berkas dump sampai 20 MB diterima lewat proxy Next
  (`proxyClientMaxBodySize` 25 MB); batas sebenarnya dijaga backend dan ditolak dengan 413.
- Permintaan analisis hingga 180 detik tidak diputus proxy (`proxyTimeout`).

## Akun

Akun dibuat lewat skrip terhadap database layanan ini, bukan lewat `seed-demo`:

```bash
python -m scripts.users create --username NAMA --full-name "Nama Lengkap" --role admin --password-stdin
```

Persetujuan ganda (four-eyes) butuh dua pengguna berbeda, jadi siapkan minimal dua akun yang
berhak menyetujui.

## Catatan

- Isi hanya **data dummy**. Layanan ini dapat dijangkau publik.
