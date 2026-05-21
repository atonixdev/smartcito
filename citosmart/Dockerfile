# ============================================================================
# File: backend/Dockerfile
# Purpose:
#   Multi-stage container build for the SmartCito FastAPI service.
#   Stage 1 installs dependencies in a slim base; stage 2 produces a
#   minimal, non-root runtime image.
#
# Build:
#   docker build -t smartcito-backend ./backend
#
# Run (standalone, requires env vars):
#   docker run --rm -p 8000:8000 --env-file ../.env smartcito-backend
# ============================================================================

# ---- Stage 1: builder ------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# System deps required by some wheels (e.g., bcrypt, asyncpg).
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"

# Non-root user for least-privilege execution.
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app
COPY --from=builder /install /usr/local
COPY . /app

USER app

EXPOSE 8000

# Healthcheck pings the liveness endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; \
    sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
