# GPS Service

## Purpose

GPS stream normalization microservice.

## Container Image

- Build file: `services/gps-service/Dockerfile`
- What the image does: runs the lightweight FastAPI GPS microservice on port `8011` for standards lookup and payload normalization.
- What ships in the image: `/srv/app.py`, the virtual environment, and this README at `/srv/README.md`.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/gps-service/Dockerfile -t orca-gps-service .
docker run --rm -p 8011:8011 orca-gps-service
```

## Example Usage

```bash
curl http://localhost:8011/standards
```
