"""
================================================================================
 File: ai_models/model.py
 Purpose:
   Tiny scoring model used as a placeholder for real SmartCito inference.
================================================================================
"""

from __future__ import annotations

import base64
import importlib
import os
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO

from PIL import Image


@dataclass(frozen=True, slots=True)
class ObjectDetection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]
    area_ratio: float


@dataclass(frozen=True, slots=True)
class AlertClassification:
    category: str
    severity: str
    confidence: float
    recommended_action: str
    requires_human_review: bool


_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fire", ("fire", "smoke", "burn", "heat", "flammable")),
    ("intrusion", ("intrusion", "trespass", "unauthorized", "breach", "perimeter")),
    ("vehicle", ("vehicle", "car", "truck", "plate", "traffic", "collision")),
    ("human", ("person", "human", "crowd", "pedestrian", "face")),
    ("drone", ("drone", "uav", "airspace", "flight path")),
    ("environmental", ("gas", "chemical", "radiation", "flood", "weather", "wind")),
    ("infrastructure", ("vibration", "power", "network", "camera offline", "tamper")),
)

_SEVERITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "critical": ("critical", "immediate", "weapon", "explosion", "down", "emergency"),
    "high": ("high", "alarm", "pursuit", "panic", "injury", "unsafe"),
    "medium": ("warning", "anomaly", "suspicious", "delay", "offline"),
}


def _match_category(text: str) -> tuple[str, int]:
    best_category = "general"
    best_hits = 0
    for category, keywords in _CATEGORY_RULES:
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits > best_hits:
            best_category = category
            best_hits = hits
    return best_category, best_hits


def _match_severity(text: str, anomaly_score: float | None) -> str:
    for severity, keywords in _SEVERITY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return severity

    if anomaly_score is not None:
        if anomaly_score >= 0.85:
            return "critical"
        if anomaly_score >= 0.65:
            return "high"
        if anomaly_score >= 0.35:
            return "medium"

    return "low"


def _recommended_action(category: str, severity: str) -> str:
    if category == "fire":
        return "Dispatch nearest response team and verify evacuation routes."
    if category == "intrusion":
        return "Lock the affected perimeter zone and route live video to an operator."
    if category == "vehicle":
        return "Track the vehicle across adjacent cameras and notify traffic operators."
    if category == "drone":
        return "Review airspace telemetry and confirm whether the flight is authorized."
    if severity in {"critical", "high"}:
        return "Escalate to mission control and request operator acknowledgement."
    return "Log the alert, continue monitoring, and enrich with nearby sensor context."


def score_anomaly(features: list[float]) -> float:
    """Return a simple bounded score for demo and smoke-test purposes."""
    if not features:
        return 0.0
    score = sum(abs(value) for value in features) / len(features)
    return round(min(score, 1.0), 4)


def classify_alert(
    message: str,
    *,
    source: str | None = None,
    tags: list[str] | None = None,
    anomaly_score: float | None = None,
) -> AlertClassification:
    """Classify a SmartCito alert into an operational category and severity."""
    normalized_tags = tags or []
    combined_text = " ".join(part for part in [source or "", message, *normalized_tags] if part).lower()

    category, category_hits = _match_category(combined_text)
    severity = _match_severity(combined_text, anomaly_score)
    base_confidence = 0.4 if category == "general" else 0.6
    confidence = min(base_confidence + (category_hits * 0.1), 0.95)
    if anomaly_score is not None:
        confidence = min(max(confidence, anomaly_score), 0.98)

    return AlertClassification(
        category=category,
        severity=severity,
        confidence=round(confidence, 2),
        recommended_action=_recommended_action(category, severity),
        requires_human_review=severity in {"critical", "high"},
    )


def summarize_event(
    *,
    title: str | None,
    classification: str | None,
    severity: str | None,
    location: str | None,
    alerts: list[str],
    sensor_readings: dict[str, float] | None,
    max_sentences: int,
) -> str:
    """Build a short operator-facing summary from structured alert context."""
    headline_parts = []
    if title:
        headline_parts.append(title.strip())
    elif classification:
        headline_parts.append(f"{classification.title()} event")
    else:
        headline_parts.append("Operational event")

    if severity:
        headline_parts.append(f"({severity.lower()} severity)")
    if location:
        headline_parts.append(f"at {location}")

    sentences = [" ".join(headline_parts).strip() + "."]

    if alerts:
        alert_clause = "; ".join(alert.strip() for alert in alerts[:2] if alert.strip())
        if alert_clause:
            sentences.append(f"Primary signals: {alert_clause}.")

    if sensor_readings:
        formatted = ", ".join(f"{key}={value:.2f}" for key, value in list(sensor_readings.items())[:3])
        if formatted:
            sentences.append(f"Key readings: {formatted}.")

    return " ".join(sentences[:max_sentences])


def _decode_image(image_b64: str) -> Image.Image:
    raw_bytes = base64.b64decode(image_b64)
    return Image.open(BytesIO(raw_bytes)).convert("RGB")


def _candidate_labels(labels: list[str] | None) -> list[str]:
    return labels or ["motion-object"]


def _confidence_from_area(area_ratio: float) -> float:
    return round(min(0.55 + (area_ratio * 3.5), 0.98), 2)


def _detect_with_heuristic(
    image: Image.Image,
    *,
    labels: list[str] | None,
    threshold: float,
) -> tuple[list[ObjectDetection], dict[str, object]]:
    grayscale = image.convert("L")
    width, height = grayscale.size
    pixels = grayscale.load()
    min_blob_area = max(16, int(width * height * 0.01))

    visited: set[tuple[int, int]] = set()
    detections: list[ObjectDetection] = []
    candidate_labels = _candidate_labels(labels)

    for y in range(height):
        for x in range(width):
            if (x, y) in visited:
                continue
            if pixels[x, y] < 220:
                continue

            stack = [(x, y)]
            visited.add((x, y))
            min_x = max_x = x
            min_y = max_y = y
            area = 0

            while stack:
                current_x, current_y = stack.pop()
                area += 1
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x)
                min_y = min(min_y, current_y)
                max_y = max(max_y, current_y)

                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    if (next_x, next_y) in visited:
                        continue
                    visited.add((next_x, next_y))
                    if pixels[next_x, next_y] >= 220:
                        stack.append((next_x, next_y))

            if area < min_blob_area:
                continue

            area_ratio = area / float(width * height)
            confidence = _confidence_from_area(area_ratio)
            if confidence < threshold:
                continue

            detections.append(
                ObjectDetection(
                    label=candidate_labels[min(len(detections), len(candidate_labels) - 1)],
                    confidence=confidence,
                    bbox=(min_x, min_y, max_x, max_y),
                    area_ratio=round(area_ratio, 4),
                )
            )

    return detections, {
        "backend": "heuristic",
        "image_width": width,
        "image_height": height,
        "candidate_labels": candidate_labels,
    }


def _detect_with_opencv(
    image: Image.Image,
    *,
    labels: list[str] | None,
    threshold: float,
) -> tuple[list[ObjectDetection], dict[str, object]]:
    try:
        cv2 = importlib.import_module("cv2")
        numpy = importlib.import_module("numpy")
    except ModuleNotFoundError as exc:
        raise RuntimeError("OpenCV backend requested but cv2/numpy is not installed") from exc

    rgb_image = numpy.array(image)
    grayscale = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(grayscale, 220, 255, cv2.THRESH_BINARY)
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=4)

    height, width = grayscale.shape
    min_blob_area = max(16, int(width * height * 0.01))
    candidate_labels = _candidate_labels(labels)
    detections: list[ObjectDetection] = []

    for component_index in range(1, component_count):
        left = int(stats[component_index, cv2.CC_STAT_LEFT])
        top = int(stats[component_index, cv2.CC_STAT_TOP])
        blob_width = int(stats[component_index, cv2.CC_STAT_WIDTH])
        blob_height = int(stats[component_index, cv2.CC_STAT_HEIGHT])
        area = int(stats[component_index, cv2.CC_STAT_AREA])
        if area < min_blob_area:
            continue

        area_ratio = area / float(width * height)
        confidence = _confidence_from_area(area_ratio)
        if confidence < threshold:
            continue

        detections.append(
            ObjectDetection(
                label=candidate_labels[min(len(detections), len(candidate_labels) - 1)],
                confidence=confidence,
                bbox=(left, top, left + blob_width - 1, top + blob_height - 1),
                area_ratio=round(area_ratio, 4),
            )
        )

    return detections, {
        "backend": "opencv",
        "image_width": width,
        "image_height": height,
        "candidate_labels": candidate_labels,
    }


@lru_cache(maxsize=2)
def _load_yolo_model(model_path: str):
    try:
        ultralytics = importlib.import_module("ultralytics")
    except ModuleNotFoundError as exc:
        raise RuntimeError("YOLO backend requested but ultralytics is not installed") from exc
    return ultralytics.YOLO(model_path)


def _detect_with_yolo(
    image: Image.Image,
    *,
    labels: list[str] | None,
    threshold: float,
) -> tuple[list[ObjectDetection], dict[str, object]]:
    model_path = os.getenv("SMARTCITO_YOLO_MODEL", "yolov8n.pt")
    model = _load_yolo_model(model_path)
    results = model(image, verbose=False, conf=threshold)
    candidate_labels = _candidate_labels(labels)
    detections: list[ObjectDetection] = []

    first_result = results[0]
    names = getattr(first_result, "names", {}) or {}
    for index, box in enumerate(first_result.boxes):
        left, top, right, bottom = [int(value) for value in box.xyxy[0].tolist()]
        confidence = round(float(box.conf[0]), 2)
        class_id = int(box.cls[0]) if getattr(box, "cls", None) is not None else index
        default_label = names.get(class_id, candidate_labels[min(index, len(candidate_labels) - 1)])
        label = candidate_labels[min(index, len(candidate_labels) - 1)] if labels else str(default_label)
        area_ratio = ((right - left) * (bottom - top)) / float(image.width * image.height)
        detections.append(
            ObjectDetection(
                label=label,
                confidence=confidence,
                bbox=(left, top, right, bottom),
                area_ratio=round(area_ratio, 4),
            )
        )

    return detections, {
        "backend": "yolo",
        "image_width": image.width,
        "image_height": image.height,
        "candidate_labels": candidate_labels,
        "model": model_path,
    }


def _detect_with_auto(
    image: Image.Image,
    *,
    labels: list[str] | None,
    threshold: float,
) -> tuple[list[ObjectDetection], dict[str, object]]:
    backend_functions = []
    if os.getenv("SMARTCITO_YOLO_MODEL"):
        backend_functions.append(_detect_with_yolo)
    backend_functions.extend((_detect_with_opencv, _detect_with_heuristic))

    for backend_fn in backend_functions:
        try:
            return backend_fn(image, labels=labels, threshold=threshold)
        except RuntimeError:
            continue
    return _detect_with_heuristic(image, labels=labels, threshold=threshold)


def detect_objects(
    image_b64: str,
    *,
    backend: str,
    labels: list[str] | None = None,
    threshold: float = 0.6,
) -> tuple[list[ObjectDetection], dict[str, object]]:
    """Run object detection via an auto-selected, OpenCV, YOLO, or heuristic backend."""
    normalized_backend = backend.strip().lower()
    image = _decode_image(image_b64)

    if normalized_backend == "auto":
        detections, metadata = _detect_with_auto(image, labels=labels, threshold=threshold)
    elif normalized_backend == "heuristic":
        detections, metadata = _detect_with_heuristic(image, labels=labels, threshold=threshold)
    elif normalized_backend == "opencv":
        detections, metadata = _detect_with_opencv(image, labels=labels, threshold=threshold)
    elif normalized_backend == "yolo":
        detections, metadata = _detect_with_yolo(image, labels=labels, threshold=threshold)
    else:
        raise ValueError(f"Unsupported detection backend: {backend}")

    metadata["requested_backend"] = normalized_backend
    return detections, metadata
