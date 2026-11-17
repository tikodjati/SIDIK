#!/usr/bin/env bash
# SIDIK untuk juri (Linux/macOS): satu perintah menyalakan sistem, mengisi data demo, dan
# menyiapkan bahan uji. Aman dijalankan berulang kali.
set -euo pipefail
cd "$(dirname "$0")"
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

# Port: dipakai yang diminta (SIDIK_PORT), atau port stack ini yang sudah jalan, atau yang pertama kosong.
if [ -z "${SIDIK_PORT:-}" ]; then
  SIDIK_PORT="$("${COMPOSE[@]}" port app 7860 2>/dev/null | sed 's/.*://' || true)"
  if [ -z "$SIDIK_PORT" ]; then
    for p in 3000 3001 3002 3300 3301 8080; do
      if ! (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then SIDIK_PORT=$p; break; fi
    done
  fi
  SIDIK_PORT="${SIDIK_PORT:-3000}"
fi
export SIDIK_PORT

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
