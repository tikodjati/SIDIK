# Hasil Lapis 3: Honey-Token Anti-Kolusi

## Cara kerja

1. **Template**: naskah memuat 6 angka fiktif yang realistis, ditulis `[[pola]]` di
   `data/master_templates/naskah_demo.txt`. Setiap `#` diganti digit acak, misalnya
   `[[1##.###]]` menjadi `143.275`. Keenam token itu adalah frekuensi, nomor registrasi
   alpalhankam, blok arsip, kanal komunikasi, prosedur pemusnahan, dan koordinat.
2. **Penerbitan salinan**: nilai token diacak (`secrets`) lalu disimpan di tabel `honey_tokens`.
   - Digit tiap token unik secara global, jadi satu angka menunjuk tepat satu salinan.
   - Nilai token tidak bisa diturunkan dari `copy_id`, jadi tidak bisa ditebak.
   - Tidak ada kunci rahasia tambahan. Seluruh tim yang memakai database bersama bisa mendeteksi.
3. **Tata letak tidak berubah**: semua digit di font naskah selebar sama (5.28 pt), sehingga Lapis 1
   dan 2 tidak terpengaruh. Naskah tetap 56 baris dan muat satu halaman.
4. **Deteksi dari teks** (ketik ulang atau parafrase): semua angka di teks bukti diambil digitnya saja,
   sehingga `143.275`, `143,275`, dan `143275` dianggap sama, lalu dicocokkan ke registri.
5. **Deteksi dari foto** (tanpa OCR):
   - Posisi kata ber-token diketahui dari tata letak.
   - Tiap digit acak dicocokkan bentuknya ke angka 0–9.
   - Token dengan satu digit saja yang ragu tidak dipakai.

## Aturan atribusi (nol salah tuduh)

| Bukti untuk satu salinan | Hasil |
| :--- | :--- |
| ≥ 2 token cocok | Teridentifikasi |
| 1 token + Lapis 1/2 menunjuk salinan yang sama | Teridentifikasi |
| 1 token saja | Hanya **indikasi**, tanpa tuduhan |
| ≥ 2 salinan masing-masing cukup bukti | `COLLUSION_SUSPECTED`: semua salinan ditampilkan |

Kalau Lapis 1 dan Lapis 2 menunjuk salinan yang berbeda, status `CONFLICTING_EVIDENCE` tetap
berlaku seperti sebelumnya.

## Hasil uji (otomatis, `backend/tests/test_layer3.py`)

- Parafrase total yang tetap mengutip 2 angka fakta: **teridentifikasi**.
- Satu token saja: hanya indikasi, status `INSUFFICIENT_FORENSIC_ARTIFACTS`.
- Kolusi 2 salinan, masing-masing menyumbang 3 token: **kedua salinan teridentifikasi**, dan
  penerima lain yang tidak terlibat tidak ikut tertuduh.
- Angka acak atau angka resmi naskah (nomor KEP, jam) tidak cocok dengan token mana pun.

**Foto kamera simulasi** (8 foto: miring 0–35°, blur, JPEG):
- 38 dari 48 token terbaca, **0 salah baca**.
- Foto beresolusi rendah (sisi 1600 px) hanya membaca 0–2 token karena digitnya terlalu kecil.
  Token yang tidak terbaca dilewati, tidak ditebak.

## Batasan (tulis apa adanya di dokumen lomba)

1. **Sanitasi angka**: kalau pelaku membuang atau mengganti semua angka, token hilang (GAP 3 di proposal).
2. **Mudah dikenali saat dibandingkan**: pelaku yang membandingkan dua salinan akan melihat angkanya
   berbeda dan bisa membuangnya, dengan risiko kehilangan informasi intelijennya.
3. **Kolusi lebih dari 3 orang**: dengan 6 token, tiap pelaku rata-rata menyumbang kurang dari 2 token,
   sehingga sebagian pelaku hanya muncul sebagai indikasi.
4. **Bukan kode Tardos**: kode Tardos biner butuh sekitar 230 bit untuk 2 pelaku, sedangkan slot
   naskah sudah dipakai frame Reed-Solomon. Tardos dicatat sebagai roadmap. Ganti klaim "Tardos
   c≥5, p<10⁻⁶" di proposal dengan "honey-token unik per penerima, anti-kolusi c=2–3".
5. **Salinan lama**: salinan yang terbit sebelum Lapis 3 mendapat token saat PDF atau teksnya
   diunduh ulang. Salinan yang sudah beredar sebelumnya tidak memuat token.

## Pemasangan

Ada migrasi baru `0003` (tabel `honey_tokens`). Container `api` menjalankan `alembic upgrade head`
saat start, jadi cukup:

```bash
docker compose up --build -d api
```

Tanpa Docker, jalankan `alembic upgrade head` dari folder `backend`. Pada database bersama (Neon),
migrasi cukup dijalankan sekali oleh satu orang.
