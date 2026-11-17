# Hasil Lapis 4: Honey-Record & Pemeriksa Klaim Dump

## Cara kerja

1. **Data personel demo** (pengganti SISFO) ada di tabel `personnel`: sekitar 400 persona rekaan
   dengan format realistis (NIK 16 digit berstruktur, HP seluler, NRP).
   - Sekitar 2% isinya **honey-record tertanam** yang tidak bisa dibedakan dari baris lain.
   - Katalognya hanya ada di tabel terpisah `honey_records`.
2. **Ekspor data** (halaman *Data Personel*, peran admin/distributor):
   - Setiap ekspor CSV mendapat honey-record **unik untuk ekspor itu**, kira-kira 1 per 50 baris dan
     minimal 3, yang diselipkan di posisi acak.
   - Ekspor dicatat di ledger: akun, waktu, satuan, dan keperluan.
3. **Pemeriksa dump** (halaman *Investigasi*, tab *Data dump*):
   - Menerima berkas CSV, SQL, JSON, atau teks.
   - NIK, nomor HP (`08…`, `+62…`, `62…`, boleh bertanda pisah atau spasi), dan NRP diambil dari berkas.
   - Identitas lalu dicocokkan secara berurutan seperti di bawah.

| Urutan | Pemeriksaan | Status |
| :---: | :--- | :--- |
| 1 | Honey-record terbukti ada | **KEBOCORAN ASLI**, menunjuk ekspor (akun/waktu) atau "DB langsung" |
| 2 | ≥ 50% identitas cocok dengan data personel kita | **COCOK, SUMBER TAK TERLACAK** |
| 3 | ≥ 50% identitas ada di korpus data publik lama | **HOAKS: DAUR ULANG** (beserta nama korpus) |
| 4 | ≥ 30% NIK berformat tidak valid | **HOAKS: DATA REKAAN** |
| 5 | Selain itu | **BUKAN DATA KITA** |

**Nol salah tuduh**: satu sumber baru dinyatakan terbukti bila ≥ 2 baris honey-record-nya cocok,
atau 1 baris cocok di ≥ 2 kolom (NIK + HP, dan sebagainya). Satu nilai saja hanya **indikasi**,
karena NIK rekaan bisa saja kebetulan sama dengan NIK orang sungguhan.

**Privasi korpus publik**: yang disimpan hanya hash SHA-256 dari NIK dan HP, bukan isi berkasnya.

## Hasil uji (otomatis, `backend/tests/test_layer4.py`, 14 tes)

| Kasus | Hasil |
| :--- | :--- |
| Ekspor bocor utuh | Terlacak ke ekspor itu, beserta akun pengekspornya |
| Potongan berisi 2 honey-record dan 20 baris biasa | Terlacak |
| Satu NIK honey-record saja | Hanya indikasi |
| Gabungan dua ekspor | Keduanya terlacak |
| Dump langsung tabel personel (SQL `INSERT`, HP format `+62`) | Terlacak ke "DB langsung" |
| Data publik lama berkop militer | DAUR ULANG; korpus terbukti hanya menyimpan hash |
| NIK acak | REKAAN |
| NIK valid tapi bukan milik kita | BUKAN DATA KITA |
| Berkas tanpa identitas | TIDAK ADA IDENTITAS |
| Peran | Investigator tidak bisa mengekspor; distributor tidak bisa memeriksa dump |

Migrasi `0004` dan alur seed → ekspor → analisis juga sudah diuji di PostgreSQL 16.

## Cara menguji di dashboard

1. **Siapkan data.** Rebuild dengan `docker compose up --build -d api web` (migrasi berjalan otomatis).
   Admin lalu membuka **Data Personel** dan menekan **Isi data demo** (sekali saja per basis data).
2. **Siapkan sampel hoaks.** Jalankan `docker compose exec api python -m scripts.personnel hoax-samples`.
   Perintah ini mendaftarkan korpus "Data publik lama 2021 (DEMO)" dan menulis dua berkas di
   `data/test_leaks/`: `dump_hoaks_daur_ulang.csv` dan `dump_hoaks_rekaan.csv`.
3. **Uji kebocoran asli.** Ekspor CSV sebuah satuan dengan keperluan apa saja, lalu unggah berkas itu
   di **Investigasi → Data dump**. Hasilnya **KEBOCORAN ASLI**, beserta nomor ekspor, akun, dan waktunya.
4. **Uji potongan.** Hapus sebagian besar baris CSV, lalu unggah ulang. Dump tetap terlacak selama
   ada ≥ 2 honey-record yang tersisa. Karena posisinya acak, potongan yang sangat kecil bisa jadi
   hanya terbaca sebagai indikasi.
5. **Uji hoaks.** Unggah kedua berkas sampel hoaks. Hasilnya **DAUR ULANG** dan **REKAAN**.
6. **Cek jejak.** Buka **Audit Trail**: ekspor dan pemeriksaan dump tercatat.

## Dibanding proposal

| Klaim proposal | Kondisi |
| :--- | :--- |
| Persona sintetis realistis (NRP, nama, NIK, HP perangkap, satuan) | ✅ Format realistis, rekaan |
| Mengarahkan investigasi ke akun yang mengakses saat bocor | ✅ Lewat honey-record per ekspor; akses langsung ditandai "DB langsung" |
| Sentinel Query Matcher (cocokkan dump dengan katalog) | ✅ |
| Live Test 3: dump hoaks daur ulang data publik | ✅ Lewat korpus data publik yang didaftarkan |
| *Digital Sentinel Trigger*: alarm otomatis | ⚠️ Belum ada alarm: deteksi baru terjadi saat dump diunggah. Alarm saat nomor perangkap dihubungi butuh SIM/infrastruktur sungguhan |
| AI *Sentence-Transformers* (kemiripan semantik) | ⚠️ Tidak dipakai: verifier deterministik, sesuai keputusan arsitektur |
| "Tingkat Kepalsuan 99.4%" | ⚠️ Diganti porsi terukur: cocok dengan data kita / korpus / NIK tidak valid |
| SISFO TNI AD sungguhan (PostgreSQL/Oracle) | ⚠️ Data demo; di produksi butuh konektor ke SISFO |
| OSINT Dark-Web Radar (Inovasi 4) | ⏳ Roadmap: bukti masih diunggah manual |

## Batasan

1. **Dump yang sangat kecil** (di bawah sekitar 50 baris) bisa tidak memuat 2 honey-record, sehingga
   hanya terbaca sebagai indikasi atau "cocok, sumber tak terlacak".
2. **Pembobol bisa menyaring** baris yang tampak aneh. Persona dibuat berformat sama dengan data asli
   supaya sulit disaring, tetapi ini tidak dijamin.
3. **Deteksi daur ulang hanya sekuat korpusnya.** Data publik lama harus didaftarkan lebih dulu.
4. **NIK rekaan bisa kebetulan sama** dengan NIK orang sungguhan. Karena itu satu nilai saja tidak
   pernah dijadikan bukti.
