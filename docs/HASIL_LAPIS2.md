# Lapis 2 (semantik): desain dan hasil simulasi

Kode: `backend/app/core/layer2_semantic.py`, `backend/app/api/layer2.py`, template `data/master_templates/naskah_demo.txt`.
Simulasi: `cd backend && python -m scripts.simulate_retype --trials 100` (opsi `--synthetic-slots N`).

## Desain

- Template naskah memuat grup varian `{a|b}` (1 bit) atau `{a|b|c|d}` (2 bit). PM/ahli Jukminu dapat menambah atau mengganti grup tanpa mengubah kode.
- Bit payload (frame `copy_id` + Reed-Solomon yang sama dengan Lapis 1: 13 byte = 104 bit) dipetakan berurutan ke slot; frame berulang bila slot lebih banyak.
- **Dekoder tidak menyejajarkan posisi.** Tiap varian berupa satu kata yang unik di seluruh naskah; cukup dicari kemunculannya pada teks bukti (fuzzy ringan untuk kata ≥ 6 huruf). Karena itu potongan sebagian, urutan berubah, huruf besar/kecil, spasi, dan tanda baca tidak berpengaruh. Slot yang tidak ditemukan menjadi erasure.
- **Validator otomatis saat template dimuat**: varian satu kata, 2 atau 4 varian per grup, tidak muncul di teks tetap, tidak dipakai ganda, dan tidak semirip kata lain (kemiripan ≥ 86) supaya tak tertukar saat fuzzy.
- Keluaran skor bit memakai `payload.decode_scores`, yang juga dipakai Lapis 1, sehingga bukti kedua lapis dapat digabung (belum dibangun).

## Kebijakan zero false-accusation (temuan penting)

Simulasi awal memberi hasil **`SALAH` (ID keliru)** pada kasus sinonim tertukar (6 dari 100 pada potongan 50%): Reed-Solomon yang dipakai sampai batas kapasitas dapat salah-koreksi ke kata sandi lain. Perbaikan: `decode_scores` menyisakan 2 simbol paritas untuk deteksi dan menolak bila `2E + S > nsym − 2`. Setelah itu **0 hasil `SALAH` di seluruh simulasi**, dengan harga toleransi potongan yang lebih kecil.

## Hasil simulasi (template demo: 87 slot, 105 bit; 100 percobaan/sel; sel = persen benar / jumlah salah)

| Potongan | Bersih | Typo 2% | Typo 5% | Kata diganti 10% | Kata diganti 20% | Sinonim tertukar 5% |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 100% | 100/0 | 100/0 | 49/0 | 57/0 | 10/0 | 44/0 |
| 80% | 100/0 | 96/0 | 25/0 | 35/0 | 0/0 | 28/0 |
| 60% | 100/0 | 52/0 | 4/0 | 5/0 | 0/0 | 13/0 |
| 50% | 63/0 | 13/0 | 0/0 | 4/0 | 0/0 | 5/0 |
| 40% | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |

Di bawah ±50% potongan teks, template demo tidak cukup. **Penyebab: kapasitas 105 bit hanyalah 1× frame.** Template sintetis (kata acak 8 huruf) menunjukkan skalanya:

| Kapasitas | Potongan terkecil yang masih 100% (bersih) | Potongan 40%, typo 2% |
| :---: | :---: | :---: |
| 105 bit (demo) | 60% | 0% |
| 210 bit | 30% | 35% |
| 315 bit | 30% | 95% |

Kata sintetis lebih panjang daripada kosakata nyata, jadi angka typo pada tabel kedua optimistis.

## Implikasi untuk proposal dan tugas PM

1. Klaim proposal "tahan selama menyalin ≥ 35% dokumen" **belum tercapai** dengan template demo; syaratnya sekitar 2–3× kapasitas (≥ 210–315 bit, yaitu 170–260 slot 1-bit per naskah) **dengan kamus yang sah menurut Perkasad**. Itu pekerjaan PM/ahli Jukminu, bukan kode.
2. Kamus di `naskah_demo.txt` adalah padanan leksikal umum (ditandai BELUM DIVALIDASI). Jangan diklaim sebagai variasi resmi Jukminu.
3. Naskah demo bukan Tata Naskah Dinas sungguhan; hanya untuk menguji mesin.
4. Belum ada: registri `copy_id` di DB (endpoint hanya stateless), penggabungan bukti Lapis 1+2, dan Lapis 3 (honey-token / Tardos).
