# Hasil Spike Lapis 1 (modulasi spasi antar-kata)

Tanggal: 2026-11-01. Kode: `backend/app/core/layer1_visual.py`, `vision_extractor.py`, `backend/scripts/spike_layer1.py`.
Ulangi dengan: `cd backend && python -m scripts.spike_layer1 --trials 10 --deltas 0.2 0.3 0.5`.

## Metode

- Template deterministik 56 baris × 13 kata (helvetica 10 pt). Satu bit = sepasang spasi bersebelahan: `(+δ, −δ)` untuk 1, `(−δ, +δ)` untuk 0. Lebar baris tetap.
- 336 slot per halaman memuat payload 104 bit (copy_id + paritas RS) ±3,2 kali; hasil ukur digabung (soft vote), lalu RS.
- Dekoder membandingkan spasi terukur dengan render referensi dari template yang sama (meniadakan bias bentuk huruf).
- Simulasi foto: perspektif (tilt 0°/35° + yaw/roll acak), bayangan kertas, blur σ=0,8 px, noise, JPEG q80, meja gelap. "Sisi-panjang" = panjang sisi kertas dalam piksel (3500 ≈ 300 dpi, 1200 ≈ 100 dpi).
- 10 percobaan per kondisi, copy_id acak.

## Hasil (pulih = payload terpulihkan benar; salah = payload keliru tanpa terdeteksi)

| δ (pt) | ideal | 3500 | 2400 | 1700 | 1200 (tilt 0 / 35°) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 0,2 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 / **7/10** |
| 0,3 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 / 10/10 |
| 0,5 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 / 10/10 |

Tilt 0° dan 35° sama pada kolom 3500–1700. Kasus "salah" = 0 di semua kondisi. BER per slot: δ=0,3 → 0,0–0,1% (≥2400 px), 1,5% (1700, 35°), 5,3% (1200, 35°).

## Kesimpulan

1. **Lapis 1 layak** pada simulasi foto, termasuk miring 35° dan foto ~1 MP. Rekomendasi awal δ = 0,3 pt (selisih 0,6 pt antar-pasangan spasi).
2. **Spesifikasi proposal tidak berlaku**: ±0,08–0,12 pt tidak diuji karena di bawah δ terendah yang kami coba (0,2 pt sudah mulai gagal pada foto 1 MP). Revisi angka di dokumen submisi.
3. Temuan penting: pendeteksian spasi dengan ambang mutlak gagal karena blur menyempitkan celah kata (hanya 1–29 dari 56 baris terukur). Solusi yang dipakai: ambil N celah terlebar per baris (N diketahui dari template), tolak baris bila celah kata/huruf tak terpisah jelas.

## Batasan (jangan diklaim di luar ini)

- **Simulasi, bukan foto HP asli.** Belum ada moiré layar, pantulan, fokus tidak rata, kertas melengkung/kusut.
- Dekoder mengetahui template (posisi baris, jumlah kata, referensi). Untuk tata letak dokumen lain perlu referensi per dokumen (tersedia karena dokumen dibuat dari template).
- Seluruh halaman terlihat; **crop** belum diuji.
- Kasat mata: δ=0,3–0,5 pt pada spasi 2,8 pt belum diuji persepsi manusia. Perlu uji buta tim (cetak/layar, 5 orang) sebelum klaim "tak terlihat".
- Teks rata kiri dengan jumlah kata per baris tetap; teks rata kanan-kiri (justify) belum didukung.

## Foto asli (2026-11-01): 7 foto via WhatsApp (960×1280 px), copy_id uji 0x51D1C0DE

**Hasil: 6 dari 7 foto berwatermark terbaca benar, dan 4 dari 4 foto kontrol ditolak** (`COCOK`, error slot 0–0,6%). Dekode buta; ID uji hanya dipakai untuk memeriksa hasil. Tidak pernah ada hasil `SALAH` atau tuduhan palsu pada kontrol.

| Foto | δ | Slot terbaca | Error slot | Hasil |
| :--- | :---: | :---: | :---: | :---: |
| dekat, tegak | 0,3 | 314/336 | 0,0% | COCOK |
| dekat, miring ~20° | 0,3 | 320/336 | 0,3% | COCOK |
| dekat, miring 35°, terputar | 0,3 | 331/336 | 0,6% | COCOK |
| jauh, miring 35° | 0,3 | 320/336 | 0,3% | COCOK |
| dekat, tegak | 0,5 | 328/336 | 0,0% | COCOK |
| dekat, miring 35°, terputar, ada tangan | 0,5 | 333/336 | 0,0% | COCOK |
| **jauh, miring 35°, landscape, tangan menutup sudut** | 0,5 | 2/336 | - | **GAGAL (ditolak)** |

### Foto kontrol (`kontrol_tanpa_modulasi.pdf`, tanpa watermark): 4 dari 4 ditolak

| Foto | Slot terbaca | Error slot vs ID uji | Hasil |
| :--- | :---: | :---: | :---: |
| dekat, tegak | 335/336 | 51,0% | GAGAL (ditolak) |
| sedang, tegak | 335/336 | 50,7% | GAGAL (ditolak) |
| sedang, tegak, kiri-kanan terpotong | 336/336 | 48,2% | GAGAL (ditolak) |
| jauh, miring 35° | 255/336 | 51,4% | GAGAL (ditolak) |

Ini penolakan yang bermakna: penyelarasan berhasil (skor baris 0,84–0,88, hampir semua slot terbaca), tetapi bit yang terbaca acak (error ±50% terhadap ID uji), sehingga Reed-Solomon menolak. Sistem tidak mengarang identitas dari dokumen tanpa watermark. Foto kontrol berukuran 720×1280 px.

Yang membuat berhasil (semua temuan dari foto asli):
1. **Registrasi kata berbasis template** (korelasi silang sub-piksel per kata ke render referensi; bit = pergeseran kata ganjil terhadap rata-rata dua tetangganya) menggantikan pengukuran tepi celah, yang tenggelam di noise/blur. Putaran pertama dengan metode lama: 0/4.
2. **Cetakan diperkecil ±94%** ("fit to page"): skala dan geseran baris dicari otomatis.
3. **Penyelarasan ke template**: tiga cara pelurusan awal (tepi kertas, deskew blok teks, persegi panjang minimum blok teks) × 4 rotasi × dengan/tanpa tahap affine awal, dipilih menurut korelasi ECC kasar; lalu ECC homografi; baris dilacak satu per satu; skala+geseran horizontal dicari per baris.

Kasus yang masih gagal: halaman kecil di bingkai (jauh), landscape, sudut kertas tertutup jari. Penyelarasan ke template tidak menemukan posisi yang cocok (skor baris 0,32), jadi sistem menolak, bukan menebak.

Batas lain: simulasi 1280 px dengan blur σ ≥ 1,6 px masih gagal; waktu proses ±1,5 menit per foto yang sulit (±25 detik untuk foto mudah), belum dioptimasi; foto dikompres WhatsApp, foto resolusi asli belum diuji.

## Langkah berikutnya

1. Foto asli: cetak/tampilkan PDF δ=0,3 dan 0,5, foto dengan HP tim (sudut, cahaya, jarak berbeda), jalankan ekstraktor; simpan di `data/test_leaks/`.
2. Uji crop (50–70% halaman) dan uji persepsi.
3. Setelah lulus: sambungkan ke endpoint `/watermark` dan `/intake`.
