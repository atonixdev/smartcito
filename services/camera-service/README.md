# Camera Service

## Purpose

Video ingestion microservice for camera protocols and stream validation.

## Container Image

- Build file: `services/camera-service/Dockerfile`
- What the image does: runs the lightweight FastAPI camera microservice on port `8010` for capability reporting and stream validation.
- What ships in the image: `/srv/app.py`, the virtual environment, and this README at `/srv/README.md`.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/camera-service/Dockerfile -t orca-camera-service .
docker run --rm -p 8010:8010 orca-camera-service
```

## Example Usage

```bash
curl http://localhost:8010/capabilities
```
