# GPS Service

## Purpose

GPS stream normalization microservice.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn

## How To Run Its Container

```bash
docker build -f services/gps-service/Dockerfile -t smartcito-gps-service .
docker run --rm -p 8011:8011 smartcito-gps-service
```

## Example Usage

```bash
curl http://localhost:8011/standards
```
