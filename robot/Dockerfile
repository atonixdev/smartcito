FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/app/venv \
	PATH=/app/venv/bin:$PATH \
	PYTHONPATH=/app

WORKDIR /app

RUN python -m venv "$VIRTUAL_ENV"

RUN pip install --no-cache-dir "jax[cpu]>=0.4.30" fastapi==0.115.2 uvicorn[standard]==0.32.0 pydantic==2.13.4 "numpy>=2.0"

COPY gpuops /app/gpuops
COPY robot /app/robot

ENTRYPOINT ["uvicorn", "robot.service:app", "--host", "0.0.0.0", "--port", "8016"]