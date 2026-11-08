# SIDIK

Sistem Identifikasi Dokumen dan Investigasi Kebocoran - Kartika Cyber Hackathon (Defensive Shield).

Dokumen: [proposal](Documents/PROPOSAL_DAN_SPESIFIKASI_SIDIK.md) · [strategi](Documents/STRATEGI_PENILAIAN_DAN_BLUEPRINT_SKENARIO_A.md) · [keputusan arsitektur](docs/KEPUTUSAN_ARSITEKTUR.md)

## Struktur

```
backend/    FastAPI (Python 3.12/3.13) - mesin forensik di app/core
frontend/   Next.js + Tailwind - dashboard taktis
data/       master_templates (di-commit), watermarked_outputs & test_leaks (lokal)
docs/       keputusan arsitektur, openapi.json
```

## Menjalankan

**Panduan lengkap (dengan atau tanpa Docker, akun, alur uji, masalah umum): [docs/PANDUAN_MENJALANKAN.md](docs/PANDUAN_MENJALANKAN.md).**

Ringkas, dengan Docker:

```bash
docker compose up --build -d
docker compose exec api python -m scripts.users seed-demo   # sekali; sandi di data/keys/demo_users.txt
```

Web: http://localhost:3000 · API: http://localhost:8000/docs · Peran dan akun: [docs/AUTENTIKASI_RBAC.md](docs/AUTENTIKASI_RBAC.md)

Kontrak API: setelah mengubah endpoint, jalankan `cd backend && python -m scripts.export_openapi`, lalu `cd frontend && pnpm gen:api`.

## Alur tim

`main` dilindungi; satu fitur = satu branch + PR; commit konvensional (`feat:`, `fix:`, `docs:`). CI menjalankan lint + test + build.
