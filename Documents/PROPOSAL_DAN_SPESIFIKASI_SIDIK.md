# DOKUMEN SPESIFIKASI TEKNIS & PROPOSAL KOMPETISI
## KARTIKA CYBER HACKATHON — PUSSIBERAD & CODEPOLITAN
**Kategori:** Defensive Shield (Penangkalan)  
**Nama Produk:** **SIDIK (Sistem Identifikasi Dokumen dan Investigasi Kebocoran)**  
**Klasifikasi Solusi:** *Military-Grade Multi-Layer Document Forensics, Attribution Deception & Leak Intelligence Platform*  

---

# BAGIAN 1: STRUKTUR DOKUMEN PROPOSAL LENGKAP

### 1.1 Judul dan Ringkasan Eksekutif (Executive Summary)
* **Judul:** SIDIK: Platform Forensik Atribusi Digital & Deception Multi-Lapisan Berbasis Modulasi Spasi Mikro, Semantik Jukminu, Honey-Token Anti-Kolusi, dan Honey-Record untuk Menangkal Kebocoran Dokumen dan Basis Data Strategis TNI AD.
* **Ringkasan Eksekutif:**  
  Dalam pertempuran domain siber modern (Fifth Domain Warfare), kebocoran dokumen rahasia militer dan basis data intelijen sering kali tidak dapat dicegah hanya dengan proteksi perimeter (Firewall, EDR, atau Data Loss Prevention/DLP konvensional). Ancaman nyata justru bersumber dari *insider threat* dan kebocoran *air-gap bridge* melalui kanal analog: pemotretan dokumen fisik/layar menggunakan kamera ponsel cerdas (smartphone), penyalinan/pengetikan ulang parsial (retyping), serta kebocoran basis data melalui serangan APT/Infostealer.
  
  **SIDIK (Sistem Identifikasi Dokumen dan Investigasi Kebocoran)** hadir sebagai perisai defensif aktif (*Active Defensive Shield*) yang menyisipkan identifikasi forensik tak kasat mata (*imperceptible & robust forensic marking*) ke dalam setiap dokumen dan data militer sebelum didistribusikan. Dengan mengombinasikan 4 Lapis Perlindungan:
  1. **Lapis 1 (Visual):** *Differential Inter-Word Spacing Modulation* (tahan foto HP miring, foto layar laptop, scan, crop setengah halaman, cap dinas, dan lipatan kertas).
  2. **Lapis 2 (Semantik):** *Variasi Tata Naskah Dinas (Jukminu) + Reed-Solomon Error-Correcting Code* (tahan ketik ulang, salin-tempel, salah ketik, dan kutipan sebagian).
  3. **Lapis 3 (Honey-Token):** *Angka fiktif unik per penerima* (tahan parafrase total, dan mengidentifikasi 2–3 oknum yang berkolusi menggabungkan salinan).
  4. **Lapis 4 (Honey-Record):** *Synthetic Sentinel Database Injection* (menjebak dan mengatribusi kebocoran basis data ke ekspor/akun asalnya).
  
  Dilengkapi dengan **Leak Claim Verifier deterministik** (anti-psywar: membedakan kebocoran asli dari data daur ulang atau rekaan), **persetujuan ganda (four-eyes)** untuk naskah RAHASIA, dan arsitektur **100% Sovereign & Air-Gapped Ready** berlandaskan *Tamper-Proof Audit Trail* (rantai hash SHA-256 bertanda tangan Ed25519). SIDIK mengidentifikasi salinan sumber kebocoran beserta nama, pangkat/NRP, satuan, dan waktu distribusinya dari registri, dengan kebijakan **nol salah tuduh**: bila bukti tidak cukup, sistem menolak menebak. Purwarupa diuji dengan 231 tes otomatis dan foto HP sungguhan (hasil terukur di Bagian 2.7).

---

### 1.2 Latar Belakang Faktual & Analisis Ancaman Nyata
Pengembangan SIDIK didasarkan pada tiga studi kasus kebocoran intelijen dan militer paling destruktif dalam dekade terakhir:

1. **Insiden Kebocoran Data BAIS TNI (2024):**  
   Aktor ancaman anonim (MoonzHaxor) di forum gelap BreachForums dan saluran Telegram mengklaim membocorkan sampel data milik Badan Intelijen Strategis (BAIS) TNI. Insiden ini memperlihatkan dua kelemahan kritis nasional:
   * *Ketiadaan Atribusi Sumber*: Ketidakmampuan melacak siapa personel internal atau akun mana yang salinan datanya pertama kali keluar.
   * *Rentensi Psywar*: Ketidakmampuan memverifikasi secara instan apakah data yang beredar merupakan dokumen baru yang valid, data usang/daur ulang tahun-tahun sebelumnya, atau sekadar disinformasi (psywar) untuk menjatuhkan kredibilitas institusi pertahanan.

2. **Jack Teixeira / Discord Pentagon Leaks (2023):**  
   Seorang prajurit intelijen muda Garda Nasional Udara AS membocorkan ratusan dokumen sangat rahasia (*TOP SECRET*) terkait perang Ukraina dengan cara mencetak dokumen fisik, melipatnya, membawanya pulang, lalu memotretnya di atas meja menggunakan kamera ponsel. Solusi DLP konvensional (Endpoint DLP/Network DLP) lumpuh total karena kebocoran terjadi pada *analog gap*.

3. **Reality Winner / NSA Leak via The Intercept (2017):**  
   Seorang kontraktor NSA membocorkan laporan rahasia operasi siber intelijen militer Rusia. FBI berhasil menangkap Reality Winner dalam hitungan hari karena dokumen yang dipindai dan dipublikasikan media memuat *tracking microdots* (titik kuning mikro tak kasat mata dari printer laser komersial) yang merekam model printer, tanggal, dan waktu cetak. Ini membuktikan secara empiris bahwa penandaan forensik tingkat mikro adalah senjata defensif paling mematikan bagi pembocor rahasia.

---

### 1.3 Matriks Penilaian Proposal (Scoring Rubrics Alignment)

| Kriteria Penilaian | Bobot | Keunggulan Strategis SIDIK |
| :--- | :---: | :--- |
| **Relevansi & Manfaat** | **25%** | Menjawab langsung doktrin pengamanan dokumen rahasia TNI AD (Petunjuk Teknis Pengamanan Sandi & Siber). Mencegah kerugian strategis akibat spionase militer dan kebocoran rencana operasi pertempuran. |
| **Inovasi Teknis** | **25%** | Modulasi spasi diferensial yang dibaca dari foto **tanpa OCR** (registrasi bentuk kata ke template), digabung dengan variasi kata Tata Naskah Dinas + Reed-Solomon dalam **satu dekode terpadu** (bukti dua lapis saling menguatkan, dan menolak bila saling bertentangan), honey-token anti-kolusi, serta honey-record per ekspor. |
| **Fungsionalitas Purwarupa** | **25%** | Purwarupa berjalan *end-to-end*: penerbitan salinan bertanda (PDF), intake foto/teks/dump data, atribusi ke penerima, verifikasi klaim hoaks, persetujuan ganda, dan audit trail yang bisa diverifikasi. 231 tes otomatis lulus. |
| **Kelayakan Implementasi** | **15%** | Arsitektur *Zero-Internet Sovereign Appliance* (Docker, tanpa layanan cloud wajib). Template naskah bisa diganti oleh ahli Jukminu tanpa mengubah kode; validator otomatis menolak template yang tidak aman. Seluruh fungsi tersedia sebagai REST API untuk integrasi ke SISFO. |
| **Dokumentasi & Standar** | **10%** | Spesifikasi teknis modular, kontrak API OpenAPI/Swagger, RBAC tiga peran, rantai bukti (*Chain of Custody*) bertanda tangan digital, serta laporan hasil uji dan batasan yang dicatat apa adanya. |

---

# BAGIAN 2: SPESIFIKASI REKAYASA TEKNIS & ARSITEKTUR SISTEM

### 2.1 Diagram Arsitektur Sistem SIDIK (End-to-End ASCII Diagram)

```
+==================================================================================================+
|                                    SISTEM SIDIK (ARSITEKTUR AIR-GAPPED)                          |
+==================================================================================================+

 [ SISTEM SUMBER / SISFO TNI AD ]
        |
        +-----> [ Dokumen Asli (PDF/DOCX) ] ----+
        |                                       |
        +-----> [ Database Relasional (SQL) ] --|--+
                                                |  |
================================================|==|================================================
 1. MULTI-LAYER MARKING & INGESTION ENGINE      |  |
================================================|==|================================================
                                                v  |
   [ Target Penerima: NRP/Nama/Satuan/Waktu ]      |
                 |                                 |
                 v                                 |
   +---------------------------------------+       |
   | Payload Generator (Reed-Solomon)      |       |
   |   - Versi + flags:   8-bit            |       |
   |   - copy_id acak:   32-bit            |       |
   |   - Paritas RS:     64-bit (nsym=8)   |       |
   |   - Frame: 104-bit (13 byte)          |       |
   +---------------------------------------+       |
                 |                                 |
       +---------+---------+---------+             |
       |                   |         |             |
       v                   v         v             v
 +---------------+ +---------------+ +----------+ +----------------------------------+
 | LAPIS 1       | | LAPIS 2       | | LAPIS 3  | | LAPIS 4: HONEY-RECORD SENTINEL   |
 | Spasi antar-  | | Varian kata   | | Honey-   | | Persona rekaan tertanam di DB    |
 | kata +/-0,5pt | | Jukminu       | | Token    | | + unik per ekspor data           |
 +---------------+ +---------------+ +----------+ +----------------------------------+
       |                   |         |                     |
       +---------+---------+---------+                     |
                 v                                         v
   [ Dokumen Berstempel Forensik ]              [ Database Berpagar Sentinel ]
                 |                                         |
                 +===================+=====================+
                                     |
                       [ JALUR DISTRIBUSI MILITER ]
                                     |
             x x x x x x x KEBOCORAN DOKUMEN / DATA x x x x x x x
             x (Foto HP, Scan Miring, Retyping, Forum Gelap DB) x
                                     |
=====================================v==============================================================
 2. LEAK INTAKE & FORENSIC DECODER ENGINE
====================================================================================================
                                     |
       +-----------------------------+-----------------------------+
       |                             |                             |
       v                             v                             v
 [ KANAL A: CITRA / FOTO ]    [ KANAL B: TEKS / KETIK ]     [ KANAL C: BASIS DATA / FORUM ]
       |                             |                             |
       v                             v                             v
 +-----------------------+    +-----------------------+     +-------------------------------+
 | Vision Preprocessing  |    | Semantic Matcher      |     | Leak Claim Verifier           |
 | - Rectify (tepi/teks/ |    | - Varian kata (fuzzy) |     | - Honey-Record Query Match    |
 |   potongan halaman)   |    | - Angka honey-token   |     | - Cocok data personel kita?   |
 | - Registrasi ECC      |    | - Kemiripan naskah    |     | - Korpus data publik lama     |
 | - Bentuk kata & digit |    |   resmi (bigram)      |     | - Validasi format NIK         |
 +-----------------------+    +-----------------------+     +-------------------------------+
       |                             |                             |
       v                             v                             v
 [ Bit spasi + varian + token ] [ Bit varian + token ]       [ Ekspor / akun sumber, atau   ]
       |                             |                       [ HOAKS: daur ulang / rekaan   ]
       |                             |                             |
       +-----------------------------+-----------------------------+
                                     |
                                     v
                 +---------------------------------------+
                 | FORENSIC ATTRIBUTION ENGINE           |
                 | Reed-Solomon + registri salinan:      |
                 | - Nama: Kolonel Inf XXXXXX            |
                 | - NRP: 110300XXXX                     |
                 | - Jabatan: Asintel Kasdam             |
                 | - Waktu Terbit: 2026-10-30 14:02      |
                 | - Rincian bukti per lapis             |
                 | - Bukti kurang -> MENOLAK MENEBAK     |
                 | - >1 salinan -> INDIKASI KOLUSI       |
                 +---------------------------------------+
                                     |
                                     v
 +-------------------------------------------------------------------------------------------------+
 | 3. TAMPER-PROOF AUDIT TRAIL (CRYPTOGRAPHIC SHA-256 LOG HASH CHAIN)                              |
 | Block N-1 Hash <--- Block N [Evidensi Forensik + Digital Signature + Waktu] <--- Block N+1     |
 +-------------------------------------------------------------------------------------------------+
```

---

### 2.2 Dekonstruksi Mendalam Alur Arsitektur End-to-End (Fase 1 s/d Fase 6)

Diagram arsitektur SIDIK di atas merepresentasikan siklus hidup (*lifecycle*) pengamanan dokumen dan data intelijen militer yang terbagi menjadi 6 Fase Operasional Utama:

```
[FASE 1: Ingestion & Payload] 
            │
            ▼
[FASE 2: Multi-Layer Marking Engine (Lapis 1 - 4)]
            │
            ▼
[FASE 3: Jalur Distribusi Militer & Terjadinya Kebocoran]
            │
            ▼
[FASE 4: Leak Intake & Multi-Channel Preprocessing]
            │
            ▼
[FASE 5: Forensic Decoder & AI Claim Verifier]
            │
            ▼
[FASE 6: Tamper-Proof Audit Trail (Cryptographic Hash Chain)]
```

#### FASE 1: Ingestion & Cryptographic Payload Generation
Tahap ini dieksekusi sesaat sebelum dokumen naskah dinas atau data intelijen didistribusikan dari sistem persuratan resmi (SISFO TNI AD):
1. **Input Data:** Naskah dinas disusun dari **template terstruktur** (teks naskah dengan grup varian kata dan posisi honey-token), beserta metadata registri:
   * Penerima (NRP, nama, pangkat, jabatan, satuan).
   * Nomor naskah dan tingkat kerahasiaan (Biasa s.d. Sangat Rahasia). Naskah RAHASIA/SANGAT RAHASIA wajib disetujui admin kedua sebelum salinannya terbit (*four-eyes principle*).
2. **Penyusunan Payload (Frame 104-bit):**
   $$\text{Frame} = \underbrace{\text{Versi} \parallel \text{Flags}}_{8\text{ bit}} \;\parallel\; \underbrace{\text{copy\_id}}_{32\text{ bit}} \;\parallel\; \underbrace{\text{Paritas Reed-Solomon}}_{64\text{ bit}}$$
   * *copy_id 32-bit acak* (bukan berurutan, tak bisa ditebak) menunjuk satu salinan di registri. **NRP, nama, dan waktu sengaja tidak ditanam di dokumen**: semuanya diambil dari registri, sehingga dokumen yang bocor tidak membocorkan data pribadi penerima.
3. **Penyandian Galois Field $GF(2^8)$:** Paritas Reed-Solomon (8 simbol) mampu memulihkan hingga 4 byte salah atau 8 byte hilang ($2E + S \le 8$). Demi nol salah tuduh, SIDIK hanya menerima hasil dekode bila $2E + S \le 6$; dua simbol paritas disisakan untuk mendeteksi bukti rusak berat yang bisa "dikoreksi" ke identitas yang salah.

#### FASE 2: Multi-Layer Marking Engine (Injeksi Penanda Multi-Lapisan)
Sistem memecah dokumen menjadi empat lapisan pertahanan independen yang bekerja secara komplementer:
1. **Lapis 1 (Visual) — Differential Inter-Word Spacing Modulation:**
   * *Objek Sasaran*: PDF salinan dan cetakannya.
   * *Mekanisme*: `PyMuPDF` merender naskah (rata kanan-kiri seperti naskah dinas) dengan spasi antar-kata yang dimodulasi berpasangan: bit `1` = spasi pertama $+\delta$ dan spasi kedua $-\delta$, bit `0` sebaliknya, dengan $\delta = 0{,}5$ pt. Lebar baris tidak berubah, sehingga margin tetap lurus. Naskah demo membawa **165 slot**, jadi frame 104-bit tertanam lebih dari sekali dan digabung dengan *soft voting*.
   * *Karakteristik Pertahanan*: Dekoder membaca pergeseran **tiap kata terhadap rata-rata dua tetangganya**, sehingga skala cetak, perspektif sisa, dan perataan kanan-kiri saling meniadakan. Pembacaan tidak memakai OCR: setiap kata didaftarkan bentuknya ke render referensi (korelasi silang sub-piksel). *Catatan revisi*: rencana awal ±0,08–0,12 pt dan geser glif vokal ditinggalkan karena hasil spike membuktikan tidak terbaca andal dari foto HP.
2. **Lapis 2 (Semantik) — Variasi Kata Tata Naskah Dinas:**
   * *Objek Sasaran*: Teks naskah dinas.
   * *Mekanisme*: Template naskah memuat grup varian `{a|b}` (1 bit) atau `{a|b|c|d}` (2 bit). Naskah demo memuat **87 grup = 105 bit**. Validator otomatis memastikan setiap varian unik, tidak muncul di teks tetap, dan tidak mirip kata lain (supaya tidak tertukar saat pencocokan *fuzzy*). Pemilik naskah (ahli Jukminu) cukup menulis template tanpa mengubah kode. *Kamus di naskah demo masih padanan leksikal umum dan perlu disahkan ahli Jukminu.*
   * *Karakteristik Pertahanan*: Teks yang disalin dari PDF, diketik ulang, berubah huruf kapital/tanda baca, atau salah ketik tetap terbaca, termasuk potongan yang urutannya berubah. Dari foto, varian kata dibaca dengan pencocokan bentuk, lalu **digabung dengan Lapis 1 dalam satu dekode**. Bila tiap lapis sendiri terbaca tetapi menunjuk salinan berbeda, hasilnya ditolak sebagai bukti bertentangan (tanda manipulasi).
3. **Lapis 3 (Honey-Token) — Angka Fiktif Unik per Penerima:**
   * *Objek Sasaran*: Fakta mikro operasional di naskah: frekuensi (`143.275 MHz`), nomor registrasi alpalhankam (`REG-AL-48271`), kanal komunikasi, nomor prosedur, dan koordinat.
   * *Mekanisme*: Naskah demo memuat 6 token. Digitnya **diacak saat salinan terbit** (5 digit acak per token) dan disimpan di registri dengan aturan unik global. Karena semua digit selebar sama pada font naskah, tata letak tidak berubah dan Lapis 1/2 tidak terganggu. Token dideteksi dari teks (tahan `143.275` vs `143,275`) maupun dari foto (pencocokan bentuk angka 0–9).
   * *Anti-Kolusi*: Bila beberapa oknum menggabungkan salinannya, setiap token yang dipertahankan menunjuk pemiliknya secara pasti, dan sistem melaporkan **INDIKASI KOLUSI** dengan semua salinan yang terlibat. Satu salinan baru teridentifikasi bila ≥ 2 tokennya cocok (atau 1 token yang dikonfirmasi Lapis 1/2); satu token saja hanya indikasi. *Revisi dari rancangan awal*: kode Tardos biner tidak dipakai karena butuh sekitar 230 bit untuk 2 pelaku (dan ribuan bit untuk 5 pelaku), melebihi kapasitas naskah satu halaman yang sudah dipakai Reed-Solomon. Tardos menjadi roadmap untuk naskah multi-halaman.
4. **Lapis 4 (Honey-Record) — Database Sentinel Generator:**
   * *Objek Sasaran*: Basis data personel (di purwarupa: data demo pengganti SISFO).
   * *Mekanisme*: Persona sintetis berformat realistis (NRP, nama, pangkat, satuan, NIK 16 digit berstruktur, nomor HP seluler) **ditanam di tabel personel** (sekitar 1 per 50 baris) tanpa penanda apa pun. **Setiap ekspor data** juga mendapat persona unik yang disisipkan acak, lalu ekspor dicatat di ledger (akun, waktu, satuan, keperluan).
   * *Karakteristik Pertahanan*: Bila dump yang beredar memuat honey-record, sistem menunjuk **ekspor dan akun asalnya**, atau "akses langsung ke basis data" (misalnya SQL injection) bila yang cocok hanya persona tertanam. Satu sumber baru terbukti bila ≥ 2 honey-record cocok (atau 1 yang cocok di ≥ 2 kolom). Di produksi, nomor HP honey-record adalah SIM perangkap milik satuan.

#### FASE 3: Jalur Distribusi Militer & Titik Terjadinya Kebocoran
Dokumen didistribusikan melalui saluran resmi intranet militer, kurir persuratan dinas, atau portal komando. Kebocoran disimulasikan terjadi melalui 3 kanal:
1. **Kanal A (Optik):** Foto miring kamera ponsel dari layar monitor atau kertas fisik, hasil scan kualitas rendah, atau foto yang di-crop.
2. **Kanal B (Tekstual):** Pengetikan ulang sebagian isi dokumen oleh oknum di aplikasi chat terenkripsi (Signal/Telegram).
3. **Kanal C (Basis Data):** Data dump SQL disebarkan di forum bawah tanah (Dark Web / BreachForums).

#### FASE 4: Leak Intake & Multi-Channel Preprocessing Engine
Sistem forensik SIDIK menerima data bukti kebocoran melalui portal investigasi dan mengarahkannya ke pipeline pemrosesan yang sesuai:
1. **Pipeline Kanal Citra / Foto (Kanal A), tanpa OCR:**
   * *Pelurusan multi-kandidat (OpenCV)*: tepi kertas, kotak blok teks, dan **blok naskah rata kiri** (untuk foto potongan atau foto layar yang tertutup taskbar/tab browser). Perspektif kuat (layar laptop condong) dikoreksi dari geometri baris: tepi kiri tiap baris harus lurus di margin dan tiap baris harus horizontal. Semua kandidat dicoba pada 4 rotasi.
   * *Registrasi ECC bertahap* ke render template, dengan *mask* untuk foto potongan, serta perataan pencahayaan untuk menghilangkan bayangan.
   * *Pelacakan baris satu per satu* dan registrasi horizontal per baris (meredam lengkung kertas). Lalu: bentuk kata varian (Lapis 2), bentuk digit honey-token (Lapis 3), dan pergeseran kata (Lapis 1).
2. **Pipeline Kanal Teks / Retyped / Parafrase (Kanal B):**
   * *Pencocokan varian*: teks dinormalisasi (huruf, spasi, tanda baca), lalu tiap varian dicari kemunculannya (*fuzzy* ringan untuk salah ketik). Varian yang ragu dianggap hilang (*erasure*).
   * *Reed-Solomon Erasure-Error Decoding* untuk memulihkan frame dari teks sebagian.
   * *Pencarian honey-token*: semua angka di teks dicocokkan ke registri token.
   * *Kemiripan dengan naskah resmi*: porsi pasangan kata berurutan yang sama dengan naskah resmi, untuk membedakan salinan/ketik ulang dari parafrase berat atau dokumen rekaan.
3. **Pipeline Kanal Basis Data (Kanal C):**
   * *Ekstraksi identitas* dari CSV, SQL `INSERT`, JSON, atau teks: NIK 16 digit, nomor HP (`08…`, `+62…`, bertanda pisah atau spasi), dan NRP.
   * *Sentinel Query Matcher*: pencocokan ke katalog honey-record (per ekspor dan tertanam di DB).

#### FASE 5: Forensic Attribution Engine & AI Claim Verifier
Setelah payload berhasil diekstraksi dari salah satu lapis pertahanan:
1. **Penguncian Atribusi:**
   Frame yang terdekode memberi `copy_id`, yang lalu dicocokkan ke registri salinan: nama, pangkat, NRP, jabatan, satuan, nomor naskah, dan waktu terbit. Alih-alih satu "skor keyakinan", SIDIK menampilkan **rincian bukti per lapis** (berapa bit spasi, bit kata, dan token yang terbaca, serta apakah tiap lapis sendiri cukup) dan menerapkan pagar nol salah tuduh:
   * Dekode Reed-Solomon ditolak bila kerusakan mendekati batas koreksi.
   * `copy_id` wajib terdaftar, dan salinannya wajib benar-benar pernah diedarkan.
   * Lapis 1 dan Lapis 2 yang menunjuk salinan berbeda menghasilkan **BUKTI BERTENTANGAN**, bukan atribusi.
   * Honey-token butuh ≥ 2 kecocokan. Bila ≥ 2 salinan masing-masing cukup bukti, hasilnya **INDIKASI KOLUSI**.
   * Hasil atribusi berbunyi "salinan yang bocor", **bukan putusan bersalah**.
2. **Leak Claim Verifier (Modul Anti-Psywar, deterministik):**
   * *Dump data*: berturut-turut diperiksa honey-record (**KEBOCORAN ASLI** beserta sumbernya), kecocokan dengan data personel kita (**COCOK, SUMBER TAK TERLACAK**), kecocokan dengan korpus data publik lama yang didaftarkan (**HOAKS: DAUR ULANG**), dan porsi NIK berformat tidak valid (**HOAKS: DATA REKAAN**). Korpus publik hanya disimpan sebagai hash SHA-256, bukan data mentah.
   * *Dokumen teks*: kemiripan dengan naskah resmi. Salinan naskah bernilai 94–97%, ketik ulang dengan typo 72%, parafrase 12%, dan dokumen rekaan berkosakata militer 0%.
   * *Revisi dari rancangan awal*: model *Sentence-Transformers* tidak dipakai. Pencocokan deterministik bisa dijelaskan dan dibela di persidangan, tidak butuh model sekitar 90 MB, dan tetap berjalan tanpa internet. Semantic embedding menjadi pendukung opsional di roadmap.

#### FASE 6: Tamper-Proof Audit Trail (Cryptographic Log Hash Chain)
Hasil investigasi dan jejak distribusi dokumen dicatat ke dalam buku besar kriptografi lokal (*Cryptographic Ledger*):
$$\text{Hash}_N = \text{SHA-256}(\text{Hash}_{N-1} \parallel \text{JSON kanonik entri}), \qquad \text{Sig}_N = \text{Ed25519}(\text{Hash}_N)$$
Setiap penerbitan, pengajuan dan persetujuan salinan, unduhan PDF, ekspor data, login, dan pemeriksaan bukti dicatat. Untuk bukti, yang disimpan hanya **hash SHA-256**-nya, bukan isinya. Tabel ledger dijaga *trigger* basis data (*append-only*, UPDATE/DELETE ditolak), dan halaman Audit Trail dapat **memverifikasi seluruh rantai**: perubahan pada satu entri pun terdeteksi. Penulisan dari beberapa server diserialkan dengan *advisory lock* PostgreSQL. Mekanisme ini mendukung pembuktian *Chain of Custody* di Pengadilan Militer. *Kunci penandatangan saat ini berupa berkas terproteksi; HSM/TPM menjadi roadmap (Inovasi 5).*

---

### 2.3 Analisis Gap & Batasan Sistem (System Boundary & Vulnerability Analysis)

Sebagai arsitek keamanan siber, kita wajib memahami batas toleransi fisik dan matematis sistem untuk mengantisipasi pertanyaan mendalam dari dewan juri PUSSIBERAD:

```
+---------------------------------------------------------------------------------------------------+
|                                 MATRIKS IDENTIFIKASI GAP SISTEM SIDIK                             |
+---------------------------------------------------------------------------------------------------+
| GAP / BATASAN SISTEM          | PENYEBAB TEKNIS                   | DAMPAK PADA SISTEM            |
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 1: Foto beresolusi rendah | Digit/kata terlalu kecil (mis.    | Sebagian bit/token tak        |
|        atau buram berat       | sisi foto <= 1600 px), blur berat | terbaca -> dilewati, tak ditebak|
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 2: Kutipan sangat pendek  | 1 kalimat hanya ~4 bit; membeda-  | Lapis 2 tak cukup; Lapis 2    |
|        (< ~50% naskah)        | kan 200 penerima butuh >= 8 bit   | butuh ~50-60% teks naskah     |
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 3: Intentional Entity     | Pembocor membuang semua angka,    | Lapis 3 (Honey-Token)         |
|        Sanitization           | koordinat, dan kode sandi         | kehilangan cantolan fakta     |
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 4: Potongan sangat kecil  | Foto 2-3 baris saja (~8 bit dari  | Ditolak tanpa atribusi;       |
|        (close-up)             | ~56 bit minimum)                  | setengah halaman tetap terbaca|
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 5: Waktu analisis foto    | Banyak kandidat pelurusan dicoba  | 10-30 detik per foto; 2 worker|
|                               | demi ketelitian                   | agar unggahan paralel tak antre|
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 6: Dump data sangat kecil | < ~50 baris mungkin memuat kurang | Hanya "indikasi" / "sumber tak|
|                               | dari 2 honey-record               | terlacak", tanpa tuduhan      |
+-------------------------------+-----------------------------------+-------------------------------+
| GAP 7: Bergantung template    | Dekoder perlu tata letak & kamus  | Belum untuk PDF bebas (blind  |
|                               | naskah yang terdaftar             | watermarking = roadmap)       |
+-------------------------------+-----------------------------------+-------------------------------+
```

#### Mitigasi Doktrinal Terhadap Gap Teridentifikasi:
1. **Prinsip Pertahanan Berlapis (*Defense-in-Depth Fallback*):**
   Lapis 1–3 dibaca bersama dari satu foto, dan bukti Lapis 1 + 2 digabung dalam satu dekode, sehingga foto yang buram untuk salah satu lapis tetap bisa terdekode dari gabungannya. Bila teks diketik ulang, Lapis 1 hilang tetapi Lapis 2 dan 3 tetap ada. Bila teks diparafrase total (Gap 2), honey-token Lapis 3 tetap menunjuk pelaku selama angka faktanya dikutip. Kebocoran basis data ditangani terpisah oleh Lapis 4.
2. **Fail-Safe Thresholding (Anti-False Accusation):**
   Jika kerusakan pada bukti melebihi kapasitas koreksi matematis Reed-Solomon, sistem menolak memberikan tuduhan acak (*zero false-positive policy*) dan mengeluarkan status: *"INSUFFICIENT FORENSIC ARTIFACTS TO PROVE GUILT"*. Hal ini menjaga integritas hukum agar personel tidak dituduh tanpa bukti matematis yang valid.

---

### 2.4 Peluang Inovasi Tambahan (Value-Add Innovation Roadmap)

Untuk memberikan keunggulan kompetitif mutlak pada kriteria **Inovasi Teknis (25%)**, berikut lima inovasi terobosan tingkat lanjut yang dirancang ke dalam roadmap sistem SIDIK:

1. **Inovasi 1: Invisible High-Frequency Spectral Color Modulation (Lapis 1+)**
   * *Konsep*: Mengadopsi prinsip *Yellow Tracking Dots* printer laser ke dalam format digital dokumen PDF.
   * *Mekanisme*: Menyisipkan matriks biner berupa pola titik mikro berwarna kuning sangat lembut (*High-Frequency Yellow Constrained Noise*) pada latar belakang halaman dengan nilai transparansi alfa $< 1.5\%$.
   * *Keunggulan*: Tidak terlihat oleh mata telanjang, namun sensor kamera smartphone modern dengan algoritma *Blue Channel Subtraction* mampu membacanya secara instan, bahkan jika kertas dilipat atau difoto dari sudut ekstrem.
2. **Inovasi 2: Kode Anti-Kolusi Tardos untuk Naskah Multi-Halaman**
   * *Konsep*: Melengkapi honey-token dengan sidik jari biner Tardos yang tersebar di ribuan pilihan kata, sehingga kolusi lebih dari 3 orang tetap terbongkar walau angka fakta dibuang.
   * *Mekanisme*: Slot varian kata tambahan (naskah multi-halaman, sekitar 230 bit untuk 2 pelaku dan ribuan bit untuk 5 pelaku) dipakai untuk kode Tardos, terpisah dari frame Reed-Solomon.
   * *Catatan*: Rancangan awal "jangkar sudut *Zero-Width Space*" dibatalkan karena karakter tak tercetak tidak tertangkap kamera. Masalah yang hendak diatasinya (pelurusan tanpa tepi kertas) **sudah terselesaikan** di purwarupa: blok naskah dicari dari baris-baris rata kiri, dan perspektif dikoreksi dari geometri baris.
3. **Inovasi 3: Kirchenbauer-Inspired Neural Semantic Watermarking untuk AI Drafter**
   * *Konsep*: Mengantisipasi staf administrasi militer yang mulai memanfaatkan AI generatif lokal untuk menyusun naskah dinas.
   * *Mekanisme*: Mengadaptasi algoritma *Kirchenbauer Watermarking* pada model bahasa (LLM) lokal: membagi perbendaharaan kata (*vocabulary*) menjadi daftar hijau (*greenlist*) dan daftar merah (*redlist*) secara pseudo-random berdasarkan kunci rahasia penerima.
   * *Keunggulan*: Setiap naskah dinas yang dibuat dengan bantuan AI secara inheren telah membawa watermark probabilitas kata yang tahan terhadap parafrase skala masif.
4. **Inovasi 4: Automated OSINT Dark-Web Sentinel Radar**
   * *Konsep*: SIDIK bertransformasi dari sistem investigasi reaktif menjadi sistem peringatan dini (*Early Warning System*) proaktif.
   * *Mekanisme*: Mengintegrasikan *Local Headless Crawler* yang memantau kanal Telegram aktor ancaman siber dan forum gelap secara berkala.
   * *Keunggulan*: Begitu ada aktor ancaman mempublikasikan tangkapan layar atau cuplikan naskah berlabel TNI AD, crawler otomatis memasukkannya ke pipeline investigasi SIDIK, sehingga dalam tempo 60 detik PUSSIBERAD sudah menerima notifikasi atribusi pembocor sebelum berita sempat viral di publik.
5. **Inovasi 5: Hardware Security Module (HSM) Cryptographic Anchor**
   * *Konsep*: Mencegah kecurigaan bahwa administrator sistem dapat merekayasa watermark untuk menjebak perwira tertentu.
   * *Mekanisme*: Seluruh kunci privat penandatanganan payload watermark dan rantai log SHA-256 dikunci di dalam modul perangkat keras fisik *Hardware Security Module (HSM)* atau *TPM 2.0 Chip* bersertifikasi FIPS 140-2 Level 3 pada server Command Center dengan otorisasi kunci ganda (*Dual-Custody Ceremony*).
   * *Keunggulan*: Tidak ada seorang pun—termasuk Super-Admin sistem—yang dapat menerbitkan dokumen ber-watermark palsu atau merekayasa hasil investigasi tanpa otorisasi bersama.

---

### 2.5 Rincian Tech Stack & Arsitektur Komponen

*(Diperbarui sesuai purwarupa yang dibangun; lihat juga `docs/KEPUTUSAN_ARSITEKTUR.md`.)*

1. **Inti Pemrosesan Backend & Forensik:**
   * **Python 3.12/3.13 + FastAPI:** API REST (kontrak OpenAPI) untuk registri, penerbitan salinan, intake bukti, ekspor data, dan audit. Siap diintegrasikan ke SISFO lewat API. Analisis foto berjalan di 2 worker agar unggahan bersamaan tidak saling antre.
   * **SQLAlchemy 2 + Alembic:** model data dan migrasi skema versi demi versi.
2. **Mesin Dokumen:**
   * **PyMuPDF:** render PDF salinan (rata kanan-kiri) dengan modulasi spasi per kata, varian kata, dan honey-token.
3. **Computer Vision (tanpa OCR):**
   * **OpenCV + NumPy:** pelurusan multi-kandidat, registrasi ECC (*Enhanced Correlation Coefficient*) bertahap, perataan pencahayaan, pelacakan baris, korelasi silang sub-piksel per kata, serta pencocokan bentuk kata varian dan digit token. Rancangan awal memakai OCR (Surya/Tesseract); ternyata OCR tidak diperlukan dan malah lebih rapuh, karena tata letak naskah sudah diketahui dari template.
4. **Algoritma Koreksi Galat & Anti-Kolusi:**
   * **Reed-Solomon (`reedsolo`), GF(2⁸), nsym = 8:** frame 104-bit dengan *soft voting* lintas lapis dan cadangan deteksi salah-koreksi.
   * **RapidFuzz:** pencocokan varian kata yang tahan salah ketik, serta validator template (kata varian yang terlalu mirip ditolak).
   * **Honey-token beralfabet besar** (angka acak unik per penerima) sebagai mekanisme anti-kolusi. Tardos = roadmap.
5. **Kedaulatan & Integritas Data:**
   * **PostgreSQL 16:** lokal (Docker) atau basis data bersama tim. TimescaleDB tidak dipakai karena tidak dibutuhkan fitur apa pun.
   * **Ledger rantai hash SHA-256 + tanda tangan Ed25519**, *append-only* dijaga trigger basis data, dengan endpoint verifikasi rantai.
   * **RBAC tiga peran** (admin, distributor, investigator), kata sandi scrypt, sesi HttpOnly, penguncian akun setelah gagal login berulang, dan **persetujuan ganda** untuk salinan naskah RAHASIA/SANGAT RAHASIA.
6. **Frontend & Tampilan Taktis:**
   * **Next.js 16 + React 19 + TypeScript + Tailwind CSS v4:** dashboard taktis (Distribusi, Data Personel, Investigasi foto/teks/dump, Audit Trail, Pengguna). Font sistem, tanpa layanan luar, sehingga siap air-gapped.
7. **Deployment:** Docker Compose (API, web, PostgreSQL); migrasi skema dan kunci ledger disiapkan otomatis saat start.

---

### 2.6 Algoritma Kerja Lapis 2: Semantik Jukminu TNI AD & Reed-Solomon ECC

#### Prinsip Kerja Penyisipan Semantik
Naskah dinas militer Indonesia (diatur dalam Petunjuk Administrasi Umum / Jukminu TNI AD) memiliki struktur formal yang ketat. Lapis 2 memanfaatkan variasi gramatikal dan sinonim resmi yang sah menurut regulasi militer tanpa mengubah maksud, nada hierarki, maupun integritas isi dokumen.

```
+-----------------------------------------------------------------------------------+
|                        STRUKTUR PAYLOAD KONTRA-INTELIJEN                          |
+---------------------+----------------------------------+--------------------------+
| Versi + Flags       | copy_id (acak, penunjuk registri)| Paritas Reed-Solomon     |
| 8 Bit               | 32 Bit                           | 64 Bit (8 simbol)        |
+---------------------+----------------------------------+--------------------------+
|<-------------------------- Total Frame = 104 Bit -------------------------------->|
  NRP, nama, satuan, dan waktu terbit diambil dari registri, tidak ditanam di dokumen.
```

#### Kamus Variasi Semantik Jukminu (Contoh Ilustratif Aturan Transformasi Bit)
Setiap bit atau pasangan bit (2-bit tuple) dikodekan ke dalam pemilihan frasa baku pada posisi kalimat tertentu. *Tabel di bawah adalah ilustrasi; kamus pada naskah demo purwarupa ada di `data/master_templates/naskah_demo.txt` dan masih perlu disahkan ahli Jukminu.*

| Bit Value | Posisi Frasa dalam Jukminu | Pilihan Kata / Frasa Standar Jukminu |
| :---: | :--- | :--- |
| **00** | Rujukan Dasar Perintah | "Berdasarkan surat telegram Panglima TNI Nomor..." |
| **01** | Rujukan Dasar Perintah | "Menindaklanjuti surat telegram Panglima TNI Nomor..." |
| **10** | Rujukan Dasar Perintah | "Merujuk surat telegram Panglima TNI Nomor..." |
| **11** | Rujukan Dasar Perintah | "Sesuai dengan surat telegram Panglima TNI Nomor..." |
| **0** | Klausul Penutup Petunjuk | "...untuk menjadi maklum." |
| **1** | Klausul Penutup Petunjuk | "...untuk dipedomani dan dilaksanakan." |
| **0** | Penulisan Waktu Pasukan | "pukul 08.00 WIB" |
| **1** | Penulisan Waktu Pasukan | "pukul 08.00 Waktu Indonesia Barat" |
| **0** | Frasa Status Operasi | "dalam status siap siaga operasional penuh" |
| **1** | Frasa Status Operasi | "dalam kondisi kesiapsiagaan operasi penuh" |

#### Ketahanan Terhadap Pengetikan Ulang (Retyping Resilience via Reed-Solomon)
Ketika seorang oknum pembocor hanya mengetik ulang 2 paragraf di aplikasi pesan singkat (Signal/Telegram) dan mengganti kata-kata tertentu, ia menimbulkan dua jenis galat (*error*):
1. **Erasures (Penghapusan):** Kalimat-kalimat lain yang tidak diketik dianggap sebagai simbol yang hilang.
2. **Bit Flips / Errors (Perubahan):** Kata sinonim yang sengaja ia ubah secara manual.

Dengan mengaplikasikan algoritma **Reed-Solomon $RS(13, 5)$ atas $GF(2^8)$**:
$$\text{Kapasitas Koreksi: } 2E + S \le N - K = 8 \quad (\text{SIDIK menerima hanya } 2E + S \le 6)$$
Di mana:
* $E$ = byte frame yang salah (varian yang diubah ke varian lain)
* $S$ = byte frame yang tidak teramati (*erasure*: kalimat yang tidak dikutip, atau varian yang ragu)
* $N = 13$ byte frame; $K = 5$ byte data

*Hasil terukur* (simulasi kutipan berurutan, 200 percobaan per panjang, naskah sekitar 400 kata, Lapis 2 saja):

| Bagian naskah yang dikutip | Teridentifikasi | Salah tuduh |
| :--- | :-: | :-: |
| 15 kata | 0% | 0 |
| 100 kata (25%) | 0% | 0 |
| 200 kata (50%) | 68% | 0 |
| 250 kata (62%) | 100% | 0 |

Kutipan yang lebih pendek tetap tertolong **Lapis 3**: dua angka honey-token dalam kutipan sudah cukup untuk identifikasi. Untuk kutipan sangat pendek tanpa angka, sistem **menolak menebak**. Ini batas matematis (satu kalimat hanya membawa sekitar 4 bit), bukan kekurangan implementasi.

---

### 2.7 Hasil Uji Purwarupa (Terukur, Bukan Klaim)

Pengujian memakai foto HP sungguhan, simulasi kamera (perspektif, bayangan, blur, noise, JPEG), dan **231 tes otomatis**. Sumbernya dicatat di folder `docs/` (`SPIKE_LAYER1_HASIL.md`, `HASIL_LAPIS2/3/4.md`, `TANGGAPAN_ISSUE_GAP.md`).

| Uji | Kondisi | Hasil |
| :--- | :--- | :--- |
| Foto HP asli, halaman uji Lapis 1 | 11 foto, miring sampai 35°, dipegang tangan, 720p | **6/7** salinan bertanda teridentifikasi, **4/4** kontrol ditolak, **0 salah** |
| Foto layar laptop (foto asli tim) | PDF di layar, sekitar 60% halaman tampak | 53/53 bit spasi terbaca **benar**; tidak diatribusikan karena bukti kurang (sistem menolak menebak) |
| Foto potongan (simulasi) | 95%, 70%, setengah atas, setengah bawah | Semua teridentifikasi; potongan 3 baris ditolak tanpa error |
| Cap dinas, tanda tangan, keduanya (simulasi) | Menimpa teks badan naskah, foto miring 20° | 3/3, 3/3, 3/3, **0 salah** |
| Kertas lipat empat (simulasi) | Lekuk 4, 10, dan 20 px | 3/3 untuk setiap tingkat, **0 salah** |
| Honey-token dari foto (simulasi) | 8 foto, sisi 1600–3200 px, miring 0–35° | 41/48 token terbaca, **0 salah baca** |
| Ketik ulang (Lapis 2) | Kutipan 62% naskah | 100% teridentifikasi, 0 salah tuduh |
| Parafrase total + 2 angka fakta (Lapis 3) | Kalimat ditulis ulang tanpa kata varian | Teridentifikasi |
| Kolusi 2 salinan (Lapis 3) | Token dicampur dari dua salinan | **Kedua** salinan teridentifikasi, penerima lain tidak ikut tertuduh |
| Dump ekspor / SQL injection (Lapis 4) | Ekspor utuh, potongan, dua ekspor digabung, dump tabel | Terlacak ke ekspor dan akun yang tepat, atau ke "akses langsung basis data" |
| Hoaks data (Lapis 4) | Data publik lama berkop militer; NIK acak | DAUR ULANG; REKAAN |
| Persetujuan ganda | Pengaju mencoba menyetujui sendiri | Ditolak; salinan belum terbit tidak bisa diunduh dan tidak pernah diatribusikan |

Di semua uji di atas, **tidak ada satu pun salah tuduh**. Analisis satu foto memakan waktu 10–30 detik.

---

# BAGIAN 3: SKENARIO DEMO VITAL (3-MINUTE LIVE HACKATHON DEMO)

### Ringkasan Alur Pitch & Live Demo (3 Menit Penuh Aksi)

```
[00:00 - 00:25] ==================> THE HOOK & REAL THREAT
                    Insiden BAIS & Teixeira: Mengapa DLP Konvensional Lumpuh?
[00:25 - 01:05] ==================> LIVE TEST 1: FOTO HP MIRING
                    Lapis 1 + 2 + 3 dibaca dari satu foto -> TARGET TERIDENTIFIKASI
[01:05 - 01:45] ==================> LIVE TEST 2: KETIK ULANG & PARAFRASE AI
                    Lapis 2 (kata) lalu Lapis 3 (honey-token) saat kalimat ditulis ulang total
[01:45 - 02:30] ==================> LIVE TEST 3: KLAIM "DATABASE TNI AD BOCOR"
                    Lapis 4: hoaks daur ulang vs kebocoran asli dari ekspor tertentu
[02:30 - 03:00] ==================> CLOSING: NOL SALAH TUDUH & AUDIT TRAIL
                    Rantai bukti terverifikasi, 100% on-premise
```

Persiapan sebelum naik panggung (urutan klik ada di `docs/PANDUAN_DEMO_DASHBOARD.md`): salinan RAHASIA untuk Kolonel Inf Hendro sudah **diajukan dan disetujui** (four-eyes), PDF-nya sudah dicetak, data personel demo sudah diisi, dan satu ekspor CSV serta dua sampel dump hoaks sudah siap.

---

### Naskah Demonstrasi Panggung (Stage Pitch Script)

#### Menit 00:00 - 00:25 | The Operational Hook & Ancaman Nyata
*(Layar menampilkan berita kebocoran Discord Pentagon Jack Teixeira dan klaim kebocoran data BAIS TNI).*

> **Pitcher:**  
> "Selamat pagi Dewan Juri yang terhormat.  
> Tahun 2023, seorang prajurit intelijen membocorkan rencana perang Pentagon hanya dengan memotret kertas di atas meja. Tahun 2024, data BAIS diklaim bocor di forum gelap, dan publik tidak tahu apakah itu fakta atau psywar.  
> Firewall dan DLP **buta** begitu dokumen difoto, diketik ulang, atau datanya diunggah ke forum gelap.  
> Hari ini kami mempersembahkan **SIDIK**: setiap salinan dokumen dan data membawa identitas penerimanya sendiri."

---

#### Menit 00:25 - 01:05 | Live Test 1: Foto HP Miring (Lapis 1 + 2 + 3)
*(Co-Presenter memegang kertas cetak PDF salinan dan smartphone).*

> **Pitcher:**  
> "Ini surat telegram RAHASIA untuk Kolonel Infanteri Hendro. Salinan ini baru terbit setelah disetujui pejabat kedua, karena untuk naskah RAHASIA kami menerapkan *four-eyes principle*. Tidak ada watermark kasat mata: format naskah dinas rata kanan-kiri, rapi seperti biasa.  
> Rekan saya memotretnya miring, di bawah lampu ruangan, seperti oknum yang membocorkan."

*(Foto diunggah di Investigasi → tab Foto).*

> **Pitcher:**  
> "SIDIK meluruskan halaman, membaca pilihan kata, angka fiktif, dan pergeseran spasi setengah poin di setiap kata, **tanpa OCR**. Lalu:  
> **TARGET TERIDENTIFIKASI: Kolonel Infanteri Hendro, NRP 1102003912, Kodam Jaya**, beserta waktu terbit salinannya.  
> Perhatikan rincian buktinya: lapis spasi, lapis kata, dan honey-token masing-masing terbaca. Dokumen difoto, identitasnya tetap ikut."

---

#### Menit 01:05 - 01:45 | Live Test 2: Ketik Ulang, lalu Parafrase AI (Lapis 2 → Lapis 3)
*(Layar menampilkan tab Teks).*

> **Pitcher:**  
> "Pembocor yang lebih lihai berkata: *'Saya ketik ulang saja di Telegram.'* Kami tempel teks yang diketik ulang dua pertiganya, lengkap dengan huruf kapital acak dan salah ketik."

*(Analisis → TERIDENTIFIKASI; Lapis 2 TERBACA; kemiripan dengan naskah resmi sekitar 70–90%).*

> **Pitcher:**  
> "Spasi memang hilang, tetapi pilihan kata tetap ikut tersalin, dan Reed-Solomon memulihkan sisanya.  
> Lalu bagaimana kalau kalimatnya ditulis ulang total oleh ChatGPT? Ini parafrasenya: tidak ada satu kalimat pun yang sama."

*(Tempel parafrase yang mengutip frekuensi dan nomor REG-AL → TERIDENTIFIKASI; Lapis 2 KURANG, Lapis 3 TERBACA).*

> **Pitcher:**  
> "Kata bisa diparafrase, tetapi **fakta intelijen tidak**. Frekuensi 143,275 MHz dan nomor REG-AL ini hanya tercetak di salinan Kolonel Hendro. Kalau dua oknum menggabungkan salinannya, keduanya muncul sebagai **indikasi kolusi**."

---

#### Menit 01:45 - 02:30 | Live Test 3: Klaim "Database TNI AD Bocor" (Lapis 4)
*(Layar menampilkan unggahan forum gelap: 'TNI AD DATABASE LEAKED').*

> **Pitcher:**  
> "Hacker anonim mengklaim membobol data personel TNI AD. Fakta, atau psywar? Kami unggah dump-nya."

*(Tab Data dump → `dump_hoaks_daur_ulang.csv` → **HOAKS: DAUR ULANG**, cocok dengan korpus data publik lama).*

> **Pitcher:**  
> "Tidak ada satu pun honey-record kami, dan seluruh identitasnya cocok dengan data publik lama yang sudah dikenal. Dispenad bisa langsung mengklarifikasi dengan bukti.  
> Sekarang kebocoran yang asli: berkas ekspor data personel yang dikirim ke luar."

*(Unggah CSV ekspor → **KEBOCORAN ASLI**: Ekspor #N, akun pengekspor, waktu, keperluan).*

> **Pitcher:**  
> "Setiap ekspor diberi personel fiktif yang unik. Kami tahu persis **ekspor mana, oleh akun siapa, kapan**."

---

#### Menit 02:30 - 03:00 | Penutup: Nol Salah Tuduh & Kedaulatan
*(Layar Audit Trail → Verifikasi rantai → VALID).*

> **Pitcher:**  
> "Semua langkah tadi tercatat di rantai hash bertanda tangan digital yang bisa diverifikasi, dan admin pun tidak bisa mengubahnya.  
> Satu hal yang paling kami jaga: **SIDIK tidak pernah menebak**. Bila bukti kurang, sistem menolak. Di semua pengujian kami, tidak ada satu pun salah tuduh.  
> Semua berjalan **100% on-premise**, tanpa cloud asing.  
> *Jika Anda membocorkan rahasia negara, dokumen itu sendiri yang akan menyebut nama Anda.*  
> Terima kasih. Cakra Perkasa, PUSSIBERAD Kuat, Pertahanan Siber TNI AD Berdaulat!"

---

### 3.4 Contoh Konkret Naskah Dinas: Sebelum vs. Sesudah Watermark SIDIK

#### Contoh Dokumen ASLI (Sebelum Watermarking):
```text
KOMANDO DAERAH MILITER JAYA/JAYAKARTA
MARKAS KOMANDO
================================================================================
                                                       RAHASIA
                                                       Salinan Nomor: 01
                                                       Jumlah Salinan: 05

SURAT TELEGRAM PANGLIMA KODAM JAYA
DARI     : PANGDAM JAYA
KEPADA   : PARA DANREM, DANDIM JAJARAN KODAM JAYA
TEMBUSAN : KASAD, PANGKODIKLATAD, DANPUSSIBERAD

NOMOR: ST/412/OPS-SIB/X/2026                            TGL: 30-10-2026

DERAJAT : KILAT
KLASIFIKASI : RAHASIA

1. DASAR:
   A. SURAT KEPUTUSAN PANGLIMA TNI NOMOR KEP/882/IX/2026 TANGGAL 15 SEPTEMBER 2026
      TENTANG GELAR KEKUATAN PENGAMANAN KTT INTERNASIONAL.
   B. PERTIMBANGAN KOMANDO DAN STAF KODAM JAYA TENTANG ANCAMAN SIBER ASIMETRIS.

2. SEHUBUNGAN DASAR TERSEBUT DI ATAS, DIPERINTAHKAN KEPADA DISTRIBUSI ALAMAT
   UNTUK MELAKSANAKAN KESIAPSIAGAAN TINGKAT SATU SEBAGAI BERIKUT:
   A. MENYIAPKAN UNSUR TIM TANGGAP INSIDEN SIBER (CSIRT) PADA MASING-MASING
      SATUAN SELAMA 1 X 24 JAM.
   B. MELAPORKAN SETIAP ANOMALI TRAFIK JARINGAN MILITER KEPADA PUSKODAL KODAM JAYA
      PADA KESEMPATAN PERTAMA.

3. SELESAI DAN UNTUK DILAKSANAKAN DENGAN PENUH TANGGUNG JAWAB.
```

#### Contoh Dokumen SESUDAH Watermarking SIDIK (Diterima oleh Letkol A):
```text
KOMANDO DAERAH MILITER JAYA/JAYAKARTA
MARKAS KOMANDO
================================================================================
                                                       RAHASIA
                                                       Salinan Nomor: 03
                                                       Jumlah Salinan: 05

SURAT TELEGRAM PANGLIMA KODAM JAYA
DARI     : PANGDAM JAYA
KEPADA   : PARA DANREM, DANDIM JAJARAN KODAM JAYA
TEMBUSAN : KASAD, PANGKODIKLATAD, DANPUSSIBERAD

NOMOR: ST/412/OPS-SIB/X/2026                            TGL: 30-10-2026

DERAJAT : KILAT
KLASIFIKASI : RAHASIA

1. DASAR:
   A. MERUJUK PADA SURAT KEPUTUSAN PANGLIMA TNI NOMOR KEP/882/IX/2026 TANGGAL 15 
      SEPTEMBER 2026 TENTANG GELAR KEKUATAN PENGAMANAN KTT INTERNASIONAL.
      [Perubahan Lapis 2: "A. MERUJUK PADA..." mengodekan Bit 10]
   B. PERTIMBANGAN KOMANDO SERTA STAF KODAM JAYA MENGENAI ANCAMAN SIBER ASIMETRIS.
      [Perubahan Lapis 2: "...SERTA STAF... MENGENAI..." mengodekan Bit 01]

2. BERKENAAN DENGAN DASAR TERSEBUT DI ATAS, DIPERINTAHKAN KEPADA DISTRIBUSI ALAMAT
   [Perubahan Lapis 2: "BERKENAAN DENGAN..." mengodekan Bit 00]
   UNTUK MELAKSANAKAN KESIAPSIAGAAN TINGKAT SATU SEBAGAI BERIKUT:
   A. MENYIAPKAN SATUAN UNSUR TIM TANGGAP INSIDEN SIBER (CSIRT) PADA MASING-MASING
      SATUAN SELAMA 24 JAM PENUH.
      [Perubahan Lapis 2: "SATUAN UNSUR..." dan "...24 JAM PENUH" mengodekan Bit 11]
   B. MELAPORKAN SEGALA ANOMALI LALU LINTAS JARINGAN MILITER KEPADA PUSKODAL 
      KODAM JAYA PADA KESEMPATAN PERTAMA.
      [Perubahan Lapis 2: "SEGALA ANOMALI LALU LINTAS..." mengodekan Bit 01]

3. SELESAI DAN UNTUK DIPEDOMANI SERTA DILAKSANAKAN DENGAN PENUH TANGGUNG JAWAB.
   [Perubahan Lapis 2: "DIPEDOMANI SERTA DILAKSANAKAN" mengodekan Bit 1]

[CATATAN LAPIS 1 VISUAL]: 
Secara bersamaan, pada file PDF, spasi antar-kata digeser berpasangan (+0,5 pt / -0,5 pt)
di seluruh baris, sehingga lebar baris dan margin rata kanan-kiri tetap utuh.

[CATATAN LAPIS 3 HONEY-TOKEN]:
Angka fakta seperti frekuensi, nomor registrasi alpalhankam, dan koordinat dicetak dengan
digit yang berbeda untuk setiap penerima (mis. "REG-AL-48271" hanya di salinan Letkol A).

Bagi mata manusia salinan ini tampak seperti naskah biasa, namun bagi SIDIK ia membawa
identitas tunggal: salinan milik LETKOL CHB A.
```
*Contoh di atas ilustratif. Naskah demo purwarupa ada di `data/master_templates/naskah_demo.txt`.*

---

# BAGIAN 4: FAQS & STRATEGI TANYA-JAWAB KRITIS DEPAN JURI

### Pertanyaan 1 (Parafrase Ekstrem):
> **Juri PUSSIBERAD:**  
> *"Bagaimana jika pembocor tidak mengambil foto dan tidak mengetik ulang kalimat naskah dinas, melainkan memparafrase total intisarinya menggunakan generative AI seperti ChatGPT/Llama, lalu menyebarkannya?"*

* **Jawaban Tangkas & Otoritatif:**  
  "Izin menjawab, Komandan. Jika teks diparafrase total, Lapis 1 (spasi) dan Lapis 2 (pilihan kata) memang hilang. Di sinilah **Lapis 3: Honey-Token** bekerja.  
  Setiap salinan memuat angka fakta fiktif yang digitnya **diacak khusus untuk penerimanya**: frekuensi, nomor registrasi alpalhankam, kanal komunikasi, dan koordinat. Angka ini tidak bisa ditebak dan unik di seluruh registri.  
  Orang yang memparafrase dokumen intelijen umumnya tetap mengutip fakta intinya, karena tanpa itu informasinya tidak bernilai. Begitu **dua** angka itu muncul di parafrase, SIDIK menunjuk salinan pemiliknya. Kami sudah mendemonstrasikannya tadi. Kalau hanya satu angka, sistem menandainya sebagai *indikasi*, bukan tuduhan.  
  Batasannya kami akui dengan jujur: bila pelaku membuang **semua** angka, Lapis 3 pun kehilangan pijakan. Tetapi bocorannya juga kehilangan nilai intelijen. Selain itu, SIDIK mengukur **kemiripan teks dengan naskah resmi**, sehingga penyidik tahu apakah teks itu salinan, parafrase, atau rekaan."

---

### Pertanyaan 2 (Collusion Attack / Pembandingan Salinan):
> **Juri PUSSIBERAD:**  
> *"Bagaimana jika ada dua atau tiga oknum perwira bersekongkol (collusion), mengumpulkan salinan dokumen milik masing-masing, lalu membandingkan perbedaan kata atau spasi untuk menemukan watermark kalian lalu menghapusnya?"*

* **Jawaban Tangkas & Otoritatif:**  
  "Siap, ini *collusion attack*, ancaman klasik pada sidik jari dokumen. SIDIK menghadapinya dengan tiga cara:  
  1. **Mencampur kata atau spasi dari dua salinan tidak menghasilkan tuduhan yang salah.** Bila Lapis 1 menunjuk satu salinan dan Lapis 2 menunjuk salinan lain, hasilnya **BUKTI BERTENTANGAN**: tanda manipulasi, tanpa atribusi. Reed-Solomon dengan cadangan deteksi juga menolak campuran yang kacau. Jadi kolusi tidak bisa dipakai untuk menjebak orang lain.  
  2. **Honey-token membongkar para pelaku.** Setiap angka fakta yang mereka pertahankan menunjuk pemiliknya secara pasti. Bila token dari dua salinan muncul bersama, SIDIK melaporkan **INDIKASI KOLUSI** beserta semua salinan yang terlibat, sementara penerima lain tidak ikut tertuduh (sudah diuji).  
  3. **Membuang semua perbedaan = membuang nilai intelijen.** Untuk menghapus jejak, pelaku harus membuang semua angka fakta dan semua kata yang berbeda, sehingga isi bocorannya kehilangan nilai.  
  Kami jujur soal batasnya: dengan 6 token per naskah, pelacakan paling andal untuk 2–3 pelaku. Kami sudah menghitung kode Tardos: butuh sekitar 230 bit untuk 2 pelaku dan ribuan bit untuk 5 pelaku, melebihi kapasitas naskah satu halaman. Tardos kami tempatkan di roadmap untuk naskah multi-halaman."

---

### Pertanyaan 3 (Integritas Aturan Naskah Dinas Militer):
> **Juri PUSSIBERAD:**  
> *"Tata Naskah Dinas TNI AD (Jukminu) diatur sangat ketat dalam Perkasad. Sedikit saja salah tanda baca atau format bisa dianggap cacat administrasi dinas militer. Apakah manipulasi font atau pergantian kata pada SIDIK tidak melanggar Jukminu?"*

* **Jawaban Tangkas & Otoritatif:**  
  "Siap, kami memahami sepenuhnya bahwa disiplin administrasi adalah cerminan disiplin prajurit. SIDIK dirancang dengan prinsip **Zero Administrative Violation**:  
  1. Pada Lapis 1 (Visual), spasi antar-kata digeser **berpasangan** ±0,5 poin: satu spasi melebar, spasi berikutnya menyempit dengan besar yang sama. Lebar baris tidak berubah, sehingga margin dan perataan **rata kanan-kiri** tetap lurus. Variasi spasi sekecil ini lumrah pada teks rata kanan-kiri. Kami memilih 0,5 poin dari uji foto HP sungguhan: amplitudo yang lebih kecil tidak terbaca andal dari kamera.  
  2. Pada Lapis 2 (Semantik), mesin tidak mengarang kata. Kamus varian **ditulis oleh pemilik naskah** dalam template, dan mesin hanya memilih di antara varian yang diizinkan. Validator otomatis menolak varian yang ambigu. Kami terbuka: kamus pada naskah demo masih padanan leksikal umum, sehingga untuk adopsi resmi kamus itu perlu disahkan ahli Jukminu. Mesinnya tidak perlu diubah.  
  3. Honey-token hanya mengganti digit angka fakta. Lebar setiap digit sama, sehingga tata letak naskah tidak bergeser sedikit pun."

---

### Pertanyaan 4 (Kemampuan Operasional Offline / Air-Gapped):
> **Juri PUSSIBERAD:**  
> *"Jaringan PUSSIBERAD dan Satuan Siber TNI AD beroperasi secara Air-Gapped terisolasi total dari internet luar demi keamanan. Apakah sistem SIDIK membutuhkan API luar, cloud computing, atau update model dari internet?"*

* **Jawaban Tangkas & Otoritatif:**  
  "Siap, tidak sama sekali. SIDIK menganut prinsip **100% Sovereign & On-Premise Air-Gapped Architecture**.  
  Seluruh komponen (pustaka matriks, OpenCV, PyMuPDF, Reed-Solomon, basis data PostgreSQL, dan dashboard) berjalan dalam container Docker di server lokal. SIDIK **tidak memakai OCR atau model AI** yang perlu diunduh, dan dashboard memakai font sistem, tanpa memanggil layanan luar.  
  Log audit forensik dikunci dengan rantai hash SHA-256 bertanda tangan Ed25519 di basis data lokal, tanpa blockchain publik. Tidak ada metadata militer yang keluar ke penyedia teknologi luar negeri."

---

### Pertanyaan 5 (Penanganan Hoax / False Alarm Psywar):
> **Juri PUSSIBERAD:**  
> *"Di media sosial sering kali beredar tangkapan layar dokumen bertuliskan 'RAHASIA' yang ternyata palsu atau buatan buzzer untuk mendiskreditkan pimpinan TNI. Bagaimana SIDIK memastikan sistem tidak salah menuduh personel (False Accusation)?"*

* **Jawaban Tangkas & Otoritatif:**  
  "Siap. Nol salah tuduh adalah prinsip pertama SIDIK, dan diterapkan berlapis:  
  1. **Bukti harus cukup secara matematis.** Reed-Solomon hanya diterima bila kerusakannya jauh dari batas koreksi. Honey-token dan honey-record butuh minimal dua kecocokan. Bila kurang, statusnya **BUKTI TIDAK CUKUP**, dan sistem menolak menebak.  
  2. **Salinan harus terdaftar dan benar-benar pernah diedarkan.** Penanda yang terbaca tetapi tidak ada di registri berstatus **TIDAK TERDAFTAR**, yang mengindikasikan dokumen palsu. Salinan yang belum disetujui atau ditolak tidak pernah diatribusikan.  
  3. **Bukti yang saling bertentangan ditolak.** Dokumen hasil tempelan dua salinan ditandai sebagai manipulasi.  
  4. **Membedakan asli dan rekaan.** Untuk dokumen, SIDIK mengukur **kemiripan dengan naskah resmi**: dokumen rekaan buzzer bernilai sekitar 0%, sedangkan salinan asli di atas 90%. Untuk klaim kebocoran data, verifier membedakan **kebocoran asli**, **daur ulang data publik lama**, dan **data rekaan**.  
  5. **Hasil adalah petunjuk, bukan vonis.** Atribusi berbunyi "salinan yang bocor", bukan "pelaku bersalah", dan setiap pemeriksaan tercatat di rantai bukti yang tidak bisa diubah.  
  SIDIK melindungi institusi dari dua arah: menemukan sumber kebocoran yang nyata, dan melindungi personel serta pimpinan dari tuduhan dan dokumen rekayasa."

---

# BAGIAN 5: ROADMAP TUGAS TIM (TIMELINE 2 MINGGU)

*Catatan: jadwal di bawah adalah rencana awal. Beberapa butir diganti dalam pelaksanaan berdasarkan hasil uji, yaitu OCR, `python-docx`, dan AI verifier (lihat Bagian 2.5 dan `docs/KEPUTUSAN_ARSITEKTUR.md`). Butir tambahan yang terealisasi: Lapis 3 honey-token, persetujuan ganda, basis data bersama tim, dan format rata kanan-kiri.*

### Pembagian Peran dan Matriks Tanggung Jawab Tim

* **Role 1: Frontend & UI-UX Engineer (TOC / Dashboard Specialist)**
  * Bertanggung jawab atas antarmuka Taktis Siber (Next.js/Tailwind), dashboard monitoring dokumen, modul visualisasi penemu kebocoran, dan tampilan interaktif perbandingan dokumen asli vs dokumen bocor.
* **Role 2: Backend & Forensics / NLP Engineer (Core System Specialist)**
  * Bertanggung jawab atas modulasi spasi PDF (PyMuPDF), engine varian kata Jukminu, honey-token dan honey-record, pengkodean Reed-Solomon, pipeline computer vision tanpa OCR (OpenCV), serta audit log hash chain.
* **Role 3: Product Manager, Military Domain & Pitcher (Strategist & Lead Pitcher)**
  * Bertanggung jawab atas pemetaan regulasi Jukminu TNI AD, perancangan skenario demo panggung yang dramatis, penyusunan proposal submisi, materi presentasi pitch deck, serta kepatuhan hukum forensik siber.

---

### Jadwal Eksekusi Harian (Daily Sprint Timeline)

```
MINGGU 1: PENGEMBANGAN INTI TEKNOLOGI & ARSITEKTUR
========================================================================================================
HARI    | ROLE 1: FRONTEND / UI-UX      | ROLE 2: BACKEND & FORENSICS   | ROLE 3: PM & MILITARY DOMAIN
--------+-------------------------------+-------------------------------+-------------------------------
HARI 1  | Setup Next.js, Design System  | Setup FastAPI, PostgreSQL,    | Analisis Perkasad Jukminu &
        | Military Dark Mode (Tailwind) | PyMuPDF, OpenCV env           | Studi Kasus BAIS/Pentagon
--------+-------------------------------+-------------------------------+-------------------------------
HARI 2  | Wireframing Dashboard         | Riset modul modulasi spasial  | Kurasi kamus 50 variasi
        | Distribusi & Modul Upload     | glyph PDF (PyMuPDF vector)    | frasa baku Jukminu TNI AD
--------+-------------------------------+-------------------------------+-------------------------------
HARI 3  | Halaman Detail Dokumen &      | Implementasi Lapis 1 Engine:  | Rancang skema payload ID
        | Visualizer Posisi Watermark   | Micro-Glyph Shift pada PDF    | (NRP + Waktu + Paritas)
--------+-------------------------------+-------------------------------+-------------------------------
HARI 4  | UI Modul 'Leak Intake Portal' | Integrasi modul python-docx & | Penyusunan draf Bab 1 & 2
        | (Area Drop Foto / Teks Bocor) | pergantian teks semantik      | Dokumen Proposal Submisi
--------+-------------------------------+-------------------------------+-------------------------------
HARI 5  | Komponen Visual Perbandingan  | Implementasi Reed-Solomon ECC | Validasi ketahanan semantik
        | Diff Teks (Asli vs Bocoran)   | encoder & decoder (reedsolo)  | terhadap variasi tata kalimat
--------+-------------------------------+-------------------------------+-------------------------------
HARI 6  | Dashboard Forensic Result     | Pipeline Vision: Homography,  | Uji coba sampling foto HP
        | (Target Found, Confidence Bar)| Deskew, & Binarization OpenCV | di berbagai sudut & cahaya
--------+-------------------------------+-------------------------------+-------------------------------
HARI 7  | Review UI & Integrasi state   | Integrasi Surya/Tesseract OCR | Evaluasi Sprint Minggu 1 &
        | manajemen ke mock data awal   | dengan Decoder Lapis 1 Visual | penajaman konsep nilai jual
========================================================================================================

MINGGU 2: INTEGRASI, PENGUJIAN ROBUSTNESS, DAN PERSIAPAN PITCHING
========================================================================================================
HARI    | ROLE 1: FRONTEND / UI-UX      | ROLE 2: BACKEND & FORENSICS   | ROLE 3: PM & MILITARY DOMAIN
--------+-------------------------------+-------------------------------+-------------------------------
HARI 8  | Integrasi API Frontend ke     | Pengembangan Modul Lapis 4:   | Finalisasi Bab 3 & 4 Proposal
        | Backend FastAPI Endpoints     | Honey-Record Generator DB     | (Kelayakan & Implementasi)
--------+-------------------------------+-------------------------------+-------------------------------
HARI 9  | Halaman 'AI Psywar Verifier'  | Implementasi Algoritma Deteksi| Pengumpulan sampel kebocoran
        | dengan grafik probabilitas    | Klaim Palsu (Leak Claim AI)   | nyata di forum gelap utk demo
--------+-------------------------------+-------------------------------+-------------------------------
HARI 10 | Halaman Audit Trail Log       | Implementasi SHA-256 Tamper-  | Finalisasi Dokumen Proposal &
        | (Visualisasi Hash Chain)      | Proof Log Hash Chaining di DB | Formatting PDF Submisi
--------+-------------------------------+-------------------------------+-------------------------------
HARI 11 | Polish UI/UX, Animasi Radar   | Stress-test ketahanan foto HP | Pembuatan Slide Deck Pitching
        | Forensik, & Audio Effect Taktis| dan retyping 5 varian naskah | (Maksimal 10 slide berdampak)
--------+-------------------------------+-------------------------------+-------------------------------
HARI 12 | Freeze Fitur Frontend &       | Freeze Backend & siapkan      | Gladi Bersih Demo 3 Menit &
        | penguncian skenario demo      | container offline (Docker)    | simulasi tanya-jawab juri
--------+-------------------------------+-------------------------------+-------------------------------
HARI 13 | Backup rekaman video demo     | Penyiapan lokal environment   | Rehearsal intensif & simulasi
        | resolusi tinggi (Fail-safe)   | cadangan (Laptop sekunder)    | jawaban pertanyaan jebakan
--------+-------------------------------+-------------------------------+-------------------------------
HARI 14 | SUBMISI FINAL PRODUK          | STANDBY DEMO HACKATHON        | PITCHING DAY DI DEPAN JURI
        | & DOKUMENTASI LENGKAP         | & TECHNICAL DEFENSE           | PUSSIBERAD & CODEPOLITAN!
========================================================================================================
```

---
*Dokumen ini dirancang sebagai acuan standar rekayasa teknologi pertahanan siber militer dan siap dipergunakan sebagai berkas submisi resmi tim pada ajang Kartika Cyber Hackathon.*
