# Panduan demo dashboard

Alur 3 halaman yang sudah jalan end-to-end. Buka http://localhost:3000 setelah `docker compose up --build`.

## Persiapan

```bash
docker compose up --build        # db + api (migrasi otomatis) + web
```

Isi kolom **Petugas** di kanan atas navigasi (mis. "Kolonel Wibowo (Pussiberad)"). Namanya dikirim sebagai `X-Actor` dan tercatat di buku besar sebagai pelaku setiap tindakan. Disimpan di browser, bukan di server.

## Alur demo

1. **Distribusi** (`/distribusi`)
   1. Daftarkan penerima (NRP, nama, pangkat, jabatan, satuan).
   2. Daftarkan naskah (nomor, judul, klasifikasi).
   3. Pilih naskah + penerima, klik **Terbitkan**. Muncul ID salinan, nomor entri ledger, dan teks naskah bertanda (salin atau unduh .txt). Terbitkan untuk beberapa penerima: teksnya berbeda-beda.
2. **Investigasi** (`/investigasi`)
   1. Di kartu *Simulasi kebocoran*: pilih salinan yang "bocor", atur bagian teks yang disalin (slider), centang huruf kapital / salah ketik, klik **Buat teks bocor simulasi**.
   2. Klik **Analisis bukti**. Hasil: nama, pangkat, NRP, jabatan, satuan penerima, naskah, waktu terbit, plus ledger yang mencatat analisis.
   3. Coba slider rendah (±30%) atau teks bebas: hasilnya **BUKTI TIDAK CUKUP** (sistem menolak menebak), dan penolakan itu juga tercatat.
3. **Audit Trail** (`/audit`)
   - **RANTAI VALID** bila tak ada catatan yang diubah. Klik entri untuk melihat hash, tanda tangan Ed25519, dan isi JSON.
   - Salin **jangkar** (hash ujung rantai) ke berita acara. Pemotongan entri terakhir hanya terdeteksi dengan membandingkan jangkar.

## Demo manipulasi (opsional, untuk juri teknis)

Pemilik database dapat melepas trigger append-only, mengubah satu catatan, lalu memasangnya kembali. Rantai tetap menangkapnya:

```bash
docker compose exec db psql -U sidik -d sidik -c "ALTER TABLE ledger_entries DISABLE TRIGGER USER; UPDATE ledger_entries SET body = replace(body, 'COPY_ISSUED', 'X') WHERE seq = 1; ALTER TABLE ledger_entries ENABLE TRIGGER USER;"
```

Muat ulang `/audit`: **RANTAI RUSAK**, "Entri #1: isi entri telah diubah". Kembalikan dengan `replace(body, 'X', 'COPY_ISSUED')` (jalankan hanya pada data demo).

## Batasan yang perlu dijelaskan jujur

- Tanpa autentikasi/RBAC: semua halaman dan endpoint terbuka. Tombol simulasi memakai `GET /copies/{id}/text`, yang seharusnya hanya admin.
- Atribusi menunjukkan **salinan yang diterbitkan**, bukan putusan bersalah.
- Hanya bukti teks (Lapis 2). Foto (Lapis 1) belum tersambung ke registri/dashboard.
- Kamus Lapis 2 sementara (belum divalidasi Perkasad); naskah demo ≈ 60% teks dibutuhkan untuk identifikasi.
- Tidak ada halaman "Verifikasi Klaim" (AI anti-psywar) karena modulnya belum dibangun.
