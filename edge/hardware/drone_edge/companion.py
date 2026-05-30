from __future__ import annotations

from hardware.drone_edge.mavlink_bridge import normalize_mavlink_telemetry
from hardware.drone_edge.schemas import CameraStreamProfile, DroneProfile, FrameSample, SensorSnapshot
from hardware.drone_edge.sdk import OrcaDroneSDK
from hardware.drone_edge.streamer import VideoEncodingProfile, build_camera_stream_profile


class DroneCompanionRuntime:
    def __init__(
        self,
        *,
        sdk: OrcaDroneSDK,
        drone_profile: DroneProfile,
        camera_profile: CameraStreamProfile | None = None,
        encoder_profile: VideoEncodingProfile | None = None,
    ) -> None:
        self.sdk = sdk
        self.drone_profile = drone_profile
        self.camera_profile = camera_profile
        self.encoder_profile = encoder_profile
        self._camera_registered = False

        if self.camera_profile is None and self.encoder_profile is not None:
            self.camera_profile = build_camera_stream_profile(
                drone_id=self.drone_profile.drone_id,
                encoder_profile=self.encoder_profile,
            )

    def camera_pipeline_plan(self) -> dict[str, object] | None:
        if self.encoder_profile is None:
            return None
        return {
            "behavior": self.encoder_profile.behavior_contract(),
            "command": self.encoder_profile.ffmpeg_command(),
        }

    def bootstrap(self) -> dict[str, object]:
        connect_result = self.sdk.connect_drone(self.drone_profile)
        capability_result = self.sdk.sync_capabilities(self.drone_profile)
        camera_result = None
        if self.camera_profile is not None:
            camera_result = self.sdk.register_camera_stream(self.camera_profile)
            self._camera_registered = True
        return {
            "connect": connect_result,
            "capabilities": capability_result,
            "camera": camera_result,
            "camera_pipeline": self.camera_pipeline_plan(),
        }

    def uplink_snapshot(
        self,
        *,
        mavlink_payload: dict[str, object],
        sensor_snapshots: list[SensorSnapshot] | None = None,
        frame_size: tuple[int, int] | None = None,
    ) -> dict[str, object]:
        telemetry = normalize_mavlink_telemetry(drone_id=self.drone_profile.drone_id, mavlink_payload=mavlink_payload)
        telemetry_result = self.sdk.publish_telemetry(telemetry)

        frame_result = None
        if self.camera_profile is not None and not self._camera_registered:
            self.sdk.register_camera_stream(self.camera_profile)
            self._camera_registered = True
        if self.camera_profile is not None and frame_size is not None:
            width, height = frame_size
            frame = FrameSample(
                drone_id=self.camera_profile.drone_id,
                width=width,
                height=height,
                stream_url=self.camera_profile.stream_url,
                position=telemetry.position,
            )
            frame_result = self.sdk.publish_frame(frame)

        sensor_results = []
        for snapshot in sensor_snapshots or []:
            sensor_results.append(self.sdk.publish_sensor_snapshot(snapshot))

        return {
            "telemetry": telemetry_result,
            "frame": frame_result,
            "sensors": sensor_results,
        }