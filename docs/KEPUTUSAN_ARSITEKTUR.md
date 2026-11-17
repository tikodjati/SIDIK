# Keputusan Arsitektur & Revisi Proposal

Hasil review proposal awal terhadap best practice. Keputusan ditetapkan tim pada inisiasi proyek.

## Keputusan

| Topik | Keputusan | Alasan singkat |
| :--- | :--- | :--- |
| Ingest dokumen | Template terstruktur (data → PDF/DOCX). Upload PDF bebas = stretch goal | Posisi kata dan slot semantik terkontrol penuh; stabil untuk demo |
| Payload | `copy_id` 32 bit + flags 4 bit + paritas RS(nsym=8), diulang di banyak slot. NRP/satuan/waktu dicari lewat DB | Lebih tahan galat, NRP tidak tertanam di dokumen (`backend/app/core/payload.py`) |
| Bahasa/runtime | Python 3.12 saja (Go dihapus) | Tim 3 orang, 14 hari; throughput dijawab dengan benchmark |
| Database | PostgreSQL 16 biasa (tanpa TimescaleDB), SQLAlchemy 2 + Alembic | Timescale tidak dipakai fitur apa pun |
| OCR | Tesseract 5 + `ind.traineddata` (Surya tidak dipakai) | Ringan, offline; Lapis 1 tidak bergantung OCR |
| Claim verifier | Honey-record match (deterministik) utama; embedding pendukung, model dibundel di image | Dapat dibela secara hukum, tetap air-gapped |
| Audit trail | Hash chain linier SHA-256 + tanda tangan Ed25519; endpoint verifikasi rantai. HSM = roadmap | Sesuai klaim yang bisa dibuktikan |
| Frontend | Next.js 16 + TypeScript + Tailwind v4, font sistem (tanpa Google Fonts), pnpm | Air-gapped |
| API | OpenAPI-first: `backend/scripts/export_openapi.py` → `docs/openapi.json` → `pnpm gen:api` | Frontend dan backend paralel |
| Auth | RBAC minimal: distributor / investigator / admin | Produk keamanan |

## Revisi klaim proposal (harus dikoreksi di dokumen submisi)

1. **Lapis 1**: spasi ±0.08–0.12 pt tidak terbaca andal dari foto HP. Ganti ke modulasi diferensial redundan (besar 0.3–0.6 pt, diulang banyak baris, deteksi statistik langsung dari citra). Ditentukan oleh spike di bawah.
2. **Payload 80 bit / paritas 24 bit**: hanya memulihkan 1 byte salah. Diganti desain `copy_id` di atas (4 byte salah atau 8 byte hilang per frame).
3. **Tardos c≥5, p<10⁻⁶, "ortogonal"**: tidak realistis pada kode pendek. Turunkan ke c=2–3 pada Lapis 3 dengan simulasi; hapus kata "ortogonal".
4. **Akurasi ">99.8%"**: ganti dengan angka hasil benchmark otomatis.
5. **Zero-width space sebagai jangkar homografi**: tidak tertangkap kamera. Pakai fiducial visual samar di sudut; ZWSP hanya kanal teks tambahan.

## Spike Hari 1 (kriteria lulus)

Render PDF template dengan modulasi Lapis 1 → cetak/tampilkan → foto HP miring (~35°) → ekstraksi. Ukur bit error rate pada ≥ 20 foto uji (cahaya/sudut berbeda).

- Lulus jika payload terpulihkan pada ≥ 80% foto uji setelah koreksi RS.
- Tidak lulus: perbesar amplitudo/redundansi, atau demo Lapis 1 dibatasi ke screenshot/scan dan foto HP ditangani Lapis 2–3. Klaim proposal disesuaikan dengan hasil.
