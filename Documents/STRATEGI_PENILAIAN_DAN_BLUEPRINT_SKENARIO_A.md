# STRATEGI PEMENANGAN & BLUEPRINT ARSITEKTUR PURWARUPA (SKENARIO A)
## KARTIKA CYBER HACKATHON — PUSSIBERAD & CODEPOLITAN
**Kategori:** Defensive Shield (Penangkalan)  
**Produk:** **SIDIK (Sistem Identifikasi Dokumen dan Investigasi Kebocoran)**  
**Status Eksekusi:** *Locked Strategy — Skenario A (Core Defensive Shield)*

---

# 1. KONTEKS STRATEGIS: MENGAPA SKENARIO A?

Berdasarkan analisis kelayakan teknis (*technical feasibility*) dan batasan waktu kompetisi hackathon, tim secara resmi mengunci **Skenario A** sebagai jalur utama pengembangan (*The Winning Path*).

### Rasional Keputusan:
1. **Tingkat Realisme Tinggi (85% – 90%):** Memanfaatkan fondasi pustaka teruji (`PyMuPDF`, `reedsolo`, `OpenCV`, `pytesseract`, `FastAPI`, dan `Next.js`) sehingga purwarupa dapat dituntaskan 100% dalam waktu 7–10 hari tanpa risiko kebuntuan teknis (*deadlock*).
2. **Stabilitas Demonstrasi Panggung (> 95%):** Mengeliminasi ketergantungan pada hardware militer mahal (HSM fisik) dan koneksi internet luar (Dark Web scraping), sehingga meminimalkan risiko kegagalan live demo di hadapan dewan juri PUSSIBERAD.
3. **Fokus Menyelesaikan Masalah Faktual:** Secara presisi menjawab luka nyata pertahanan siber militer: kebocoran analog melalui kamera HP (kasus Jack Teixeira/Pentagon) dan kebocoran chat/forum gelap (kasus BAIS TNI).

---

# 2. MATRIKS PENILAIAN & TAKTIK EKSEKUSI TIM SIDIK

Berikut adalah pemetaan strategi untuk memaksimalkan perolehan nilai pada kelima kriteria penilaian resmi Kartika Cyber Hackathon:

| Kriteria & Bobot | Tantangan Nyata Siber Militer | Taktik Eksekusi SIDIK (Skenario A) | Target Nilai |
| :--- | :--- | :--- | :---: |
| **1. Relevansi & Manfaat (25%)** | Kebocoran data BAIS (2024), kebocoran dokumen operasi via foto HP, dan kutipan teks di grup Telegram yang melumpuhkan sistem DLP/Firewall konvensional. | **Menutup "The Analog Gap":** Membuktikan bahwa SIDIK adalah solusi penangkalan aktif yang bekerja di medium apa pun data dibocorkan (kamera smartphone, scan, printout, maupun ketik ulang teks). | **25 / 25** |
| **2. Inovasi Teknis (25%)** | Watermark visual kasat mata merusak format naskah dinas militer; metadata PDF mudah dihapus menggunakan software gratisan (*ExifTool*). | **Fusi Forensik Unik:** Mengawinkan *Micro-Glyph Spatial Modulation* pada PDF (Lapis 1) dengan *Reed-Solomon Error-Correcting Code* pada Tata Naskah Dinas Jukminu TNI AD (Lapis 2). | **25 / 25** |
| **3. Fungsionalitas Purwarupa (25%)** | Banyak tim hackathon hanya menyajikan UI mockup atau slide presentasi tanpa *functional backend* yang benar-benar bekerja. | **Live Demo Panggung Dramatis (3 Menit):** Membuktikan secara nyata di depan juri: foto miring HP dan ketik ulang teks Telegram berhasil didekode dan identitas pembocor terkunci seketika. | **25 / 25** |
| **4. Kelayakan Implementasi (15%)** | Lingkungan militer beroperasi secara *Air-Gapped* (terisolasi total dari internet) dan sangat patuh pada aturan kaku Jukminu (Perkasad No. 36 Tahun 2018). | **100% Sovereign & Zero Violation:** Arsitektur mandiri (*zero cloud dependency*), berjalan di intranet lokal Mabesad, serta menjamin *Zero Administrative Violation* pada format naskah dinas. | **15 / 15** |
| **5. Dokumentasi & Regulasi (10%)** | Hasil investigasi siber sering gugur di Pengadilan Militer karena rantai bukti digital (*Chain of Custody*) mudah disanggah atau dimanipulasi. | **Cryptographic Tamper-Proof Trail:** Penerapan *SHA-256 Log Hash Chain* yang mengunci setiap rekaman pembuktian forensik secara matematis dan sah secara hukum militer. | **10 / 10** |

---

# 3. BLUEPRINT STRUKTUR REPOSITORI PURWARUPA (SKENARIO A)

Untuk memastikan kolaborasi paralel tanpa hambatan antara Frontend Engineer, Backend/Forensic Engineer, dan Product Manager/Pitcher, berikut struktur direktori proyek yang dibakukan:

```text
PUSSIBERADxCODEPOLITAN_Hackathon/
│
├── Documents/
│   ├── PROPOSAL_DAN_SPESIFIKASI_SIDIK.md            <-- Berkas Master Proposal Submisi Lengkap
│   └── STRATEGI_PENILAIAN_DAN_BLUEPRINT_SKENARIO_A.md <-- Berkas Strategi Eksekusi & Arsitektur Kode
│
├── backend/                                         <-- Lingkungan Python 3.11+ / FastAPI
│   ├── app/
│   │   ├── main.py                                  <-- FastAPI Entrypoint & REST API Endpoints
│   │   ├── config.py                                <-- Kunci Kriptografi & Konfigurasi Air-Gapped
│   │   │
│   │   ├── core/                                    <-- INTI MESIN FORENSIK DEFENSIVE SHIELD
│   │   │   ├── __init__.py
│   │   │   ├── payload.py                           <-- Modul 80-Bit Frame + Reed-Solomon GF(2^8)
│   │   │   ├── layer1_visual.py                     <-- PyMuPDF Micro-Glyph & Spacing Modulator
│   │   │   ├── layer2_semantic.py                   <-- Kamus Jukminu TNI AD & FSM Retyping Decoder
│   │   │   ├── layer3_honeytoken.py                 <-- Dynamic Contextual Military Token Generator
│   │   │   ├── layer4_honeyrecord.py                <-- Database Sentinel & Synthetic Persona Injector
│   │   │   ├── vision_extractor.py                  <-- OpenCV Deskewing, Thresholding & OCR Pipeline
│   │   │   ├── claim_verifier.py                    <-- AI Leak Claim Verifier (Anti-Psywar Analyzer)
│   │   │   └── audit_ledger.py                      <-- SHA-256 Cryptographic Log Hash Chain
│   │   │
│   │   ├── models/                                  <-- Skema Validasi Pydantic & Model Data
│   │   │   ├── __init__.py
│   │   │   ├── request_models.py
│   │   │   └── response_models.py
│   │   │
│   │   └── storage/                                 <-- Repositori Berkas Uji Coba Luring
│   │       ├── master_templates/                    <-- Template Naskah Dinas Asli (PDF/DOCX)
│   │       ├── watermarked_outputs/                 <-- PDF Berstempel Forensik Siap Distribusi
│   │       └── test_leaks/                          <-- Sampel Uji (Foto HP Miring & Chat Dump)
│   │
│   ├── tests/                                       <-- Automated Unit Testing Modul Forensik
│   │   ├── test_payload.py
│   │   ├── test_layer1.py
│   │   └── test_layer2.py
│   │
│   ├── requirements.txt                             <-- Dependensi Terverifikasi (Air-Gapped Ready)
│   └── Dockerfile                                   <-- Container Deployment Mandiri
│
└── frontend/                                        <-- Lingkungan Next.js 14 / Tailwind CSS
    ├── src/
    │   ├── components/
    │   │   ├── TacticalNav.tsx                      <-- Header Pusat Operasi Pertahanan Siber (TOC)
    │   │   ├── DocumentWatermarker.tsx              <-- Modul Distribusi & Stempel Naskah Dinas
    │   │   ├── LeakInvestigationDrop.tsx            <-- Portal Drag-and-Drop Foto HP / Teks Bocoran
    │   │   ├── ForensicResultModal.tsx              <-- Tampilan Target Teridentifikasi & Confidence
    │   │   ├── PsywarVerifierPanel.tsx              <-- Analisis Hoax / Data Daur Ulang Forum Gelap
    │   │   └── AuditLedgerTable.tsx                 <-- Visualisasi Rantai Hash Log Pengadilan Militer
    │   │
    │   ├── lib/
    │   │   └── api.ts                               <-- API Client Penghubung ke Backend FastAPI
    │   │
    │   └── app/
    │       ├── layout.tsx
    │       └── page.tsx                             <-- Dashboard Taktis Terpadu
    │
    ├── public/                                      <-- Asset Taktis & Lambang Militer
    ├── package.json
    └── tailwind.config.js                           <-- Skema Warna Military Dark (High-Contrast)
```

---

# 4. RINCIAN TANGGUNG JAWAB MODUL CORE BACKEND

| Nama Berkas | Fungsi Utama | Dependensi Utama |
| :--- | :--- | :--- |
| `payload.py` | Mengonversi metadata (NRP, Waktu, Flags) menjadi 80-bit biner dan menambahkan paritas koreksi galat $GF(2^8)$. | `reedsolo`, `struct`, `hashlib` |
| `layer1_visual.py` | Memodifikasi matriks spasi kata dan pergeseran mikro glif pada berkas PDF tanpa mengubah tampilan mata telanjang. | `PyMuPDF` (`fitz`) |
| `layer2_semantic.py` | Memetakan bit payload ke variasi kosakata resmi Jukminu TNI AD dan merekonstruksi payload saat teks diketik ulang. | `regex`, `reedsolo` |
| `layer3_honeytoken.py` | Menghasilkan entitas data fiktif operasional (nomor registrasi logistik unik) berbobot Tardos Code. | `random`, `hashlib` |
| `layer4_honeyrecord.py` | Membuat baris data personel sintetis realistis (*tripwire*) untuk disuntikkan ke pangkalan data basis militer. | `faker` (lokal), `sqlite3` / `psycopg2` |
| `vision_extractor.py` | Meluruskan foto kertas miring (*perspective homography*), membersihkan noise, dan mengekstrak koordinat spasi via OCR. | `opencv-python` (`cv2`), `pytesseract` |
| `claim_verifier.py` | Mengukur derajat kesamaan semantik bukti kebocoran forum gelap untuk memvalidasi hoaks/psywar vs data otentik. | `sentence-transformers` (ringan/luring) |
| `audit_ledger.py` | Mengelola buku besar rantai hash SHA-256 yang merekam setiap siklus penerbitan dan investigasi forensik. | `hashlib`, `json` |

---

# 5. PRIORITAS LANGKAH EKSEKUSI BERIKUTNYA

Tim dapat memilih salah satu dari 3 prioritas pengerjaan lanjutan:

1. **Prioritas 1 (Core Backend Engine):**  
   Membangun dan menguji modul `payload.py` (80-bit frame + Reed-Solomon $GF(2^8)$) serta `layer2_semantic.py` (Kamus Jukminu TNI AD) agar uji coba ketik ulang (*retyping resilience test*) dapat langsung dieksekusi di terminal lokal.
2. **Prioritas 2 (Visual Engine & Vision Pipeline):**  
   Membangun modul `layer1_visual.py` (PyMuPDF spacing modulator) dan `vision_extractor.py` (OpenCV deskewing + OCR) untuk membuktikan ketahanan terhadap foto kamera ponsel.
3. **Prioritas 3 (Pitch Deck & Skenario Panggung):**  
   Menyusun draf 10 Slide Pitching berstandar militer dan naskah narasi demo berdurasi presisi 3 menit.

---
*Dokumen ini merupakan panduan kerja resmi tim dan disimpan sebagai aset teknis pendukung submisi Kartika Cyber Hackathon.*
