FROM python:3.11-slim

WORKDIR /app
COPY ai_models/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY ai_models /app/ai_models

CMD ["uvicorn", "ai_models.inference:app", "--host", "0.0.0.0", "--port", "8012"]
