# API Gateway Service

## Purpose

Container entrypoint for the SmartCito FastAPI gateway.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/api-gateway/Dockerfile -t smartcito-api-gateway .
docker run --rm -p 8000:8000 --env-file .env smartcito-api-gateway
```

## Example Usage

```bash
curl http://localhost:8000/api/v1/health/live
```
