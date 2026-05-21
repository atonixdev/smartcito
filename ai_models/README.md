# AI Models

Computer vision and predictive analytics models for SmartCito.

## Scope

- Object detection, classification, and tracking on CCTV/drone feeds
- Facial recognition (subject to deployment policy and consent)
- Anomaly detection on sensor and traffic streams
- Forecasting (traffic, environmental, asset utilisation)

## Layout

```
ai_models/
├── Dockerfile       # Container image for inference service
├── requirements.txt # Runtime dependencies
├── model.py         # Lightweight scoring model
├── inference.py     # FastAPI inference service
└── README.md
```

## Conventions

- Frameworks: **PyTorch** and **TensorFlow** are both supported.
- Each model lives in its own subfolder with:
  - `model.py` — architecture / wrapper
  - `inference.py` — load + predict entry point
  - `README.md` — purpose, inputs, outputs, metrics, license of weights
- Pre-trained weights are **not** committed. Provide a download script or
  point to a model registry (S3, HuggingFace, MLflow).
- Use type hints and PEP8.

## Integration

Inference services are exposed to the backend through the ingestion layer or
via a dedicated REST/gRPC microservice. Metadata (events, alerts, scores) is
written to the database — **raw video is never stored**.

## Tests

Add accuracy + smoke tests under [`../tests/ai_models/`](../tests/).

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn
- Model scoring helpers compatible with TensorFlow / PyTorch expansion

## How To Run Its Container

```bash
docker build -f ai_models/Dockerfile -t smartcito-ai-models .
docker run --rm -p 8012:8012 smartcito-ai-models
```

## Example Usage

```bash
curl -X POST http://localhost:8012/infer \
  -H 'Content-Type: application/json' \
  -d '{"features":[0.2,0.4,0.8]}'
```
