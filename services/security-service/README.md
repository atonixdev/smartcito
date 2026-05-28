# Security Service

## Purpose

Encryption and IAM helper microservice.

## Container Image

- Build file: `services/security-service/Dockerfile`
- What the image does: runs the lightweight FastAPI security microservice on port `8013` for control inspection and encryption helper endpoints.
- What ships in the image: `/srv/app.py`, the virtual environment, and this README at `/srv/README.md`.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/security-service/Dockerfile -t orca-security-service .
docker run --rm -p 8013:8013 orca-security-service
```

## Example Usage

```bash
curl http://localhost:8013/controls
```
