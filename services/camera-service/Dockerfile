FROM cgr.dev/chainguard/python:latest@sha256:e4ec7051aae87617182379ef05c33ad757fbed85e804c5e07e9a2d1778042ae5 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/srv/venv \
	PATH=/srv/venv/bin:$PATH

WORKDIR /srv

FROM cgr.dev/chainguard/python:latest-dev@sha256:5b542358ae4f8a121f9b81661c449a83ad23a587a7d5fe2a530d7b3771b2dc5e AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/srv/venv \
	PATH=/srv/venv/bin:$PATH

WORKDIR /srv
RUN python -m venv "$VIRTUAL_ENV"
COPY services/camera-service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/camera-service/app.py /srv/app.py

FROM runtime
COPY --from=builder /srv /srv

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]
