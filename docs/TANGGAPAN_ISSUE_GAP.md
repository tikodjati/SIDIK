# Tanggapan Issue / Gap dari Ketua Tim

Status: ✅ diperbaiki · 🧪 diuji (tidak perlu perbaikan) · ⚠️ batasan (dengan alasan) · 📝 klaim issue sudah tidak berlaku.
Semua angka berasal dari tes otomatis dan simulasi foto, bukan foto HP sungguhan, kecuali yang
disebutkan lain.

| # | Issue | Status | Ringkas |
| :-: | :--- | :-: | :--- |
| 1 | Format naskah dinas: cap basah, tanda tangan, kop, tembusan | 🧪 + ⚠️ | Cap dan tanda tangan sudah diuji dan tetap terbaca. Format resmi lengkap butuh template dari pihak TNI |
| 2 | Kutipan 1–2 kalimat tidak teratribusi | ⚠️ (sebagian tertolong Lapis 3) | Batas teori informasi. Kalimat yang memuat angka token tetap bisa terlacak |
| 3 | Portal mandiri, belum terintegrasi SISFO | ⚠️ | API REST (OpenAPI) sudah menjadi titik integrasi; konektor butuh akses ke SISFO |
| 4 | Lapis 3 dan 4 "tidak diimplementasikan" | 📝 | Sudah ada di commit `aa5b999` (Lapis 3) dan `c81fdd4` (Lapis 4). Tardos sengaja tidak dipakai |
| 5 | Bukan *blind watermarking* (butuh template) | ⚠️ | Pilihan desain demi ketahanan terhadap foto |
| 6 | Hanya rata kiri, naskah dinas rata kanan-kiri | ✅ | **Sebelumnya BELUM diperbaiki** (klaim "sudah di-fix" keliru). Sekarang sudah |
| 7 | Foto close-up tanpa 4 sudut halaman | ✅ (sejak `43b627e`, `490f3ee`) + ⚠️ | Setengah halaman terbaca. 2–3 baris saja memang tidak cukup bit |
| 8 | Kertas terlipat (non-planar) | 🧪 | Lipat 4 sampai lekuk 20 px tetap terbaca dalam simulasi |
| 9 | AI Claim Verifier tidak ada | ✅ (deterministik) | Verifikasi dump (Lapis 4) dan kemiripan dokumen dengan naskah resmi. Model AI tidak dipakai |
| 10 | Foto membebani CPU, unggahan bersamaan antre | ✅ | 2 worker API. Route foto memang sudah tidak memblokir server |
| 11 | Kunci Ed25519 berupa file di disk | ⚠️ (roadmap HSM) | Sudah `chmod 600` dan terpisah dari DB; HSM butuh perangkat keras |
| 12 | Tidak ada generator synset otomatis | ⚠️ | Sengaja tidak dibuat: varian kata harus disahkan ahli Jukminu |
| 13 | Admin berkuasa mutlak, belum *four-eyes* | ⚠️ (bisa dibangun) | Ledger tetap tidak bisa diubah admin. Alur persetujuan ganda bisa ditambahkan bila tim setuju |

## Rincian

### 1. Cap dinas dan tanda tangan (🧪)
Simulasi dilakukan pada 3 foto per kasus: cap bulat dan tanda tangan menimpa beberapa baris teks
badan, lalu foto dibuat miring 20° dengan blur dan JPEG.

| Kasus | Teridentifikasi | Salah | Token terbaca |
| :--- | :-: | :-: | :-: |
| Cap dinas | 3/3 | 0 | 16/18 |
| Tanda tangan | 3/3 | 0 | 17/18 |
| Cap + tanda tangan | 3/3 | 0 | 17/18 |

Kata yang tertutup hanya menjadi *erasure*, dan Reed-Solomon beserta pengulangan bit menutupinya.

Kop surat, tembusan, dan lampiran tabel adalah soal **template**. Template bisa diubah tanpa
mengubah mesin, tapi format resminya harus berasal dari pihak TNI. Sebagai tim eksternal, kita
tidak memiliki naskah aslinya.

### 2. Kutipan sangat pendek (⚠️)
Satu kalimat hanya membawa sekitar 4 bit, padahal untuk membedakan 200 penerima saja butuh minimal
8 bit. Ini **batas matematis**, bukan bug.

Sejak Lapis 3, kalimat yang memuat angka fakta (frekuensi, nomor registrasi, koordinat) membawa
honey-token. Satu token ditampilkan sebagai **indikasi**, dan dua token sudah **teridentifikasi**.
Sistem sengaja menolak menebak demi nol salah tuduh.

### 3. Integrasi SISFO (⚠️)
Semua fungsi sudah tersedia sebagai **REST API terdokumentasi** (`docs/openapi.json`): terbitkan
salinan, unduh PDF, intake bukti, dan ekspor data. Pipeline cetak SISFO cukup memanggil API ini.
Konektor khusus memang tidak bisa dibuat tanpa akses ke sistem TNI, dan aturan hackathon tidak
mengizinkannya.

### 4. Lapis 3 dan 4 (📝)
Klaim ini **sudah tidak berlaku**.
- **Lapis 3**: 6 honey-token per salinan dengan deteksi dari teks maupun foto, serta status kolusi
  (`docs/HASIL_LAPIS3.md`).
- **Lapis 4**: honey-record per ekspor dan pemeriksa dump (`docs/HASIL_LAPIS4.md`).
- **Tardos sengaja tidak dipakai**: butuh sekitar 230 bit untuk 2 pelaku dan sekitar 2.500 bit untuk
  5 pelaku, sedangkan kapasitas naskah satu halaman hanya sekitar 270 bit dan sudah dipakai
  Reed-Solomon. Penggantinya adalah honey-token unik ber-alfabet besar. Klaim di proposal perlu
  direvisi.

### 5. Bukan blind watermarking (⚠️)
Template justru menjadi sumber ketahanan terhadap foto miring, buram, dan terpotong: dekoder tahu
persis di mana setiap kata seharusnya berada. Watermark tanpa template untuk PDF bebas jauh lebih
rapuh terhadap foto. Ini *roadmap*, tidak bisa dikerjakan dalam lingkup hackathon.

### 6. Rata kanan-kiri (✅)
Sebelumnya **belum diperbaiki**. Engineer sempat menjelaskan bahwa ini bukan celah keamanan (format
ditentukan sistem), tapi kodenya belum diubah. Sekarang:
- Baris yang dipatahkan menjadi rata kanan-kiri; baris akhir paragraf dan judul tetap rata kiri,
  sesuai kaidah perataan.
- Modulasi ±δ ditambahkan di atas spasi yang sudah dilebarkan. Dekoder membaca selisih kata
  terhadap rata-rata tetangganya, sehingga pelebaran yang merata saling meniadakan.
- Hasil regresi setelah perubahan ini: semua uji crop lolos, token terbaca 41/48 dengan 0 salah,
  dan semua tes lulus.

Di naskah demo hanya 3 dari 56 baris yang terpengaruh, karena kebanyakan butir cukup satu baris.

### 7. Foto close-up (✅ + ⚠️)
Sudah diperbaiki sebelumnya: blok teks dicari tanpa membutuhkan 4 sudut halaman, dan perspektif
dikoreksi dari geometri baris. Hasilnya, setengah halaman atau 70% halaman tetap terbaca, termasuk
foto PDF di layar laptop yang sebagian tertutup taskbar.

2–3 baris tetap tidak cukup: hanya sekitar 8 bit, padahal minimal sekitar 56 bit dibutuhkan. Sistem
menolak tanpa crash.

### 8. Lipatan kertas (🧪)
Simulasi lipat empat dengan lekuk di tengah horizontal dan vertikal, baris melengkung, dan bayangan
di lekukan:

| Lekuk | Teridentifikasi | Salah |
| :--- | :-: | :-: |
| 4 px | 3/3 | 0 |
| 10 px | 3/3 | 0 |
| 20 px | 3/3 | 0 |

Ini terbantu oleh pelacakan baris satu per satu dan registrasi horizontal per baris. Lipatan yang
lebih ekstrem (kertas diremas) belum diuji.

### 9. Pemeriksa klaim (✅, deterministik)
- **Data dump**: honey-record, kecocokan dengan data personel, korpus data publik lama, dan validasi
  format NIK. Ada di halaman *Investigasi → Data dump*.
- **Dokumen teks**: hasil intake teks sekarang menampilkan **kemiripan dengan naskah resmi**, yaitu
  porsi pasangan kata yang sama.

| Teks | Kemiripan |
| :--- | :-: |
| Salinan naskah | 94–97% |
| Diketik ulang dengan typo | 72% |
| Parafrase | 12% |
| Dokumen rekaan berkosakata militer | 0% |

*Sentence-Transformers* sengaja tidak dipakai, sesuai keputusan arsitektur: hasil deterministik bisa
dibela di persidangan, tidak butuh model 90 MB, dan tetap berjalan tanpa internet.

### 10. Beban CPU (✅)
Route foto sudah memakai `def` biasa, sehingga FastAPI menjalankannya di thread pool. Server tidak
"macet": endpoint lain tetap melayani.

Masalahnya, hanya ada 1 proses, sehingga dua analisis foto berebut CPU. Sekarang container API
menjalankan **2 worker** (`SIDIK_WORKERS`, bisa dinaikkan sesuai jumlah core). Kunci ledger disiapkan
sekali sebelum worker dijalankan, supaya tidak ada dua worker yang membuat kunci berbeda. Penulisan
ledger tetap aman karena memakai advisory lock PostgreSQL.

Analisis per foto memang 10–30 detik. Itu harga ketelitian (banyak kandidat pelurusan); antrean
kerja di latar belakang dicatat sebagai roadmap.

### 11. Kunci di disk (⚠️, sesuai keputusan tim: pending)
File kunci sudah `chmod 600`, tidak ikut git, dan terpisah dari basis data. Proposal sendiri
(Inovasi 5) menempatkan HSM/TPM sebagai roadmap. HSM butuh perangkat keras dan tidak bisa
disimulasikan dengan jujur di hackathon.

### 12. Generator synset otomatis (⚠️)
Varian kata dalam naskah dinas harus **sah menurut Jukminu**. Generator otomatis berisiko
menghasilkan kata yang tidak baku dan merusak naskah resmi. Yang sudah ada adalah **validator
otomatis**: keunikan varian, kemiripan antar-kata, kapasitas bit, dan kemuatan satu halaman semuanya
diperiksa saat template dimuat. Ahli Jukminu cukup menulis template, dan mesin menolak template yang
tidak valid.

### 13. Four-eyes principle (⚠️)
Admin tidak bisa memalsukan jejak. Ledger bersifat *append-only* (dijaga trigger basis data),
ditandatangani, dan berantai hash, sehingga perubahan apa pun terdeteksi di halaman Audit. Yang
belum ada adalah **alur persetujuan ganda**, misalnya penerbitan salinan RAHASIA yang harus disetujui
akun kedua. Fitur ini **bisa dibangun** (sekitar 1–2 jam) kalau tim menganggapnya penting untuk demo.
