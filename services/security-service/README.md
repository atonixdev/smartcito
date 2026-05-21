# Security Service

## Purpose

Encryption and IAM helper microservice.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/security-service/Dockerfile -t smartcito-security-service .
docker run --rm -p 8013:8013 smartcito-security-service
```

## Example Usage

```bash
curl http://localhost:8013/controls
```
