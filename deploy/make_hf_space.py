"""Rakit folder siap-push untuk Hugging Face Space (web + API dalam satu container).

    python deploy/make_hf_space.py

Hasilnya `deploy/_hf_space_out/` (diabaikan git). Isinya hanya yang dibutuhkan container: backend
tanpa tes, frontend tanpa node_modules, template naskah demo, dan berkas deploy/hf/*. Tidak ada
berkas rahasia yang disalin (.env, kunci, database). Penjelasan paket: docs/DEPLOY.md.

`assemble()` juga dipakai deploy/make_juri_package.py untuk paket juri."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy" / "_hf_space_out"

_SKIP_COMMON = (
    "node_modules", ".next", "__pycache__", "*.pyc", ".venv", ".env*", "*.pem", "*.db",
    "*.tsbuildinfo", ".DS_Store",
)  # fmt: skip


def _ignore(hf: bool):
    # favicon.ico dikecualikan untuk Hugging Face: push berkas biner lewat git biasa dapat ditolak
    # (harus memakai Xet/LFS). Akibatnya hanya ikon tab browser; aplikasi tidak terpengaruh.
    return shutil.ignore_patterns(*_SKIP_COMMON, *(("favicon.ico",) if hf else ()))


def write_lf(src: Path, dst: Path) -> None:
    """Salin berkas teks dengan akhir baris LF (skrip .sh tidak jalan di Linux bila CRLF)."""
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    dst.write_text(text, encoding="utf-8", newline="\n")


def assemble(out: Path, *, hf: bool = True) -> None:
    """Susun isi image (backend, frontend, template, Dockerfile, start.sh) ke `out`.

    hf=True menambah README.md berformat Hugging Face dan melewati favicon.ico."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    ignore = _ignore(hf)

    backend = out / "backend"
    backend.mkdir()
    for name in ("pyproject.toml", "alembic.ini"):
        shutil.copy(ROOT / "backend" / name, backend / name)
    for name in ("app", "alembic", "scripts"):
        shutil.copytree(ROOT / "backend" / name, backend / name, ignore=ignore)

    shutil.copytree(ROOT / "frontend", out / "frontend", ignore=ignore)

    templates = out / "data" / "master_templates"
    templates.mkdir(parents=True)
    shutil.copy(ROOT / "data" / "master_templates" / "naskah_demo.txt", templates)

    # Dockerfile merujuk deploy/hf/start.sh, sama seperti saat dibangun dari akar repo.
    (out / "deploy" / "hf").mkdir(parents=True)
    write_lf(ROOT / "deploy" / "hf" / "start.sh", out / "deploy" / "hf" / "start.sh")
    for name in ("Dockerfile", *(("README.md",) if hf else ())):
        write_lf(ROOT / "deploy" / "hf" / name, out / name)


def main() -> None:
    assemble(OUT)
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Siap: {OUT} ({files} berkas)")


if __name__ == "__main__":
    main()
