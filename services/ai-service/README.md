# AI Service

## Purpose

Inference microservice for Orca model serving.

## Container Image

- Build file: `services/ai-service/Dockerfile`
- What the image does: runs the lightweight FastAPI AI microservice on port `8012` for split-service deployments.
- What ships in the image: `/srv/app.py`, the virtual environment, and this README at `/srv/README.md`.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/ai-service/Dockerfile -t orca-ai-service .
docker run --rm -p 8012:8012 orca-ai-service
```

## Example Usage

```bash
curl http://localhost:8012/models
```
