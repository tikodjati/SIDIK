# SIDIK

Sistem Identifikasi Dokumen dan Investigasi Kebocoran - Kartika Cyber Hackathon (Defensive Shield).

Dokumen: [proposal](Documents/PROPOSAL_DAN_SPESIFIKASI_SIDIK.md) · [strategi](Documents/STRATEGI_PENILAIAN_DAN_BLUEPRINT_SKENARIO_A.md) · [keputusan arsitektur](docs/KEPUTUSAN_ARSITEKTUR.md)

## Struktur

```
backend/    FastAPI (Python 3.12) - mesin forensik di app/core
frontend/   Next.js + Tailwind - dashboard taktis
data/       master_templates (di-commit), watermarked_outputs & test_leaks (lokal)
docs/       keputusan arsitektur, openapi.json
```

## Menjalankan

Semua layanan (API, web, Postgres, Tesseract):

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000/docs · Web: http://localhost:3000

Pengembangan lokal tanpa Docker:

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]" && .venv/Scripts/pytest
cd frontend && pnpm install && pnpm dev
```

Kontrak API: setelah mengubah endpoint, jalankan `cd backend && python -m scripts.export_openapi`, lalu `cd frontend && pnpm gen:api`.

## Alur tim

`main` dilindungi; satu fitur = satu branch + PR; commit konvensional (`feat:`, `fix:`, `docs:`). CI menjalankan lint + test + build.
