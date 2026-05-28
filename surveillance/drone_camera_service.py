"""
================================================================================
 File: surveillance/drone_camera_service.py
 Purpose:
   Drone Camera Ingestion Service. It registers drone video streams, normalizes
   frame metadata, and publishes frame/key-frame events for AI processing.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from orca_shared.crypto import build_integrity_record, build_secure_envelope

from surveillance.ai_client import ai_client
from surveillance.geospatial import resolve_zone
from surveillance.kafka import get_publisher
from surveillance.models import CameraDetection, CameraFeedStatus, CameraGimbalState, CameraStreamRegistration, FrameMetadata, NormalizedEvent, PublishEnvelope
from surveillance.topics import DRONE_CAMERA_ALERTS_TOPIC, DRONE_CAMERA_FRAMES_TOPIC


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

app = FastAPI(title="Orca Drone Camera Ingestion Service")
_streams: dict[str, CameraStreamRegistration] = {}
_latest_frames: dict[str, FrameMetadata] = {}
_latest_detections: dict[str, list[CameraDetection]] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "drone-camera-ingestion"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "service": "drone-camera-ingestion",
        "protocols": ["rtsp", "webrtc", "vendor"],
        "topics": {"frames": DRONE_CAMERA_FRAMES_TOPIC, "alerts": DRONE_CAMERA_ALERTS_TOPIC},
    }


@app.post("/streams/register")
async def register_stream(stream: CameraStreamRegistration) -> dict[str, object]:
    _streams[stream.drone_id] = stream
    preview_url = f"/streams/{stream.drone_id}/preview" if stream.preview_enabled else None
    return {
        "drone_id": stream.drone_id,
        "protocol": stream.protocol,
        "stream_url": stream.stream_url,
        "preview_url": preview_url,
        "status": "registered",
    }


@app.get("/streams")
async def list_streams() -> dict[str, list[dict[str, object]]]:
    return {"streams": [stream.model_dump(mode="json") for stream in _streams.values()]}


@app.get("/feeds", response_model=list[CameraFeedStatus])
async def feeds() -> list[CameraFeedStatus]:
    results: list[CameraFeedStatus] = []
    for drone_id, stream in _streams.items():
        frame = _latest_frames.get(drone_id)
        detections = _latest_detections.get(drone_id)
        results.append(
            CameraFeedStatus(
                drone_id=drone_id,
                stream_url=stream.stream_url,
                preview_url=f"/streams/{drone_id}/preview" if stream.preview_enabled else None,
                camera_id="rgb-main",
                ai_detections=detections if detections is not None else ([CameraDetection(label="surveillance-online", confidence=0.99)] if frame else []),
                gimbal=CameraGimbalState(
                    pitch_deg=0 if frame is None else -12,
                    yaw_deg=0,
                    zoom_level=1.0,
                ),
            )
        )
    return results


@app.post("/frames", response_model=PublishEnvelope)
async def ingest_frame(frame: FrameMetadata) -> PublishEnvelope:
    stream = _streams.get(frame.drone_id)
    if stream is None and frame.stream_url is None:
        raise HTTPException(status_code=404, detail="stream must be registered or frame.stream_url must be supplied")

    stream_url = frame.stream_url or (stream.stream_url if stream else None)
    position = frame.position or (stream.position if stream else None)
    preview_url = frame.preview_url or (f"/streams/{frame.drone_id}/preview" if stream and stream.preview_enabled else None)
    _latest_frames[frame.drone_id] = frame
    detection_result: dict[str, object] | None = None
    if frame.image_b64:
        try:
            detection_result = await ai_client.detect_objects(
                image_b64=frame.image_b64,
                backend=frame.ai_backend,
                labels=frame.ai_labels,
                threshold=frame.detection_threshold,
            )
            _latest_detections[frame.drone_id] = [
                CameraDetection(label=str(detection["label"]), confidence=float(detection["confidence"]))
                for detection in list(detection_result.get("detections", []))
            ]
        except Exception as exc:  # noqa: BLE001
            detection_result = {
                "backend": frame.ai_backend,
                "requested_backend": frame.ai_backend,
                "detections": [],
                "error": str(exc),
            }
            _latest_detections[frame.drone_id] = []
    frame_payload = {
        **frame.model_dump(mode="json", exclude={"image_b64", "ai_backend", "ai_labels", "detection_threshold"}),
        "stream_url": stream_url,
        "preview_url": preview_url,
        "coordinate_system": "WGS84",
        "zone": resolve_zone(position),
    }
    if detection_result is not None:
        frame_payload["ai_analysis"] = {
            "backend": detection_result.get("backend", frame.ai_backend),
            "requested_backend": detection_result.get("requested_backend", frame.ai_backend),
            "detection_count": len(list(detection_result.get("detections", []))),
            "detections": detection_result.get("detections", []),
            "error": detection_result.get("error"),
        }
    event = NormalizedEvent(
        event_type="drone.camera.frame",
        source="drone-camera-ingestion",
        entity_id=frame.drone_id,
        timestamp=frame.timestamp,
        topic=DRONE_CAMERA_FRAMES_TOPIC,
        payload={
            **frame_payload,
            "snapshot_integrity": build_integrity_record(frame_payload, signer_id=frame.drone_id),
            "security": build_secure_envelope(frame_payload, purpose="camera-frame", signer_id=frame.drone_id, associated=frame.frame_id),
        },
    )
    return PublishEnvelope(event=event, publish=get_publisher().publish_event(event))
