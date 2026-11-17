"""Rakit paket SIDIK untuk juri (zip yang bisa dijalankan dengan satu perintah).

    python deploy/make_juri_package.py                 # SIDIK-juri.zip (build online)
    python deploy/make_juri_package.py --with-image    # + SIDIK-juri-offline.zip (image siap pakai)

Hasilnya di deploy/_juri_out/ (diabaikan git). Isinya seluruh berkas proyek menurut git (tracked
dan belum-tracked yang tidak diabaikan, jadi tidak ada .env, kunci, atau node_modules), ditambah
skrip peluncur, compose khusus juri, panduan, dan video demo bila ada. Commit dulu perubahanmu:
berkas yang diubah tetapi belum di-commit ikut dibawa apa adanya dan akan diperingatkan."""

import argparse
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy" / "_juri_out"
NAME = "SIDIK-juri"
TEMPLATES = ROOT / "deploy" / "juri"
IMAGE = "sidik-juri:latest"
LF_SUFFIXES = {".sh", ".yml", ".yaml"}


def git(*args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "core.quotepath=off", "-C", str(ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )  # fmt: skip
    return done.stdout


def project_files() -> list[str]:
    listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({p for p in listed.split("\0") if p and (ROOT / p).is_file()})


def put(src: Path, dst: Path, *, eol: str | None = None) -> None:
    """Salin berkas; bila `eol` diberikan dan berkas teks, seragamkan akhir barisnya."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if eol is None:
        shutil.copy2(src, dst)
        return
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    dst.write_text(text, encoding="utf-8", newline="\n" if eol == "lf" else "\r\n")


def stage(include_video: bool) -> Path:
    root = OUT / NAME
    if OUT.exists():
        shutil.rmtree(OUT)
    root.mkdir(parents=True)

    for rel in project_files():
        src, name = ROOT / rel, Path(rel).name
        is_script = Path(rel).suffix in LF_SUFFIXES or name.startswith("Dockerfile")
        put(src, root / rel, eol="lf" if is_script else None)

    # Peluncur dan konfigurasi khusus juri.
    for name in ("mulai.sh", "berhenti.sh", "reset.sh"):
        put(TEMPLATES / name, root / name, eol="lf")
    for name in ("mulai.cmd", "berhenti.cmd", "reset.cmd"):
        put(TEMPLATES / name, root / name, eol="crlf")  # cmd.exe butuh CRLF agar `goto` andal
    put(TEMPLATES / "docker-compose.yml", root / "juri" / "docker-compose.yml", eol="lf")
    put(TEMPLATES / "dockerignore", root / ".dockerignore", eol="lf")
    put(TEMPLATES / "MULAI-DI-SINI.md", root / "MULAI-DI-SINI.md")

    commit = git("rev-parse", "--short", "HEAD").strip()
    (root / "VERSI.txt").write_text(f"SIDIK paket juri\ncommit {commit}\n{date.today()}\n")

    video = ROOT / "video" / "out"
    if include_video and (video / "sidik-demo.mp4").exists():
        for name in ("sidik-demo.mp4", "sidik-demo.srt"):
            if (video / name).exists():
                put(video / name, root / "video_demo" / name)
    elif include_video:
        print("Peringatan: video/out/sidik-demo.mp4 tidak ada, paket dibuat tanpa video.")
    return root


def make_zip(root: Path, zip_path: Path, extra: dict[str, Path] | None = None) -> None:
    files = [(p, p.relative_to(root.parent).as_posix()) for p in sorted(root.rglob("*"))
             if p.is_file()]  # fmt: skip
    files += [(src, f"{NAME}/{arc}") for arc, src in (extra or {}).items()]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files:
            info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3  # Unix, supaya izin eksekusi terbawa
            executable = arc.endswith(".sh")
            info.external_attr = (0o755 if executable else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with src.open("rb") as fh, zf.open(info, "w", force_zip64=True) as out:
                shutil.copyfileobj(fh, out, 1 << 20)


def build_image_tar(root: Path) -> Path:
    print("Membangun image (beberapa menit)...")
    subprocess.run(["docker", "build", "-t", IMAGE, "-f", "deploy/hf/Dockerfile", "."],
                   cwd=root, check=True)  # fmt: skip
    target = OUT / "sidik-image.tar.gz"
    print("Menyimpan image (docker save + gzip)...")
    import gzip

    with gzip.open(target, "wb", compresslevel=6) as gz:
        proc = subprocess.Popen(["docker", "save", IMAGE], stdout=subprocess.PIPE)
        assert proc.stdout is not None
        shutil.copyfileobj(proc.stdout, gz, 1 << 20)
        if proc.wait() != 0:
            sys.exit("docker save gagal")
    return target


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-image", action="store_true", help="buat juga paket offline")
    ap.add_argument("--no-video", action="store_true", help="jangan sertakan video demo")
    args = ap.parse_args()

    dirty = [ln for ln in git("status", "--porcelain").splitlines() if ln.strip()]
    if dirty:
        print(f"Peringatan: {len(dirty)} berkas belum di-commit ikut dibawa apa adanya:")
        for ln in dirty[:8]:
            print("  ", ln)

    root = stage(include_video=not args.no_video)
    plain = OUT / f"{NAME}.zip"
    make_zip(root, plain)
    print(f"Siap: {plain} ({plain.stat().st_size / 1e6:.1f} MB)")

    if args.with_image:
        tar = build_image_tar(root)
        offline = OUT / f"{NAME}-offline.zip"
        make_zip(root, offline, {"sidik-image.tar.gz": tar})
        print(f"Siap: {offline} ({offline.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
