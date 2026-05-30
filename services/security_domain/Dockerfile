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
COPY orcaapi/requirements.txt /tmp/runtime-requirements.txt
RUN pip install --no-cache-dir -r /tmp/runtime-requirements.txt
COPY orcaapi /app
COPY services/security_domain /app/security

FROM runtime
COPY --from=builder /app /app

USER 10001
ENTRYPOINT ["uvicorn", "security.service:app", "--host", "0.0.0.0", "--port", "8013"]
