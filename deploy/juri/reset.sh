#!/usr/bin/env bash
# Mematikan SIDIK dan MENGHAPUS semua datanya (akun, salinan, audit trail, bahan uji), supaya
# jalan berikutnya mulai bersih. Image hasil build tidak dihapus.
cd "$(dirname "$0")"
read -r -p "Semua data SIDIK akan dihapus. Lanjut? (ketik ya): " jawab
if [ "$jawab" != "ya" ]; then echo "Dibatalkan."; exit 0; fi
docker compose -f juri/docker-compose.yml down -v
rm -rf bahan_uji
echo "Data dihapus. Jalankan mulai.sh untuk mulai bersih."
