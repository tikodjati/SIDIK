FROM python:3.12-slim

# Tesseract + data bahasa Indonesia untuk OCR offline
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ind \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[forensics]"
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
