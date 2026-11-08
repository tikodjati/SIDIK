# Panduan Uji Lapis 2 (variasi frasa / ketik ulang)

Tujuan: mencoba sendiri apakah identitas salinan bisa dibaca dari teks yang **diketik ulang** sebagian, dan memastikan sistem **menolak** (bukan menuduh) bila bukti kurang. Tidak butuh printer atau foto.

## 0. Persiapan (sekali saja)

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
```

Semua perintah di bawah dijalankan dari folder `backend`.

## 1. Buat dua salinan naskah

```bash
python -m scripts.layer2_cli watermark 1001 -o salinan_1001.txt
python -m scripts.layer2_cli watermark 1002 -o salinan_1002.txt
```

Buka kedua berkas. Isinya sama, tetapi puluhan kata berbeda (mis. "Berdasarkan" vs "Merujuk", "serta" vs "beserta"). Itulah penanda: tiap kata varian mengodekan 1–2 bit dari ID salinan.

(Pernah ingin lewat Swagger? Jalankan `python -m uvicorn app.main:app --reload`, buka http://localhost:8000/docs, login dulu lewat `POST /api/v1/auth/login` sebagai admin, lalu pakai `POST /api/v1/layer2/watermark` dan `/extract`.)

## 2. Skenario uji

Untuk tiap skenario: siapkan berkas teks `bukti.txt`, lalu jalankan

```bash
python -m scripts.layer2_cli extract bukti.txt
```

| # | Skenario | Cara membuat `bukti.txt` | Hasil yang diharapkan |
| :---: | :---: | :--- | :--- |
| 1 | Salinan utuh | Salin seluruh `salinan_1001.txt` | TERIDENTIFIKASI: 1001 |
| 2 | Potongan besar | Salin dari atas sekitar 70% isi | TERIDENTIFIKASI: 1001 |
| 3 | Diketik ulang | Ketik ulang sebagian di Notepad/Telegram, ubah huruf besar/kecil dan tanda baca | TERIDENTIFIKASI: 1001 |
| 4 | Ganti kata biasa | Pada skenario 3, ganti beberapa kata biasa (bukan kata varian) | Tetap terbaca bila potongan cukup besar |
| 5 | Potongan pendek | Salin hanya satu paragraf | BUKTI TIDAK CUKUP |
| 6 | Teks bebas | Tulis teks apa saja | BUKTI TIDAK CUKUP |
| 7 | Salinan lain | Salin `salinan_1002.txt` | TERIDENTIFIKASI: 1002 (bukan 1001) |
| 8 | Campuran dua salinan | Gabungkan separuh `salinan_1001` dan separuh `salinan_1002` | Biasanya ditolak; yang penting **tidak** menuduh ID asing |

Catatan: skenario 8 belum ditangani khusus (anti-kolusi Tardos ada di Lapis 3). Jangan diklaim sebagai fitur.

## 3. Yang perlu dicatat dan dilaporkan

Salin tabel ini ke chat tim:

| Skenario | Hasil (TERIDENTIFIKASI / DITOLAK) | ID benar? | Bit terbaca | Catatan |
| :--- | :--- | :---: | :---: | :--- |
| | | | | |

**Wajib dilaporkan segera** bila ada hasil **TERIDENTIFIKASI dengan ID yang salah** (mis. memberi 1002 padahal bukti dari 1001). Itu cacat serius.

Hal lain yang berguna:
- Potongan terkecil (kira-kira berapa persen teks) yang masih terbaca.
- Kata biasa mana yang bila diganti membuat hasil gagal.
- Kalimat pada naskah yang terasa janggal sebagai bahasa naskah dinas (bahan perbaikan kamus).

## 4. Perkiraan batas (template demo: 105 bit)

- Potongan teks ≥ 60% dari atas: biasanya terbaca.
- Potongan ≤ 40%: ditolak (kapasitas template kurang). Menambah kapasitas butuh kamus variasi baru, bukan perubahan kode.
- Kata varian pendek (≤ 5 huruf, mis. "agar", "guna") harus persis; kata panjang tahan typo ringan.

## 5. Coba mengubah kamus (untuk PM / ahli Jukminu)

Berkas: `data/master_templates/naskah_demo.txt`.

- Sintaks: `{varian1|varian2}` = 1 bit, `{v1|v2|v3|v4}` = 2 bit.
- Tiap varian **satu kata**, unik di seluruh naskah, tidak boleh muncul di teks tetap, dan tidak boleh mirip kata lain.
- Validasi otomatis saat dimuat; kesalahan muncul sebagai pesan yang menunjuk kata bermasalah. Coba:

```bash
python -c "from app.core.layer2_semantic import load_template; t = load_template('../data/master_templates/naskah_demo.txt'); print(len(t.slots), 'slot,', t.capacity_bits, 'bit')"
```

- Target kapasitas bila ingin tahan potongan 30–40%: sekitar 210–315 bit (170–260 slot 1-bit). Detail di `docs/HASIL_LAPIS2.md`.
- **Penting:** kamus saat ini hanya padanan kata umum, bukan variasi resmi Jukminu. Ganti dengan variasi yang sah menurut Perkasad sebelum dipakai di dokumen submisi.

## 6. Mengulang simulasi otomatis

```bash
python -m scripts.simulate_retype --trials 100
```

Kolom "benar / salah": kolom salah harus selalu 0.
