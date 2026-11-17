# Panduan Demo Panggung (3 Menit)

Panduan ini adalah urutan klik untuk naskah pitch di proposal (Bagian 3). Persiapkan semuanya **H-1**,
supaya di panggung tinggal unggah dan klik.

## A. Persiapan H-1

### 1. Jalankan sistem
```bash
docker compose up --build -d
```
Buka http://localhost:3000. Analisis foto pertama sesudah start sedikit lebih lama, jadi lakukan satu
analisis pemanasan sebelum tampil.

### 2. Akun
Siapkan tiga peran: `admin`, `distributor`, dan `investigator`.
- **Database lokal**: jalankan `docker compose exec api python -m scripts.users seed-demo`. Sandinya ada
  di `data/keys/demo_users.txt`.
- **Database bersama tim (Neon)**: jangan memakai `seed-demo`. Buat akun lewat halaman **Pengguna**.

Untuk demo persetujuan ganda, pengaju dan penyetuju harus akun yang berbeda, misalnya distributor
mengajukan lalu admin menyetujui.

### 3. Salinan RAHASIA untuk tokoh demo
1. Masuk sebagai **distributor**, lalu buka **Distribusi**.
2. Daftarkan 3 penerima. Contoh: Kolonel Inf **Hendro**, NRP `1102003912`, Asintel, Kodam Jaya, ditambah
   dua penerima lain (untuk demo kolusi).
3. Daftarkan naskah `ST/412/OPS-SIB/X/2026` dengan klasifikasi **RAHASIA**.
4. Terbitkan salinan untuk ketiga penerima. Statusnya **MENUNGGU PERSETUJUAN**.
5. Masuk sebagai **admin**, lalu klik **Setujui** di tabel "Salinan dan pengajuan". Statusnya menjadi **TERBIT**.
6. Unduh **PDF** salinan Hendro dan **cetak A4**. Unduh juga PDF satu penerima lain (untuk demo kolusi).

### 4. Uji foto sekali sebelum tampil
Foto kertas cetak itu, lalu unggah di **Investigasi → Foto**. Pastikan hasilnya **TARGET TERIDENTIFIKASI**.
Simpan foto yang berhasil sebagai cadangan kalau pemotretan live gagal.

### 5. Teks bocoran yang disiapkan
Ambil angka dari PDF salinan Hendro: **frekuensi** di butir 3.c (`1xx.xxx MHz`) dan **REG-AL** di butir 5.a.

| Berkas | Isi |
| :--- | :--- |
| `demo_ketik_ulang.txt` | Masuk sebagai admin, lalu buka Investigasi → Teks → *Simulasi kebocoran*: pilih salinan Hendro, bagian teks **70%**, centang huruf kapital dan salah ketik, klik *Buat teks bocor simulasi*, lalu salin hasilnya |
| `demo_parafrase.txt` | `Info A1: semua satuan diminta terus memantau jaringan militer di frekuensi <FREKUENSI> MHz, dan perangkat REG-AL-<NOMOR> wajib dicek sebelum pertemuan. Jangan disebar.` |
| `demo_kolusi.txt` (cadangan) | Satu kalimat yang memuat 2 angka token Hendro dan 2 angka token penerima lain |

### 6. Data personel dan sampel dump
1. Masuk sebagai **admin**, buka **Data Personel**, lalu klik **Isi data demo** (sekali per basis data).
2. Buat sampel dump hoaks:
   ```bash
   docker compose exec api python -m scripts.personnel hoax-samples
   ```
   Perintah ini menghasilkan `data/test_leaks/dump_hoaks_daur_ulang.csv` dan `dump_hoaks_rekaan.csv`.
3. Di **Data Personel**, ekspor CSV satuan *Yonif 201/Jaya Yudha* dengan keperluan "Rekap kesiapan KTT".
   Simpan berkasnya sebagai `dump_bocor_forum.csv`; berkas inilah "kebocoran asli" untuk demo.

### 7. Siapkan tab browser
Siapkan dua tab: **Investigasi** (masuk sebagai admin, supaya kartu simulasi tersedia) dan **Audit Trail**.

## B. Urutan Klik di Panggung

| Waktu | Aksi | Hasil yang harus tampil |
| :--- | :--- | :--- |
| 00:00–00:25 | Slide pembuka (tanpa dashboard) | — |
| 00:25–01:05 | **Investigasi → Foto**: potret kertas cetak secara miring, unggah, klik *Analisis bukti* | **TARGET TERIDENTIFIKASI**: Hendro, NRP, satuan. Baris Lapis 1/2/3 ditandai TERBACA, beserta foto yang sudah diluruskan |
| 01:05–01:25 | **Tab Teks**: tempel `demo_ketik_ulang.txt`, klik *Analisis* | TERIDENTIFIKASI; Lapis 2 TERBACA; kemiripan dengan naskah resmi tinggi |
| 01:25–01:45 | Ganti dengan `demo_parafrase.txt`, klik *Analisis* | TERIDENTIFIKASI; Lapis 2 KURANG, **Lapis 3 TERBACA**; 2 token TERKONFIRMASI |
| 01:45–02:05 | **Tab Data dump**: unggah `dump_hoaks_daur_ulang.csv` | **HOAKS: DAUR ULANG**, dengan nama korpus data publik |
| 02:05–02:30 | Unggah `dump_bocor_forum.csv` | **KEBOCORAN ASLI**: Ekspor #N oleh akun pengekspor, waktu, dan keperluan |
| 02:30–03:00 | **Audit Trail** → verifikasi rantai | **RANTAI VALID**; semua langkah tadi tercatat |

**Selagi foto dianalisis (10–30 detik)**, isi waktunya dengan narasi: "SIDIK sedang meluruskan halaman,
membaca pilihan kata, angka fiktif, dan pergeseran spasi setengah poin di setiap kata, tanpa OCR…"

## C. Demo Cadangan untuk Tanya-Jawab

| Pertanyaan juri | Demo singkat |
| :--- | :--- |
| "Bagaimana kalau dua orang berkolusi?" | Tempel `demo_kolusi.txt`. Hasilnya **INDIKASI KOLUSI**, menampilkan kedua salinan, dan penerima ketiga tidak muncul |
| "Bisa salah tuduh?" | Tempel satu kalimat pendek atau teks bebas. Hasilnya **BUKTI TIDAK CUKUP** dan penolakannya tercatat. Unggah `dump_hoaks_rekaan.csv`: **HOAKS: DATA REKAAN** |
| "Admin bisa menyalahgunakan?" | Admin yang mengajukan salinan RAHASIA lalu mencoba menyetujuinya sendiri akan ditolak ("four-eyes"). Ledger juga tidak bisa diubah (lihat demo manipulasi di bawah) |
| "Kalau fotonya cuma separuh?" | Unggah foto setengah halaman salinan Hendro: tetap teridentifikasi |
| "Format naskah dinas?" | Tunjukkan PDF: rata kanan-kiri, tanpa watermark kasat mata |
| "Data dari ekspor bisa dilacak?" | Tunjukkan **Data Personel → Riwayat ekspor**, yang cocok dengan hasil dump tadi |

### Demo manipulasi ledger (untuk juri teknis, database lokal saja)
```bash
docker compose exec db psql -U sidik -d sidik -c "ALTER TABLE ledger_entries DISABLE TRIGGER USER; UPDATE ledger_entries SET body = replace(body, 'COPY_ISSUED', 'X') WHERE seq = 1; ALTER TABLE ledger_entries ENABLE TRIGGER USER;"
```
Muat ulang **Audit Trail**: hasilnya **RANTAI RUSAK**, "Entri #1: isi entri telah diubah". Kembalikan
dengan `replace(body, 'X', 'COPY_ISSUED')`. **Jangan jalankan di database bersama tim.**

### Demo pembatasan peran
Masuk sebagai `distributor` lalu buka `/audit`: halaman menampilkan **Akses ditolak** dan API menjawab `403`.

## D. Rencana Kalau Ada yang Gagal

| Masalah | Tindakan |
| :--- | :--- |
| Foto live tidak terbaca | Unggah foto cadangan yang sudah berhasil (A.4). Jelaskan bahwa sistem memilih menolak daripada menebak |
| Tidak ada internet (database Neon tak terjangkau) | Pakai database lokal: kosongkan `SIDIK_SHARED_DATABASE_URL` di `.env`, lalu `docker compose up -d`, dan ulangi persiapan A.2–A.6 di laptop demo. **Lakukan versi lokal ini H-1 sebagai cadangan.** |
| Laptop bermasalah | Laptop kedua yang sudah disiapkan, atau rekaman video demo |
| Analisis lambat | Normal 10–30 detik. Teruskan narasi; jangan klik ulang |

## E. Batasan yang Dijelaskan Jujur

- Atribusi menunjuk **salinan yang bocor**, bukan putusan bersalah.
- **Kutipan sangat pendek** tanpa angka token tidak bisa diatribusi (batas matematis: satu kalimat
  hanya sekitar 4 bit). Sistem menolak menebak.
- **Foto 2–3 baris** atau foto yang sangat buram ditolak. Setengah halaman masih terbaca.
- **Kolusi** paling andal untuk 2–3 orang. Bila semua angka dibuang, honey-token hilang. Tardos menjadi roadmap.
- **Kamus varian kata** di naskah demo belum disahkan ahli Jukminu; format resmi lengkap (kop, tembusan,
  lampiran) butuh template dari pihak TNI.
- **Lapis 4** memakai data personel demo pengganti SISFO. Alarm otomatis (nomor perangkap dihubungi)
  dan radar OSINT masih roadmap.
- **Kunci ledger** berupa berkas terproteksi; HSM masih roadmap.
