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

EXPOSE 8000
# Migrasi skema dijalankan sebelum API menerima trafik.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
