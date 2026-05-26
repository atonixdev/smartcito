FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/app/venv \
	PATH=/app/venv/bin:$PATH

WORKDIR /app

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/app/venv \
	PATH=/app/venv/bin:$PATH

WORKDIR /app
RUN python -m venv "$VIRTUAL_ENV"
COPY ai/ai_models/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY ai /app/ai

FROM runtime
COPY --from=builder /app /app

ENTRYPOINT ["uvicorn", "ai.ai_models.inference:app", "--host", "0.0.0.0", "--port", "8012"]
