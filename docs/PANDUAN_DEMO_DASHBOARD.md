# Panduan demo dashboard

Alur 3 halaman yang sudah jalan end-to-end. Buka http://localhost:3000 setelah `docker compose up --build`.

## Persiapan

```bash
docker compose up --build        # db + api (migrasi otomatis) + web
```

Buat akun demo sekali saja (sandi acak tersimpan di `data/keys/demo_users.txt`, diabaikan git):

```bash
docker compose exec api python -m scripts.users seed-demo
```

Akun: `admin`, `distributor`, `investigator`. Detail peran ada di `docs/AUTENTIKASI_RBAC.md`.

## Alur demo

1. **Distribusi** (`/distribusi`, masuk sebagai `distributor`)
   1. Daftarkan penerima (NRP, nama, pangkat, jabatan, satuan).
   2. Daftarkan naskah (nomor, judul, klasifikasi).
   3. Pilih naskah + penerima, klik **Terbitkan**. Muncul ID salinan, nomor entri ledger, dan teks naskah bertanda (salin atau unduh .txt). Terbitkan untuk beberapa penerima: teksnya berbeda-beda.
   4. Klik **Unduh PDF (cetak)** (atau tombol **PDF** di tabel) lalu cetak A4. Tiap unduhan tercatat di ledger (`COPY_EXPORTED`).
2. **Investigasi** (`/investigasi`, masuk sebagai `investigator`)
   - **Tab Foto / scan:** potret kertas cetak (boleh miring, terputar, diperkecil saat cetak; seluruh halaman sebaiknya terlihat), unggah, klik **Analisis bukti**. Hasil muncul dalam ±10–15 detik beserta gambar halaman yang sudah diluruskan; foto yang ditolak butuh ±20 detik. Di HP, tombol unggah langsung membuka kamera.
   - **Tab Teks / ketik ulang:**
   1. Tempel potongan teks dari langkah 1. Alternatif untuk demo cepat: masuk sebagai `admin`, lalu pakai kartu *Simulasi kebocoran* (pilih salinan, atur bagian teks, huruf kapital / salah ketik, klik **Buat teks bocor simulasi**). Kartu itu hanya muncul untuk admin.
   2. Klik **Analisis bukti**. Hasil: nama, pangkat, NRP, jabatan, satuan penerima, naskah, waktu terbit, plus ledger yang mencatat analisis.
   3. Coba slider rendah (±30%) atau teks bebas: hasilnya **BUKTI TIDAK CUKUP** (sistem menolak menebak), dan penolakan itu juga tercatat.
3. **Audit Trail** (`/audit`, `investigator` atau `admin`)
   - Tunjukkan bahwa pelaku tercatat sesuai akun yang login, termasuk percobaan sandi salah.
   - **RANTAI VALID** bila tak ada catatan yang diubah. Klik entri untuk melihat hash, tanda tangan Ed25519, dan isi JSON.
   - Salin **jangkar** (hash ujung rantai) ke berita acara. Pemotongan entri terakhir hanya terdeteksi dengan membandingkan jangkar.

## Demo manipulasi (opsional, untuk juri teknis)

Pemilik database dapat melepas trigger append-only, mengubah satu catatan, lalu memasangnya kembali. Rantai tetap menangkapnya:

```bash
docker compose exec db psql -U sidik -d sidik -c "ALTER TABLE ledger_entries DISABLE TRIGGER USER; UPDATE ledger_entries SET body = replace(body, 'COPY_ISSUED', 'X') WHERE seq = 1; ALTER TABLE ledger_entries ENABLE TRIGGER USER;"
```

Muat ulang `/audit`: **RANTAI RUSAK**, "Entri #1: isi entri telah diubah". Kembalikan dengan `replace(body, 'X', 'COPY_ISSUED')` (jalankan hanya pada data demo).

## Demo pembatasan peran (opsional)

Masuk sebagai `distributor`, lalu buka `/audit`: halaman menampilkan **Akses ditolak** dan API menjawab `403`. Menu juga hanya menampilkan yang boleh diakses.

## Batasan yang perlu dijelaskan jujur

- Admin tetap sangat berkuasa walau tercatat di ledger; otorisasi ganda dan HSM masih roadmap.
- Atribusi menunjukkan **salinan yang diterbitkan**, bukan putusan bersalah.
- Foto dan teks masih dua jalur terpisah: PDF cetak membawa Lapis 1 saja, teks digital membawa Lapis 2 saja; bukti keduanya belum digabung. Ketik ulang dari kertas cetak tidak terlacak.
- Foto dari PDF naskah baru diuji dengan foto simulasi; foto asli belum.
- Kamus Lapis 2 sementara (belum divalidasi Perkasad); naskah demo ≈ 60% teks dibutuhkan untuk identifikasi.
- Tidak ada halaman "Verifikasi Klaim" (AI anti-psywar) karena modulnya belum dibangun.
