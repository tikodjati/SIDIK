# Panduan Uji Foto Asli (Lapis 1)

Tujuan: mengukur apakah payload terbaca dari foto HP sungguhan. Hasilnya menentukan klaim di dokumen submisi.

## 1. Siapkan PDF uji

Pasang dependensi forensik sekali saja (PyMuPDF, OpenCV, NumPy; tidak ikut instalasi biasa):

```bash
cd backend
pip install -e ".[forensics]"
```

Lalu buat PDF:

```bash
python -m scripts.make_test_pages
```

Menghasilkan di `data/watermarked_outputs/uji_foto/`:
- `uji_d0.3.pdf` dan `uji_d0.5.pdf` (dimodulasi, copy_id uji `0x51D1C0DE`)
- `kontrol_tanpa_modulasi.pdf` (tanpa watermark; harus **ditolak** sistem)

## 2. Cetak

- Kertas A4, **skala 100% / "Actual size"**. Jangan "Fit to page" dan jangan "Shrink to fit": posisi baris dipakai dekoder.
- Hitam-putih/grayscale, kualitas normal. Cetak masing-masing PDF minimal 1 lembar.
- Uji tambahan (opsional): tampilkan PDF di layar monitor 100%, lalu foto layar.

## 3. Foto dengan HP

Contoh tampilan sudut: [contoh_sudut_foto.jpg](contoh_sudut_foto.jpg) (simulasi; foto asli akan terlihat berbeda).

Sudut = seberapa miring HP terhadap kertas. 0° = HP tepat di atas kertas, menghadap lurus ke bawah. 20° = HP dimiringkan sedikit, sisi kertas yang jauh tampak sedikit menyempit. 35° = jelas miring, sisi jauh tampak jauh lebih sempit.

**Per PDF dimodulasi (`uji_d0.3`, `uji_d0.5`): 18 foto**

| Kelompok | Variasi | Jumlah |
| :--- | :--- | :---: |
| A. Inti | sudut {0°, 20°, 35°} × jarak {dekat, sedang, jauh}, lampu ruangan, meja gelap | 9 |
| B. Cahaya jendela | sudut {0°, 20°, 35°}, jarak sedang, meja gelap | 3 |
| C. Bayangan tangan | sudut {0°, 20°, 35°}, jarak sedang, bayangan jatuh di sebagian kertas | 3 |
| D. Meja terang | sudut {0°, 20°, 35°}, jarak sedang, alas meja kayu/putih (paling sulit) | 3 |

**Lembar kontrol (`kontrol_tanpa_modulasi`): 4 foto**: sudut {0°, 35°} × jarak {dekat, sedang}, lampu ruangan.

Total: 2 × 18 + 4 = **40 foto**. Jarak: dekat = halaman memenuhi layar HP, sedang = halaman ±75%, jauh = halaman ±50%.

Aturan agar ekstraktor bisa menemukan kertas:
- **Keempat sudut kertas harus terlihat** dalam foto (uji crop dilakukan terpisah).
- Kertas lebih terang daripada meja.
- Fokus tajam (ketuk layar pada teks), tanpa mode potret/beauty. Flash dimatikan.
- Rotasi foto tidak masalah (0/90/180/270 dicoba otomatis).

## 4. Penamaan berkas

Nama berkas memuat δ: `uji_d0.3_dekat_miring35.jpg`, `uji_d0.5_jauh_terang.jpg`. Foto kontrol: `kontrol_d0.3_...jpg`. Taruh semua di `data/test_leaks/` (tidak ikut git).

## 5. Jalankan ekstraksi

```bash
cd backend
python -m scripts.extract_photo ../data/test_leaks/*.jpg --out ../data/test_leaks/lurus
```

Keluaran per foto: jumlah baris terukur, `slot-BER`, dan hasil:
- `COCOK`: payload benar terpulihkan.
- `GAGAL (bukti tidak cukup...)`: ditolak, tidak menebak. Untuk foto **kontrol** ini adalah hasil yang benar.
- `SALAH (id berbeda)`: payload keliru tanpa terdeteksi. **Harus dilaporkan**, ini cacat serius.
- `kertas tidak ditemukan`: kertas tak terdeteksi; cek `--out` dan kontras kertas-meja.

## 6. Catat hasil

Salin keluaran ke tabel (δ, jarak, sudut, cahaya, hasil) dan kirim ke tim. Kriteria lulus spike (dari `KEPUTUSAN_ARSITEKTUR.md`): payload terpulihkan pada ≥ 80% foto uji yang memenuhi aturan di atas, tanpa satu pun `SALAH`.

## 7. Uji persepsi (terpisah)

Letakkan `kontrol_tanpa_modulasi.pdf` dan `uji_d0.3.pdf` cetak berdampingan; minta 5 orang yang tidak tahu tujuannya menunjuk lembar yang "terlihat berbeda". Ulangi untuk δ 0,5. Jika hasilnya tebakan acak, klaim "tak kasat mata" untuk δ tersebut boleh dipakai.
