# Camera Service

## Purpose

Video ingestion microservice for camera protocols and stream validation.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/camera-service/Dockerfile -t smartcito-camera-service .
docker run --rm -p 8010:8010 smartcito-camera-service
```

## Example Usage

```bash
curl http://localhost:8010/capabilities
```
