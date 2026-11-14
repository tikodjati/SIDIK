# SIDIK versi juri untuk Hugging Face Spaces (Docker): web Next.js dan API FastAPI dalam satu
# container, satu URL. Next meneruskan /api/* ke API di 127.0.0.1:8000 (rewrite), jadi browser hanya
# bicara ke satu domain dan cookie sesi SameSite=Strict tetap terkirim.

# --- tahap 1: bangun frontend ---
FROM node:22-slim AS web
RUN corepack enable
WORKDIR /web
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
# Kedua nilai ini ditanam saat build: "/" = API satu domain, BACKEND_URL = tujuan rewrite.
ENV NEXT_PUBLIC_API_URL=/ \
    BACKEND_URL=http://127.0.0.1:8000 \
    NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# --- tahap 2: runtime (Python + biner Node dari tahap 1) ---
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node

# Hugging Face menjalankan container sebagai user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user
WORKDIR /home/user/app

COPY --chown=user backend/pyproject.toml backend/
RUN pip install --no-cache-dir --user ./backend
ENV PATH=/home/user/.local/bin:$PATH

COPY --chown=user backend/app backend/app
COPY --chown=user backend/alembic.ini backend/alembic.ini
COPY --chown=user backend/alembic backend/alembic
COPY --chown=user backend/scripts backend/scripts
COPY --chown=user data/master_templates data/master_templates
COPY --from=web --chown=user /web web
COPY --chown=user start.sh start.sh

ENV SIDIK_DATA_DIR=/home/user/app/data \
    SIDIK_COOKIE_SECURE=true \
    SIDIK_SIGNING_KEY_AUTOCREATE=false \
    SIDIK_WORKERS=2 \
    PORT=7860
EXPOSE 7860
CMD ["bash", "start.sh"]
