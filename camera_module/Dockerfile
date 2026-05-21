FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY camera_module/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY camera_module /app/camera_module

CMD ["uvicorn", "camera_module.service:app", "--host", "0.0.0.0", "--port", "8010"]
