FROM python:3.11-slim

WORKDIR /app
COPY citosmart/requirements.txt /tmp/runtime-requirements.txt
RUN pip install --no-cache-dir -r /tmp/runtime-requirements.txt
COPY citosmart /app
COPY security /app/security

CMD ["uvicorn", "security.service:app", "--host", "0.0.0.0", "--port", "8013"]
