# Camera Module

CCTV and drone feed processing for SmartCito.

## Capabilities

- RTSP / ONVIF / WebRTC ingestion via **OpenCV** and GStreamer
- Frame extraction, decoding, and pre-processing
- Hook points for AI inference (see [`../ai_models/`](../ai_models/))
- Event + alert publishing to the backend (no raw video persistence)

## Layout

```
camera_module/
├── Dockerfile        # Container image for the camera-domain API
├── requirements.txt  # Python runtime dependencies
├── service.py        # FastAPI camera-domain service
├── drivers/         # Vendor and protocol drivers (ONVIF, RTSP, custom)
└── README.md
```

## Conventions

- Use OpenCV for video ingestion and basic CV ops.
- Prefer ONVIF for interoperable camera control and RTSP for stream transport.
- Use TensorFlow / PyTorch models (loaded from `ai_models/`) for detection.
- Persist **metadata only** (timestamps, bounding boxes, labels, alert IDs)
  in the database. Raw video must be streamed or short-buffered, never
  archived without an explicit retention policy.
- Secure feeds with **TLS** end-to-end and apply IAM policies on every
  stream endpoint.
- All operators accessing live streams must satisfy MFA and the
  `cameras:stream` RBAC rule from
  [`../security/rbac/policies.yaml`](../security/rbac/policies.yaml).
- Encryption standards follow
  [`../security/crypto/STANDARDS.md`](../security/crypto/STANDARDS.md).
- Contributor-facing standardization guidance lives in
  [`../hardware/camera_module/`](../hardware/camera_module/).

## Privacy

Any face / biometric processing requires:
- documented legal basis and consent model,
- redaction/blurring options enabled by default,
- audit logs of every model inference.

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn
- ONVIF / RTSP protocol helpers

## How To Run Its Container

```bash
docker build -f camera_module/Dockerfile -t smartcito-camera-module .
docker run --rm -p 8010:8010 smartcito-camera-module
```

## Example Usage

```bash
curl http://localhost:8010/drivers
curl -X POST http://localhost:8010/probe \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"cam-1","host":"camera.local","path":"/stream/main"}'
```
