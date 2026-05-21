# AI Service

## Purpose

Inference microservice for SmartCito model serving.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/ai-service/Dockerfile -t smartcito-ai-service .
docker run --rm -p 8012:8012 smartcito-ai-service
```

## Example Usage

```bash
curl http://localhost:8012/models
```
