# Autentikasi dan RBAC

Kode: `backend/app/core/auth.py`, `backend/app/api/{deps,auth,users}.py`, `backend/scripts/users.py`, `frontend/src/components/AuthProvider.tsx`. Test: `backend/tests/test_auth_rbac.py`.

## Matriks peran

| Tindakan | admin | distributor | investigator |
| :--- | :---: | :---: | :---: |
| Kelola penerima, naskah, terbitkan salinan | ya | ya | - |
| Analisis bukti (`/intake/text`, `/layer2/extract`) | ya | - | ya |
| Baca dan verifikasi ledger | ya | - | ya |
| Kelola pengguna | ya | - | - |
| Teks salinan (`/copies/{id}/text`), `/layer2/watermark` | ya | - | - |
| Lihat akun sendiri, ganti sandi, keluar | ya | ya | ya |

Pemisahan yang disengaja: distributor tidak bisa membaca ledger, karena isinya memuat riwayat investigasi. Investigator tidak bisa melihat daftar salinan; ia hanya mendapat identitas lewat hasil analisis. `/layer2/watermark` dibatasi admin karena bisa membuat teks dengan ID apa pun, yang berarti bisa memalsukan bukti.

**Penegakan ada di server.** Menu dan halaman di frontend hanya menyesuaikan tampilan. `test_auth_rbac.py` membaca semua rute dari skema OpenAPI: rute baru otomatis gagal test sampai dicantumkan di matriks atau di daftar publik. Rute publik hanya `/health` dan `/auth/login` (ditambah `/docs` dan `/openapi.json` bawaan FastAPI; matikan di lingkungan nyata).

## Membuat akun

Tidak ada akun bawaan. Akun pertama dibuat dari baris perintah:

```bash
docker compose exec api python -m scripts.users create --username admin --full-name "Nama Admin" --role admin
```

Untuk demo, satu akun per peran dengan sandi acak:

```bash
docker compose exec api python -m scripts.users seed-demo
```

Kredensialnya ditulis ke `data/keys/demo_users.txt` (diabaikan git). Jangan dipakai di lingkungan nyata. Akun berikutnya bisa dibuat admin lewat halaman **Pengguna**. Pengguna sebaiknya segera mengganti sandi awal di halaman **Akun**, supaya admin tak lagi mengetahuinya.

## Cara kerja

- **Sandi:** scrypt (`N=2^15, r=8, p=1`) dari pustaka standar Python, jadi tanpa dependensi baru. Parameter tersimpan di hash, sehingga biayanya bisa dinaikkan nanti. Panjang minimal 10 karakter.
- **Sesi:** token acak 256-bit di cookie `HttpOnly` + `SameSite=Strict`, berlaku 8 jam (`SIDIK_SESSION_HOURS`). Yang disimpan di DB hanya hash SHA-256-nya, jadi bocornya tabel sesi tidak memberi sesi yang bisa dipakai. Keluar, ganti sandi, dan nonaktifkan akun langsung mencabut sesi di server.
- **Salah sandi:** pesan dan waktu respons sama untuk semua sebab, sehingga keberadaan akun tak bisa ditebak. Setelah 5 kali gagal, akun terkunci 15 menit.
- **Ledger:** pelaku diambil dari pengguna yang login (`X-Actor` dihapus karena bisa dipalsukan). Peristiwa baru: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `PASSWORD_CHANGED`, `USER_CREATED`, `USER_ACTIVATED`, `USER_DEACTIVATED`. Saat akun terkunci tak ada entri baru, jadi serangan tebak sandi tak bisa membanjiri ledger. Tebakan ke nama pengguna yang tidak ada juga tak dicatat.

## Pengaturan untuk produksi

| Variabel | Catatan |
| :--- | :--- |
| `SIDIK_COOKIE_SECURE=true` | **Wajib** saat dilayani lewat HTTPS. Default `false` hanya untuk `http://localhost`. |
| `SIDIK_CORS_ORIGINS` | Asal frontend yang diizinkan. |

Frontend dan API harus berada di situs yang sama (mis. `localhost:3000` dan `localhost:8000`). Membuka lewat `127.0.0.1` sementara API di `localhost` dihitung beda situs: cookie tidak terkirim dan login tampak gagal.

## Batasan

- **Admin tetap sangat berkuasa.** Admin bisa membuat akun dan membaca semua data, walau semua tindakannya tercatat di ledger. Otorisasi ganda dan HSM dari proposal masih roadmap.
- **Penguncian akun bisa disalahgunakan:** siapa pun yang tahu nama pengguna bisa mengunci akun itu selama 15 menit. Belum ada pembatasan per alamat IP.
- **Belum ada:** reset sandi oleh admin (pengguna yang lupa sandi perlu akun baru), MFA, kebijakan kerumitan sandi, dan pengubahan peran.
- `/docs` masih publik; skema API terlihat tanpa login.
- Kunci tanda tangan ledger belum dilindungi perangkat keras.
