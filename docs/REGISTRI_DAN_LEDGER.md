# Registri salinan dan buku besar audit

Kode: `backend/app/db/`, `backend/app/core/audit_ledger.py`, `backend/app/api/{registry,intake,ledger}.py`, migrasi `backend/alembic/`.

## Alur

```
POST /api/v1/recipients                    daftar penerima (NRP unik)
POST /api/v1/documents                     daftar naskah (nomor unik, klasifikasi)
POST /api/v1/documents/{id}/copies         terbitkan salinan bertanda untuk satu penerima
                                           -> copy_id acak 32 bit + teks Lapis 2 + catat ledger
POST /api/v1/intake/text                   analisis teks bukti -> petakan ke salinan -> catat ledger
GET  /api/v1/ledger                        daftar entri
GET  /api/v1/ledger/verify                 verifikasi seluruh rantai
```

Header opsional `X-Actor` mencatat siapa yang bertindak (default `anonim`). **Belum ada autentikasi/RBAC**: semua endpoint terbuka (purwarupa). Itu harus ada sebelum dipakai di luar demo.

## Pagar anti salah-tuduh (berlapis)

1. Dekoder menolak bukti rusak berat (sisa 2 simbol paritas Reed-Solomon untuk deteksi).
2. `copy_id` hasil dekode **wajib terdaftar**. Payload yang terbaca tetapi tak terdaftar menghasilkan `UNREGISTERED` tanpa atribusi.
3. Respons selalu menyatakan bahwa atribusi menunjukkan salinan yang diterbitkan, bukan putusan bersalah.

`copy_id` dibuat acak (`secrets.randbits(32)`), bukan berurutan, sehingga tak bisa ditebak dari ID penerima lain.

## Buku besar (hash chain + tanda tangan)

`entry_hash(n) = SHA-256(entry_hash(n-1) || body(n))`, lalu ditandatangani **Ed25519**. `body` adalah JSON kanonik (event, actor, waktu UTC, data). Peristiwa yang dicatat: `COPY_ISSUED`, `LEAK_INTAKE_TEXT` (termasuk yang ditolak). Untuk intake hanya **hash SHA-256 bukti** yang disimpan, bukan teksnya.

`/ledger/verify` memeriksa urutan, keterkaitan hash, isi, dan tanda tangan; berhenti di entri pertama yang bermasalah.

| Serangan | Terdeteksi? |
| :--- | :---: |
| Ubah isi entri | ya (hash) |
| Hapus entri tengah / sisipkan | ya (nomor urut, prev_hash) |
| Ubah isi lalu hitung ulang semua hash | ya (tanda tangan tidak valid tanpa kunci) |
| Tanda tangan dengan kunci lain | ya |
| **Potong ekor rantai** | **tidak** tanpa jangkar eksternal |

Karena itu `verify` mengembalikan `head_seq` dan `head_hash`: catat/cetak secara berkala di luar sistem (mis. dalam berita acara) sebagai jangkar.

Di PostgreSQL ada lapisan tambahan: trigger menolak `UPDATE`, `DELETE`, dan `TRUNCATE` pada `ledger_entries`. Pemilik database masih bisa melepas trigger, jadi hash chain tetap menjadi jaminan utamanya.

## Temuan saat pengujian (sudah diperbaiki)

Pada uji 30 penulis paralel di PostgreSQL, **23 dari 30 gagal** dan nomor urut berlubang: (a) `SELECT ... FOR UPDATE` pada baris terakhir tidak mencegah dua transaksi membaca ujung rantai yang sama, dan (b) sequence database terbakar saat transaksi dibatalkan, sehingga tampak sebagai entri hilang. Perbaikan: penulis diserialkan dengan `pg_advisory_xact_lock`, dan nomor urut ditentukan aplikasi (`last.seq + 1`) di dalam lock. Setelah itu 30/30 berhasil dan rantai valid. Uji ini ada sebagai `tests/test_postgres_integration.py`.

## Menjalankan

```bash
docker compose up --build          # api menjalankan "alembic upgrade head" otomatis
```

Kunci penandatangan dibuat otomatis pada pemakaian pertama di `data/keys/ledger_ed25519.pem` (diabaikan git; di Docker `/data/keys/...`). **Cadangkan kunci ini** dan jangan di-commit: kehilangannya membuat rantai lama tak terverifikasi. Kunci berupa berkas PEM tanpa kata sandi (purwarupa); HSM/TPM adalah roadmap.

Migrasi manual dan uji integrasi PostgreSQL:

```bash
cd backend
alembic upgrade head                       # memakai SIDIK_DATABASE_URL
SIDIK_TEST_POSTGRES_URL=postgresql+psycopg://sidik:sidik@localhost:55432/sidik pytest tests/test_postgres_integration.py
```

(Tanpa `SIDIK_TEST_POSTGRES_URL`, kedua test integrasi dilewati. CI menjalankannya dengan layanan PostgreSQL.)

Catatan lingkungan: bila komputer sudah menjalankan PostgreSQL lain di port 5432, koneksi dari host ke container bisa terjawab oleh server yang salah ("role sidik does not exist"). Pakai port lain untuk container uji.

## Belum ada

- Autentikasi dan RBAC (distributor / investigator / admin).
- Intake foto (Lapis 1) ke registri dan penggabungan bukti Lapis 1+2.
- Bentuk PDF dari naskah Lapis 2 (saat ini Lapis 1 dan Lapis 2 memakai template terpisah).
- Jangkar eksternal otomatis untuk `head_hash`.
