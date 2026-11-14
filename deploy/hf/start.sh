#!/bin/bash
# Menyalakan API (internal, port 8000) dan web (publik, $PORT). Bila salah satu berhenti,
# container ikut berhenti supaya Hugging Face menyalakannya ulang.
set -e

cd "$HOME/app/backend"
# Skema database dan kunci ledger disiapkan sekali, sebelum worker API menerima trafik.
alembic upgrade head
python -c 'from app.core.audit_ledger import get_signer; get_signer()'

uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers "${SIDIK_WORKERS:-2}" &

cd "$HOME/app/web"
node node_modules/next/dist/bin/next start -H 0.0.0.0 -p "${PORT:-7860}" &

wait -n
exit $?
