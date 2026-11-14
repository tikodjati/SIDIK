"""Rakit folder siap-push untuk Hugging Face Space (web + API dalam satu container).

    python deploy/make_hf_space.py

Hasilnya `deploy/_hf_space_out/` (diabaikan git). Isinya hanya yang dibutuhkan container: backend
tanpa tes, frontend tanpa node_modules, template naskah demo, dan berkas deploy/hf/*. Tidak ada
berkas rahasia yang disalin (.env, kunci, database). Penjelasan paket: docs/DEPLOY.md."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy" / "_hf_space_out"

SKIP = shutil.ignore_patterns(
    "node_modules", ".next", "__pycache__", "*.pyc", ".venv", ".env*", "*.pem", "*.db",
    "*.tsbuildinfo", ".DS_Store", "favicon.ico",
)  # fmt: skip
# favicon.ico dikecualikan: Hugging Face dapat menolak push yang memuat berkas biner lewat git
# biasa (harus memakai Xet/LFS). Akibatnya hanya ikon tab browser; aplikasi tidak terpengaruh.


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=SKIP)


def write_lf(src: Path, dst: Path) -> None:
    """Salin berkas teks dengan akhir baris LF (start.sh tidak jalan di Linux bila CRLF)."""
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    dst.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    backend = OUT / "backend"
    backend.mkdir()
    for name in ("pyproject.toml", "alembic.ini"):
        shutil.copy(ROOT / "backend" / name, backend / name)
    for name in ("app", "alembic", "scripts"):
        copy_tree(ROOT / "backend" / name, backend / name)

    copy_tree(ROOT / "frontend", OUT / "frontend")

    templates = OUT / "data" / "master_templates"
    templates.mkdir(parents=True)
    shutil.copy(ROOT / "data" / "master_templates" / "naskah_demo.txt", templates)

    for name in ("Dockerfile", "README.md", "start.sh"):
        write_lf(ROOT / "deploy" / "hf" / name, OUT / name)

    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Siap: {OUT} ({files} berkas)")


if __name__ == "__main__":
    main()
