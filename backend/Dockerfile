FROM python:3.12-slim

# Tesseract + data bahasa Indonesia untuk OCR offline
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ind \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[forensics]"
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

EXPOSE 8000
# Migrasi skema dan kunci ledger disiapkan sekali sebelum API menerima trafik (beberapa worker
# yang membuat kunci bersamaan akan menghasilkan kunci berbeda). Analisis foto berat di CPU:
# beberapa worker agar dua foto yang diunggah bersamaan tidak saling antre.
ENV SIDIK_WORKERS=2
CMD ["sh", "-c", "alembic upgrade head && python -c 'from app.core.audit_ledger import get_signer; get_signer()' && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${SIDIK_WORKERS}"]
