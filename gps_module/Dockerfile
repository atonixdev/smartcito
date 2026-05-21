FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY gps_module/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY gps_module /app/gps_module

CMD ["uvicorn", "gps_module.service:app", "--host", "0.0.0.0", "--port", "8011"]
