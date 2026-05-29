"""Unified inference wrapper over the modular Orca model artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.model_stack.models.anomaly_detection.infer import score_sequence_anomaly
from ai.model_stack.models.drone_vision.infer import classify_image
from ai.model_stack.models.gps_classification.infer import classify_gps_sequence
from ai.model_stack.models.sensor_fusion.infer import score_sensor_fusion
from ai.model_stack.models.trajectory_prediction.infer import predict_trajectory


class OrcaModelPipeline:
    def __init__(
        self,
        *,
        gps_model_dir: str | Path | None = None,
        trajectory_model_dir: str | Path | None = None,
        anomaly_model_dir: str | Path | None = None,
        drone_vision_model_dir: str | Path | None = None,
        sensor_fusion_model_dir: str | Path | None = None,
    ) -> None:
        self.gps_model_dir = Path(gps_model_dir) if gps_model_dir else None
        self.trajectory_model_dir = Path(trajectory_model_dir) if trajectory_model_dir else None
        self.anomaly_model_dir = Path(anomaly_model_dir) if anomaly_model_dir else None
        self.drone_vision_model_dir = Path(drone_vision_model_dir) if drone_vision_model_dir else None
        self.sensor_fusion_model_dir = Path(sensor_fusion_model_dir) if sensor_fusion_model_dir else None

    def run(self, *, gps_sequence: list[dict[str, Any]] | None = None, image: Any = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {"metadata": metadata or {}}
        if gps_sequence and self.gps_model_dir:
            result["gps_classification"] = classify_gps_sequence(self.gps_model_dir, gps_sequence)
        if gps_sequence and self.trajectory_model_dir:
            result["trajectory_prediction"] = predict_trajectory(self.trajectory_model_dir, gps_sequence)
        if gps_sequence and self.anomaly_model_dir:
            result["anomaly"] = score_sequence_anomaly(self.anomaly_model_dir, gps_sequence)
        if image is not None and self.drone_vision_model_dir:
            result["drone_vision"] = classify_image(self.drone_vision_model_dir, image)
        if self.sensor_fusion_model_dir and "gps_classification" in result and "drone_vision" in result:
            gps_embedding = result["gps_classification"].get("embedding")
            vision_embedding = result["drone_vision"].get("embedding")
            if gps_embedding is not None and vision_embedding is not None:
                result["sensor_fusion"] = score_sensor_fusion(
                    self.sensor_fusion_model_dir,
                    gps_embedding=gps_embedding,
                    vision_embedding=vision_embedding,
                    metadata=metadata or {},
                )
        return result


# Backward compatibility for older imports.
OrcaKerasPipeline = OrcaModelPipeline