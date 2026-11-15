# SIDIK: mulai di sini

Sistem berjalan di komputer Anda lewat Docker, dengan akun dan data demo yang sudah siap.

1. Pasang dan jalankan **Docker Desktop** (https://www.docker.com/products/docker-desktop/).
2. **Windows:** klik dua kali `mulai.cmd`. **Linux/macOS:** jalankan `./mulai.sh`.
   Jalan pertama sekitar 5-15 menit (mengunduh komponen). Berikutnya hanya beberapa detik.
3. Buka **http://localhost:3000** setelah muncul tulisan "SIDIK siap".

## Akun (semua bersandi `Juri-SIDIK-2026`)

| Nama pengguna | Peran |
| :--- | :--- |
| `juri1` | admin (cukup ini untuk mencoba hampir semuanya) |
| `juri2` | admin kedua (untuk persetujuan ganda) |
| `distributor` | distributor |
| `investigator` | investigator |

## Uji 5 menit

Masuk sebagai `juri1`, buka **Investigasi**, lalu unggah berkas dari folder `bahan_uji/`:

- `01_foto/foto_01_miring.jpg` (tab Foto): **TARGET TERIDENTIFIKASI**, Hendro Prasetyo.
- `02_teks/teks_03_kolusi.txt` (tab Teks): **INDIKASI KOLUSI**.
- `02_teks/teks_04_terlalu_pendek.txt` (tab Teks): **BUKTI TIDAK CUKUP**, sistem menolak menebak.
- `03_dump/dump_01_hoaks_daur_ulang.csv` (tab Data dump): **HOAKS: DAUR ULANG**.

Daftar lengkap beserta hasil yang diharapkan: **`docs/PANDUAN_JURI.md`** (bagian 5).
Ada masalah (port bentrok, Docker belum jalan, dan sebagainya): bagian 7 panduan yang sama.

## Cadangan

- Folder `video_demo/`: video demo seluruh fitur, tanpa perlu menjalankan apa pun.
- Mematikan: `berhenti.cmd` / `./berhenti.sh`. Menghapus semua data: `reset.cmd` / `./reset.sh`.

Semua data di sistem ini rekaan.
