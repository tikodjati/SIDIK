#!/usr/bin/env bash
# Mematikan SIDIK. Data tetap tersimpan; jalankan mulai.sh lagi untuk melanjutkan.
cd "$(dirname "$0")"
docker compose -f juri/docker-compose.yml down
echo "SIDIK dimatikan. Data tetap tersimpan."
