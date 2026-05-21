FROM python:3.11-slim

WORKDIR /app
COPY hardware/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY hardware /app/hardware

CMD ["uvicorn", "hardware.service:app", "--host", "0.0.0.0", "--port", "8014"]
