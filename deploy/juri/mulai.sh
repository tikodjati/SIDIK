#!/usr/bin/env bash
# SIDIK untuk juri (Linux/macOS): satu perintah menyalakan sistem, mengisi data demo, dan
# menyiapkan bahan uji. Aman dijalankan berulang kali.
set -euo pipefail
cd "$(dirname "$0")"
export SIDIK_PORT="${SIDIK_PORT:-3000}"
export MSYS_NO_PATHCONV=1 # Git Bash di Windows tidak boleh mengubah path di dalam container
COMPOSE=(docker compose -f juri/docker-compose.yml)

trap 'echo; echo "GAGAL. Lihat bagian Pemecahan Masalah di docs/PANDUAN_JURI.md."; echo "Log aplikasi: ${COMPOSE[*]} logs app"' ERR

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker belum terpasang. Pasang Docker Desktop (https://www.docker.com/products/docker-desktop/) lalu jalankan ulang."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker terpasang tetapi belum berjalan. Buka Docker Desktop, tunggu sampai siap, lalu jalankan ulang."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Perlu Docker Compose v2 (perintah 'docker compose'). Perbarui Docker Desktop."
  exit 1
fi

if [ -f sidik-image.tar.gz ] && ! docker image inspect sidik-juri:latest >/dev/null 2>&1; then
  echo "Memuat image siap pakai (sekali saja, beberapa menit)..."
  docker load -i sidik-image.tar.gz
fi

echo "Menyalakan SIDIK. Tanpa paket offline, jalan pertama membangun image dan butuh internet (sekitar 5-15 menit)."
"${COMPOSE[@]}" up -d --wait

echo "Menyiapkan akun dan data demo..."
"${COMPOSE[@]}" exec -T -w /home/user/app/backend app python -m scripts.demo_juri
mkdir -p bahan_uji
"${COMPOSE[@]}" cp app:/home/user/app/data/bahan_uji/. bahan_uji/

echo
echo "SIDIK siap: http://localhost:${SIDIK_PORT}"
echo "Akun dan langkah uji: MULAI-DI-SINI.md. Bahan uji: folder bahan_uji/"
if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:${SIDIK_PORT}" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then open "http://localhost:${SIDIK_PORT}" || true
fi
