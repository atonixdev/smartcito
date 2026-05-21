FROM python:3.11-slim

WORKDIR /srv
COPY services/camera-service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/camera-service/app.py /srv/app.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]
