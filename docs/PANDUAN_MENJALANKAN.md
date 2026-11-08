# Panduan Menjalankan SIDIK

Panduan untuk siapa pun yang ingin menjalankan dan mencoba SIDIK di komputernya sendiri. Ada dua cara:

| | **A. Dengan Docker** (disarankan) | **B. Tanpa Docker** |
| :--- | :--- | :--- |
| Yang perlu dipasang | Git, Docker Desktop | Git, Python 3.12/3.13, Node.js 20.9+, pnpm |
| Database | PostgreSQL (dalam container) | SQLite (satu file) |
| Cocok untuk | Demo, uji bersama, mendekati kondisi nyata | Laptop tanpa Docker, uji cepat |
| Terminal yang dibutuhkan | 1 (bisa ditutup setelah start) | 2 (backend dan frontend, tetap terbuka) |

Kedua cara memakai database yang **terpisah**: akun dan data di satu cara tidak terlihat di cara lainnya.

---

## 1. Ambil kode

```bash
git clone https://github.com/tikodjati/SIDIK
cd SIDIK
git checkout dev
```

Sudah pernah clone? Cukup perbarui:

```bash
git checkout dev
git pull
```

Semua perintah di bawah dijalankan dari folder `SIDIK`, kecuali disebut lain.

---

## 2A. Menjalankan dengan Docker

Pastikan Docker Desktop sudah berjalan.

**Pertama kali**

```bash
docker compose up --build -d
```

Build pertama memakan beberapa menit. Cek ketiga layanan berstatus `running`:

```bash
docker compose ps
```

Buat akun demo (sekali saja):

```bash
docker compose exec api python -m scripts.users seed-demo
```

**Berikutnya** (termasuk setiap habis `git pull`):

```bash
docker compose up --build -d
```

Migrasi database dijalankan otomatis saat API start.

**Mematikan**

```bash
docker compose down
```

**Mulai dari data kosong** (menghapus seluruh isi database, termasuk akun):

```bash
docker compose down -v
docker compose up --build -d
docker compose exec api python -m scripts.users seed-demo
```

Hapus juga `data/keys/demo_users.txt` sebelum `seed-demo`, supaya file kata sandinya tidak bercampur dengan akun lama.

---

## 2B. Menjalankan tanpa Docker

Kalau stack Docker sedang jalan, matikan dulu (`docker compose down`), karena port 8000 dan 3000 akan bentrok.

### Pertama kali

**Backend.** Buka terminal pertama:

```bash
cd backend
python -m venv .venv
```

Aktifkan venv. Di Windows (PowerShell atau CMD):

```bash
.venv\Scripts\activate
```

Di macOS, Linux, atau Git Bash:

```bash
source .venv/bin/activate
```

Pasang dependensi, atur database ke SQLite, buat tabel, dan buat akun demo:

```bash
pip install -e ".[dev]"
```

```bash
python -c "open('.env','w').write('SIDIK_DATABASE_URL=sqlite:///./sidik.db\n')"
```

```bash
python -m alembic upgrade head
```

```bash
python -m scripts.users seed-demo
```

Jalankan backend (biarkan terminal tetap terbuka):

```bash
python -m uvicorn app.main:app --port 8000
```

Tunggu sampai muncul `Application startup complete`. Cek di http://localhost:8000/health, yang harus menampilkan `{"status":"ok"}`.

**Frontend.** Buka terminal kedua:

```bash
cd frontend
pnpm install
pnpm dev
```

Belum punya pnpm? Pasang dengan `npm install -g pnpm`.

### Berikutnya

Terminal 1, di folder `backend` (aktifkan venv dulu):

```bash
python -m uvicorn app.main:app --port 8000
```

Terminal 2, di folder `frontend`:

```bash
pnpm dev
```

### Setiap habis `git pull`

Di folder `backend` (venv aktif):

```bash
pip install -e ".[dev]"
python -m alembic upgrade head
```

Di folder `frontend`:

```bash
pnpm install
```

Ketiganya cepat dan aman kalau memang tidak ada yang berubah.

### Mulai dari data kosong

Hentikan backend, hapus `backend/sidik.db` dan `data/keys/demo_users.txt`, lalu di folder `backend` jalankan:

```bash
python -m alembic upgrade head
python -m scripts.users seed-demo
```

---

## 3. Masuk ke aplikasi

Buka **http://localhost:3000**. Pakai `localhost`, jangan `127.0.0.1`, karena kalau tidak, login akan tampak gagal.

Kata sandi akun demo ada di **`data/keys/demo_users.txt`** (buka dengan editor teks). Sandinya acak, berbeda di setiap komputer, dan tidak ikut git. Jangan dibagikan.

| Akun | Bisa membuka |
| :--- | :--- |
| `distributor` | Dashboard, **Distribusi** (penerima, naskah, terbitkan salinan, unduh PDF) |
| `investigator` | Dashboard, **Investigasi** (analisis foto dan teks), **Audit Trail** |
| `admin` | Semua halaman, termasuk **Pengguna** (kelola akun) dan simulasi kebocoran teks |

Setiap akun bisa mengganti kata sandinya di halaman **Akun** (klik nama di kanan atas). Detail peran ada di [AUTENTIKASI_RBAC.md](AUTENTIKASI_RBAC.md).

**Membuat akun sungguhan** (selain akun demo). Dengan Docker:

```bash
docker compose exec api python -m scripts.users create --username NAMA --full-name "Nama Lengkap" --role admin
```

Tanpa Docker, dari folder `backend` dengan venv aktif:

```bash
python -m scripts.users create --username NAMA --full-name "Nama Lengkap" --role admin
```

Perintah ini meminta kata sandi tanpa menampilkannya (minimal 10 karakter). Akun berikutnya bisa dibuat admin lewat halaman **Pengguna**.

---

## 4. Mencoba alur utama

### Foto halaman bocor (Lapis 1 + 2)

1. **Sebagai `distributor`, buka Distribusi.** Tambah penerima, tambah naskah, pilih keduanya, lalu klik **Terbitkan**. Setelah itu klik **Unduh PDF (cetak)**. Terbitkan juga untuk satu penerima lain sebagai pembanding.
2. **Buat foto bukti.** Pilih salah satu:
   - **Cetak lalu foto dengan HP** (paling realistis). Boleh miring atau terputar, tapi seluruh halaman sebaiknya terlihat dan fokusnya tajam. Kirim foto ke laptop sebagai **Dokumen** di WhatsApp atau lewat Drive, supaya tidak dikompres.
   - **Tangkapan layar PDF** (tanpa printer). Zoom sampai satu halaman memenuhi layar, lalu tangkap layar (Windows: `Win + Shift + S`) dan simpan sebagai PNG.
3. **Sebagai `investigator`, buka Investigasi → tab Foto / scan.** Pilih foto, lalu klik **Analisis bukti**. Dalam sekitar 10–15 detik akan muncul **TARGET TERIDENTIFIKASI**, nama dan NRP penerima pemilik PDF itu, rincian per lapis (spasi dan pilihan kata), serta gambar halaman yang sudah diluruskan.

### Teks yang disalin atau diketik ulang (Lapis 2)

1. **Sebagai `distributor`**, salin teks dari kotak naskah setelah **Terbitkan**, klik **Unduh .txt**, atau buka PDF salinan lalu salin teksnya (`Ctrl + A`, `Ctrl + C`).
2. **Sebagai `investigator`, buka Investigasi → tab Teks / ketik ulang.** Tempel sekitar 80% teks itu (boleh diketik ulang, huruf kapital, sedikit salah ketik), lalu klik **Analisis bukti**.
3. Satu paragraf saja, atau teks bebas, akan menghasilkan **BUKTI TIDAK CUKUP**. Itu hasil yang benar.

PDF salinan membawa kedua lapis: pilihan kata khusus penerima (Lapis 2) dan pergeseran spasi (Lapis 1). Jadi teks yang disalin dari PDF, atau diketik ulang dari kertas cetaknya, juga teridentifikasi.

### Uji penolakan

PDF tanpa watermark harus **ditolak**. Buat PDF-nya dengan Docker:

```bash
docker compose exec api python -m scripts.make_test_pages --layout naskah
```

Atau tanpa Docker, dari folder `backend` dengan venv aktif:

```bash
python -m scripts.make_test_pages --layout naskah
```

Foto atau tangkap layar `data/watermarked_outputs/uji_foto/naskah_kontrol_tanpa_modulasi.pdf`, lalu unggah. Hasil yang diharapkan: **BUKTI TIDAK CUKUP** (sekitar 20 detik). Bila kata milik satu salinan digabung dengan spasi milik salinan lain (tanda manipulasi), hasilnya **BUKTI BERTENTANGAN**, juga tanpa atribusi.

### Jejak audit

Sebagai `investigator`, buka **Audit Trail**. Setiap penerbitan salinan, unduhan PDF, login, dan analisis bukti (termasuk yang ditolak) tercatat dengan nama akun pelakunya. Status **RANTAI VALID** menunjukkan tidak ada catatan yang diubah.

Skenario demo lengkap, termasuk demo manipulasi database, ada di [PANDUAN_DEMO_DASHBOARD.md](PANDUAN_DEMO_DASHBOARD.md).

**Laporkan segera** bila ada hasil yang menunjuk **orang yang salah**. Itu cacat serius. Foto bagus yang ditolak juga perlu dilaporkan, beserta fotonya.

---

## 5. Masalah yang sering terjadi

| Gejala | Penyebab dan solusi |
| :--- | :--- |
| `port is already allocated` / `address already in use` | Port 8000, 3000, atau 5432 sudah dipakai program lain, misalnya PostgreSQL yang terpasang di komputer atau stack Docker yang masih jalan. Tutup program itu. Untuk Docker, `docker compose down`. |
| Login tampak gagal tanpa pesan | Buka `http://localhost:3000`, bukan `127.0.0.1:3000`. |
| Halaman menampilkan "Tidak dapat terhubung ke server API" | Backend belum jalan atau masih memuat. Cek http://localhost:8000/health. |
| "Format foto harus JPEG, PNG, atau WebP" | Foto iPhone berformat HEIC. Ubah ke JPG, atau atur kamera iPhone ke format *Most Compatible*. |
| Analisis foto pertama lebih lama | Normal. Render referensi naskah dibuat sekali setelah server start (sekitar 5 detik ekstra). |
| Tanpa Docker: backend mencoba PostgreSQL dan gagal | Perintah dijalankan di luar folder `backend`, atau `backend/.env` belum dibuat. Ulangi langkah `.env` di bagian 2B. |
| `pip install` gagal di OpenCV atau PyMuPDF | Pakai Python 3.12 atau 3.13 (cek dengan `python --version`). |
| Melihat log kesalahan (Docker) | `docker compose logs api --tail=50` |

---

## 6. Untuk pengembang

**Menjalankan test backend** (dari folder `backend`, venv aktif):

```bash
python -m pytest -q
```

Beberapa test dilewati. Itu test integrasi PostgreSQL, yang aktif hanya bila `SIDIK_TEST_POSTGRES_URL` diisi (lihat [REGISTRI_DAN_LEDGER.md](REGISTRI_DAN_LEDGER.md)).

**Memeriksa frontend** (dari folder `frontend`):

```bash
pnpm lint
pnpm build
```

**Setelah mengubah endpoint API**, perbarui kontrak dan tipe TypeScript:

```bash
cd backend && python -m scripts.export_openapi
cd ../frontend && pnpm gen:api
```

**Pengaturan penting** (variabel lingkungan; untuk Docker isi di `docker-compose.yml`, tanpa Docker isi di `backend/.env`):

| Variabel | Default | Keterangan |
| :--- | :--- | :--- |
| `SIDIK_DATABASE_URL` | PostgreSQL lokal | `sqlite:///./sidik.db` untuk jalur tanpa Docker |
| `SIDIK_COOKIE_SECURE` | `false` | **Wajib `true`** bila dilayani lewat HTTPS |
| `SIDIK_SESSION_HOURS` | `8` | Lama sesi login |
| `SIDIK_LAYER1_DELTA_PT` | `0.5` | Besar pergeseran spasi di PDF salinan (pt) |
| `SIDIK_MAX_PHOTO_MB` | `15` | Batas ukuran foto unggahan |

**Kunci tanda tangan ledger** dibuat otomatis di `data/keys/ledger_ed25519.pem` (tidak ikut git). Cadangkan file ini, karena tanpa kunci itu riwayat ledger lama tidak bisa diverifikasi.
