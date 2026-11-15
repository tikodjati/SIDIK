# Panduan Juri: menjalankan dan menguji SIDIK

Panduan ini untuk juri yang menerima SIDIK sebagai folder atau zip. Sistem berjalan **di komputer
Anda sendiri** lewat Docker, dengan akun dan data demo yang sudah disiapkan. Internet hanya
dibutuhkan saat pertama kali mengunduh komponen (dan untuk halaman dokumentasi API `/docs`). Tidak
ada data yang keluar dari komputer Anda.

Ringkasan: **pasang Docker → klik dua kali `mulai.cmd` (Windows) atau jalankan `./mulai.sh`
(Linux/macOS) → buka http://localhost:3000.**

## 1. Yang dibutuhkan

| Kebutuhan | Keterangan |
| :--- | :--- |
| Docker Desktop (Windows/macOS) atau Docker Engine + Compose v2 (Linux) | https://www.docker.com/products/docker-desktop/ |
| RAM | Sisakan minimal **4 GB** untuk Docker. Sistem memakai sekitar 1 GB setelah dipakai (terukur: aplikasi 0,8 GB + database 0,05 GB). |
| Ruang disk | Sekitar **6 GB** (image dan komponen build). |
| Internet | Hanya untuk **jalan pertama** (mengunduh komponen). Setelah itu tidak perlu. Paket `-offline` tidak butuh internet sama sekali. |
| Port | 3000 (bisa diganti, lihat bagian 7). |

Docker Desktop harus **sedang berjalan** (ikon paus di baris tugas/menu bar tidak berstatus
"starting").

## 2. Menyalakan sistem

1. Ekstrak zip, lalu buka foldernya.
2. Jalankan:
   - **Windows:** klik dua kali **`mulai.cmd`**.
   - **Linux/macOS:** buka terminal di folder ini, jalankan `./mulai.sh`
     (bila ditolak: `bash mulai.sh`).
3. Tunggu sampai muncul tulisan **`SIDIK siap: http://localhost:3000`**. Browser terbuka otomatis.

Jalan pertama membangun image: **sekitar 5-15 menit** tergantung internet. Jalan berikutnya hanya
beberapa detik. Skrip aman dijalankan berulang kali dan tidak menggandakan data.

Skrip melakukan empat hal: menyalakan sistem (web + API + database lokal), membuat akun juri,
mengisi data demo, dan menyalin **bahan uji** ke folder `bahan_uji/` di samping skrip ini.

## 3. Akun

Semua akun memakai kata sandi yang sama: **`Juri-SIDIK-2026`** (hanya berlaku di komputer Anda).

| Nama pengguna | Peran | Dipakai untuk |
| :--- | :--- | :--- |
| `juri1` | admin | Hampir semua fitur, termasuk menyetujui salinan RAHASIA. |
| `juri2` | admin | Penyetuju kedua untuk persetujuan ganda (four-eyes). |
| `distributor` | distributor | Mendaftarkan penerima/naskah dan menerbitkan salinan. |
| `investigator` | investigator | Menganalisis bukti kebocoran dan membaca audit trail. |

Peran menentukan menu yang terlihat. Untuk mencoba semuanya cukup masuk sebagai **`juri1`**.

## 4. Apa itu SIDIK, dalam satu paragraf

Setiap salinan dokumen dan setiap ekspor data diberi **identitas penerimanya sendiri yang tak
kasat mata**. Bila salinan itu bocor (difoto, diketik ulang, diparafrase, atau datanya diunggah ke
forum gelap), SIDIK menunjuk **salinan sumbernya**. Bila bukti tidak cukup, SIDIK **menolak
menebak**: tidak ada salah tuduh. Ada empat lapis penanda dan satu pemeriksa klaim; ringkasannya di
`README.md`.

## 5. Uji dalam 10 menit

Semua berkas ada di folder **`bahan_uji/`**. Masuk sebagai `juri1`, lalu buka **Investigasi**.
Kolom kanan adalah hasil yang diharapkan, **diukur langsung pada paket ini** (diunggah ke sistem
yang berjalan dari nol).

### A. Foto halaman bocor (Lapis 1 + 2 + 3)
Tab **Foto / scan (Lapis 1 + 2 + 3)**, unggah berkas, klik analisis. Waktu proses 10-20 detik.

| Berkas | Hasil yang diharapkan |
| :--- | :--- |
| `01_foto/foto_01_miring.jpg` | **TARGET TERIDENTIFIKASI**: Hendro Prasetyo, bukti terbaca 270 dari 270 bit. Foto miring 22°, buram, JPEG. |
| `01_foto/foto_02_potongan_atas.jpg` | **TARGET TERIDENTIFIKASI**: Hendro Prasetyo (sekitar 120 dari 270 bit terbaca; angkanya sedikit berbeda antar-instalasi) walau hanya bagian atas halaman terlihat. |
| `01_foto/foto_03_potongan_3_baris.jpg` | **BUKTI TIDAK CUKUP** ("Sistem menolak menebak"). Tiga baris tidak cukup untuk menunjuk siapa pun, dan itulah yang benar. |

### B. Teks bocor (Lapis 2 + 3)
Tab **Teks / ketik ulang / parafrase (Lapis 2 + 3)**, tempel isi berkas, klik analisis.

| Berkas | Hasil yang diharapkan |
| :--- | :--- |
| `02_teks/teks_01_ketik_ulang.txt` | **TARGET TERIDENTIFIKASI**: Hendro. Naskah diketik ulang 70%, huruf kapital, dengan salah ketik. |
| `02_teks/teks_02_parafrase.txt` | **TARGET TERIDENTIFIKASI**: Hendro, lewat **angka fakta unik** (Lapis 3) walau kalimatnya ditulis ulang total dan hampir tanpa kata varian. |
| `02_teks/teks_03_kolusi.txt` | **INDIKASI KOLUSI**: dua salinan ditunjuk (Hendro dan Budi), penerima lain tidak. |
| `02_teks/teks_04_terlalu_pendek.txt` | **BUKTI TIDAK CUKUP**: satu kalimat tanpa angka tidak ditunjuk ke siapa pun. |

### C. Klaim "database bocor" (Lapis 4)
Tab **Data dump (Lapis 4)**, unggah berkas.

| Berkas | Hasil yang diharapkan |
| :--- | :--- |
| `03_dump/dump_03_bocor_asli.csv` | **KEBOCORAN ASLI**: puluhan baris yang identitasnya cocok dengan data personel, terlacak ke **ekspor #1**, akun `distributor`, satuan Yonif 201/Jaya Yudha, beserta waktu pembuatannya. |
| `03_dump/dump_01_hoaks_daur_ulang.csv` | **HOAKS: DAUR ULANG**: data publik lama yang diberi kop militer. |
| `03_dump/dump_02_hoaks_rekaan.csv` | **HOAKS: DATA REKAAN**: format NIK banyak yang tidak valid. |

### D. Persetujuan ganda (four-eyes) dan rantai bukti
1. Masuk sebagai **`distributor`**, buka **Distribusi**. Salinan **Andi Nugraha** berstatus
   **MENUNGGU PERSETUJUAN**. PDF-nya belum bisa diunduh dan salinan itu tidak pernah dipakai untuk
   atribusi.
2. Keluar, masuk sebagai **`juri2`**, lalu klik **Setujui**. Statusnya menjadi **TERBIT** dan PDF
   bisa diunduh.
3. Untuk melihat penolakan: masuk sebagai **`juri1`**, daftarkan satu penerima baru, terbitkan
   salinan RAHASIA untuknya, lalu klik **Setujui** pada pengajuanmu sendiri. Sistem menolak:
   *"Persetujuan harus oleh pejabat lain, bukan pengaju (four-eyes)."*
4. Buka **Audit Trail**. Setiap tindakan, termasuk analisis yang ditolak, tercatat dengan nama
   pelaku. Status **RANTAI VALID** berarti tidak ada catatan yang diubah.

### E. Coba dengan foto Anda sendiri
Buka `bahan_uji/04_salinan_pdf/salinan_hendro.pdf`, tampilkan di layar atau cetak, lalu **foto dengan
ponsel** (miring, dari jarak biasa) dan unggah di tab Foto. Salinan Budi ada di folder yang sama.
Foto layar laptop juga terbaca asalkan hampir seluruh halaman terlihat. Hasil yang kami ukur ada di
bagian 9.

### F. Dokumentasi API
Buka http://localhost:3000/docs untuk dokumentasi interaktif (OpenAPI). Halaman ini memuat
komponen tampilannya dari internet, jadi butuh koneksi.

## 6. Mematikan dan memulai ulang

| Perintah | Efek |
| :--- | :--- |
| `berhenti.cmd` / `./berhenti.sh` | Mematikan sistem. **Data tetap tersimpan.** |
| `mulai.cmd` / `./mulai.sh` | Menyalakan lagi (cepat) dan menyalin ulang bahan uji. |
| `reset.cmd` / `./reset.sh` | Mematikan dan **menghapus semua data**, lalu `mulai` memulai dari bersih. |

## 7. Pemecahan masalah

| Gejala | Penyebab dan tindakan |
| :--- | :--- |
| "Docker belum terpasang / belum berjalan" | Pasang atau buka Docker Desktop, tunggu hingga siap, jalankan ulang. |
| "port is already allocated" / bentrok port 3000 | Port dipakai aplikasi lain. Windows: buka Command Prompt di folder ini, ketik `set SIDIK_PORT=3300`, lalu `mulai.cmd` (jangan klik dua kali). Linux/macOS: `SIDIK_PORT=3300 ./mulai.sh`. Lalu buka `http://localhost:3300`. |
| Build gagal / terhenti saat mengunduh | Koneksi terputus. Jalankan ulang `mulai`; unduhan yang selesai tidak diulang. Bila internet sulit, minta paket `-offline`. |
| "no space left on device" | Ruang disk Docker habis. Kosongkan lewat Docker Desktop (Settings → Resources) lalu ulangi. |
| Sistem sangat lambat atau analisis foto gagal | Docker kekurangan memori. Docker Desktop → Settings → Resources → Memory, naikkan ke **4 GB atau lebih**. |
| Login tampak gagal | Buka **`localhost`**, bukan `127.0.0.1` (cookie sesi). Pastikan nama pengguna huruf kecil. |
| Halaman tidak terbuka tetapi skrip bilang siap | Tunggu beberapa detik lalu muat ulang. Cek: `docker compose -f juri/docker-compose.yml logs app`. |
| Analisis foto terasa lama | Normal: 10-30 detik per foto, karena semua kandidat pelurusan dicoba. |
| `./mulai.sh: Permission denied` | Jalankan `bash mulai.sh`. |
| Mac berprosesor Apple Silicon | Seharusnya berjalan dengan build online (komponen yang dipakai mendukung arm64), tetapi **belum kami uji** di perangkat itu. Paket `-offline` dibuat di komputer x86 sehingga berjalan lewat emulasi dan lebih lambat. |

Log lengkap: `docker compose -f juri/docker-compose.yml logs app` (aplikasi) dan `... logs db`
(database).

## 8. Bila Docker tidak bisa dipakai

- **Tanpa Docker:** SIDIK juga bisa dijalankan dengan Python 3.12 dan Node 22
  (`docs/PANDUAN_MENJALANKAN.md`, bagian 2B "Menjalankan tanpa Docker"). Akun dibuat dengan
  `python -m scripts.users create`.
- **Tanpa menjalankan apa pun:** folder `video_demo/` berisi **video demo** (subtitle `.srt`) yang
  memperlihatkan seluruh fitur memakai tangkapan layar asli sistem ini.
- **Bukti terukur:** `docs/HASIL_LAPIS2.md`, `HASIL_LAPIS3.md`, `HASIL_LAPIS4.md`,
  `SPIKE_LAYER1_HASIL.md`, dan proposal di folder `Documents/`.

## 9. Hasil uji yang kami ukur (bukan klaim)

| Uji | Hasil |
| :--- | :--- |
| Foto HP asli halaman uji (11 foto, miring sampai 35°) | 6/7 salinan bertanda teridentifikasi, 4/4 kontrol ditolak, **0 salah** |
| Foto potongan, cap, tanda tangan, lipat empat (simulasi) | Semua teridentifikasi, **0 salah**; potongan 3 baris ditolak |
| Ketik ulang 62% naskah / parafrase + 2 angka fakta | Teridentifikasi |
| Kolusi 2 salinan | Keduanya teridentifikasi, penerima lain tidak tertuduh |
| Dump ekspor, dump tabel, dan hoaks | Terlacak ke ekspor/akun, ke "akses langsung DB", atau ditandai DAUR ULANG / REKAAN |
| Tes otomatis | 233 lulus |

Batasan yang kami catat apa adanya (naskah perlu template, kutipan sangat pendek tanpa angka tidak
bisa diatribusi, kolusi andal untuk 2-3 orang): `README.md` bagian "Batasan" dan
`docs/TANGGAPAN_ISSUE_GAP.md`.

## 10. Keamanan dan data

- Semua data di sistem ini **rekaan** (nama, NRP, NIK, nomor surat). Tidak ada data nyata.
- Basis data hanya ada di komputer Anda (container `db`, tidak dibuka ke jaringan). Kata sandi
  `Juri-SIDIK-2026` dan kunci audit trail hanya berlaku untuk instalasi lokal ini; skenario demo
  menolak berjalan di basis data selain container lokal paket ini.
- Menghapus semuanya: `reset`, lalu hapus folder ini.
