FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/venv \
    PATH=/app/venv/bin:$PATH \
    PYTHONPATH=/app

WORKDIR /app

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/venv \
    PATH=/app/venv/bin:$PATH \
    PYTHONPATH=/app

WORKDIR /app
RUN python -m venv "$VIRTUAL_ENV"
COPY air/surveillance/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY air/surveillance /app/surveillance
COPY orca_shared /app/orca_shared
COPY orca_shared /app/smartcito_shared

FROM runtime
COPY --from=builder /app /app

USER 10001
CMD ["uvicorn", "surveillance.drone_gateway_service:app", "--host", "0.0.0.0", "--port", "8020"]
