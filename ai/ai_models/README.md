# AI Models

Computer vision, local LLM inference, and predictive analytics models for SmartCito.

This service now supports multiple inference modes:

- Numeric anomaly scoring through `/infer` for existing SmartCito callers.
- Remote Llama Stack-backed text generation through `/models` and `/generate`.
- Local Hugging Face inference using a base foundation model.
- Local LoRA or LoRA-merged inference for SmartCito Model adapters.

It also includes structured operator workflows for:

- `POST /classify_alert` to label alerts by category and severity.
- `POST /summarize_event` to build short command-center summaries.
- `POST /detect_objects` to run object detection through an `auto`, `opencv`, `yolo`, or heuristic backend behind one stable endpoint.

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

## Text Generation Backends

`POST /generate` accepts backend selection fields so the same API can be used in local development, Kaggle notebooks, or remote runtime environments:

- `backend="remote"` or `backend="llama-stack"` for an OpenAI-compatible remote runtime.
- `backend="local"` for base-model local inference.
- `backend="local-lora"` for base model + adapter inference without merging.
- `backend="merged-local"` for base model + adapter inference with `merge_and_unload()`.

Additional fields:

- `adapter_path` for an explicit LoRA adapter directory.
- `merge_lora` to force merged-local behavior.

## Llama Stack Integration

The AI service can proxy text generation to a running Llama Stack or OGX
server through its OpenAI-compatible `/v1` API.

Set these environment variables for the `ai_models` service:

- `LLAMA_STACK_BASE_URL` — base URL of your running stack, for example `http://host.docker.internal:8321` or `http://127.0.0.1:8321/v1`
- `LLAMA_STACK_MODEL` — default model id exposed by the stack
- `LLAMA_STACK_API_KEY` — optional API key if your stack requires one
- `LLAMA_STACK_TIMEOUT_SECONDS` — optional HTTP timeout, default `30`

## Local Hugging Face and LoRA Integration

Set these environment variables for local SmartCito Model inference:

- `SMARTCITO_BASE_MODEL_ID` — your chosen compatible foundation model id from an official provider source
- `SMARTCITO_LORA_ADAPTER_PATH` — path to `output/smartcito-lora/`
- `SMARTCITO_LLM_BACKEND` — `auto`, `local`, `local-lora`, `merged-local`, or `remote`
- `SMARTCITO_LOAD_IN_4BIT` — `true` to load a 4-bit quantized local model
- `SMARTCITO_DEVICE_MAP` — optional device map, default `auto`
- `HUGGINGFACE_HUB_TOKEN` or `HF_TOKEN` — optional gated model access token

Example request for LoRA-merged inference:

```bash
curl -X POST http://localhost:8012/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt":"Analyze drone telemetry for anomalies.",
    "backend":"merged-local",
    "model":"your-foundation-model-id",
    "adapter_path":"./output/smartcito-lora",
    "merge_lora":true,
    "temperature":0.1,
    "max_tokens":160
  }'
```

## Training and Kaggle Flow

SmartCito ships a full adapter-training path for community contribution:

- [training/prepare_dataset.py](training/prepare_dataset.py) normalizes contributor data.
- [training/lora_training.py](training/lora_training.py) runs standard LoRA fine-tuning.
- [training/qlora_training.py](training/qlora_training.py) runs QLoRA fine-tuning.
- [training/dataset_format.md](training/dataset_format.md) documents the dataset schema.
- [examples/smartcito_training_demo.ipynb](examples/smartcito_training_demo.ipynb) is the Kaggle training notebook.
- [examples/smartcito_inference_demo.ipynb](examples/smartcito_inference_demo.ipynb) is the Kaggle inference notebook.

Only adapter weights from `output/smartcito-lora/` should be shared.

The `llama-stack` package is a server/runtime CLI and currently exposes
`llama stack ...` subcommands, not `llama model ...`.

Do not use `llama stack run starter` here unless you intentionally want the
full starter distribution. In current releases that config enables many
providers, including `together`, so it fails fast unless extra optional
packages are installed.

Use a minimal passthrough stack instead when you only need an OpenAI-compatible
front door for one backend:

```bash
pip install llama-stack -U
export PASSTHROUGH_URL=http://127.0.0.1:11434
venv/bin/llama stack run ai_models/llama-stack-passthrough.yaml
```

`PASSTHROUGH_URL` can point to any OpenAI-compatible backend, such as:

- Ollama at `http://127.0.0.1:11434`
- vLLM at `http://127.0.0.1:8000`
- another local or remote OpenAI-compatible gateway

If the downstream backend requires a bearer token, also set:

```bash
export PASSTHROUGH_API_KEY=your-token
```

This Kaggle bundle does not include LLaMA-3 weights. It only ships SmartCito code, LoRA or QLoRA adapters, and synthetic or sovereign datasets. Users must obtain any compatible base model from official provider sources.

Once your Llama Stack server is running and exposes an OpenAI-compatible API,
the SmartCito AI service provides:

- `GET /models` — lists model ids from the configured stack
- `POST /generate` — sends chat-completions style requests to the configured stack
- `POST /classify_alert` — classifies operational alerts into categories like intrusion or fire
- `POST /summarize_event` — turns structured alert context into an operator-facing summary
- `POST /detect_objects` — performs object-region detection from an image payload and can auto-select YOLO, OpenCV, or the built-in fallback detector

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

Example `docker run` with Llama Stack integration:

```bash
docker run --rm -p 8012:8012 \
  -e LLAMA_STACK_BASE_URL=http://host.docker.internal:8321 \
  -e LLAMA_STACK_MODEL=Llama-4-Maverick \
  smartcito-ai-models
```

## Example Usage

```bash
curl -X POST http://localhost:8012/infer \
  -H 'Content-Type: application/json' \
  -d '{"features":[0.2,0.4,0.8]}'
```

```bash
curl -X POST http://localhost:8012/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Summarize camera alerts in one sentence."}'
```

```bash
curl -X POST http://localhost:8012/classify_alert \
  -H 'Content-Type: application/json' \
  -d '{"message":"Unauthorized person detected near gate 4","source":"camera-4","tags":["perimeter"],"anomaly_score":0.72}'
```

```bash
curl -X POST http://localhost:8012/summarize_event \
  -H 'Content-Type: application/json' \
  -d '{"title":"North Gate Alert","classification":"intrusion","severity":"high","location":"North Gate","alerts":["Unauthorized person detected"],"sensor_readings":{"motion_score":0.91}}'
```

```bash
curl -X POST http://localhost:8012/detect_objects \
  -H 'Content-Type: application/json' \
  -d '{"image_b64":"<base64-png>","backend":"auto","labels":["vehicle"],"threshold":0.55}'
```

`backend="auto"` tries YOLO first when `ultralytics` and a YOLO model are available, then OpenCV when `cv2` is installed, and finally falls back to the built-in detector. You can pin `backend` to `opencv` or `yolo` to require that backend explicitly.
