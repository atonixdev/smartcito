from __future__ import annotations

from dataclasses import dataclass

from hardware.drone_edge.schemas import CameraStreamProfile, GeoPoint


@dataclass(slots=True)
class VideoEncodingProfile:
    input_source: str
    stream_host: str
    stream_path: str = "main"
    protocol: str = "rtsp"
    codec: str = "h264"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    bitrate_kbps: int = 4_000
    camera_id: str = "rgb-main"
    hardware_acceleration: str | None = None
    signaling_endpoint: str | None = None

    def stream_url(self) -> str:
        if self.protocol == "webrtc":
            if self.signaling_endpoint:
                return f"{self.signaling_endpoint.rstrip('/')}/{self.stream_path.lstrip('/')}"
            return f"webrtc://{self.stream_host}/{self.stream_path.lstrip('/')}"
        if self.protocol == "custom":
            return f"orca://{self.stream_host}/{self.stream_path.lstrip('/')}"
        return f"rtsp://{self.stream_host}/{self.stream_path.lstrip('/')}"

    def _video_codec_args(self) -> list[str]:
        codec_name = "libx265" if self.codec == "h265" else "libx264"
        if self.hardware_acceleration == "jetson":
            codec_name = "hevc_nvenc" if self.codec == "h265" else "h264_nvenc"
        elif self.hardware_acceleration == "vaapi":
            codec_name = "hevc_vaapi" if self.codec == "h265" else "h264_vaapi"
        return ["-c:v", codec_name]

    def ffmpeg_command(self) -> list[str]:
        transport_args = ["-f", "rtsp", self.stream_url()]
        if self.protocol == "webrtc":
            transport_args = ["-f", "tee", f"[f=rtp]{self.stream_url()}"]
        elif self.protocol == "custom":
            transport_args = ["-f", "mpegts", self.stream_url()]

        command = [
            "ffmpeg",
            "-re",
            "-i",
            self.input_source,
            "-vf",
            f"scale={self.width}:{self.height},fps={self.fps}",
            *self._video_codec_args(),
            "-b:v",
            f"{self.bitrate_kbps}k",
            "-pix_fmt",
            "yuv420p",
            "-an",
            *transport_args,
        ]
        return command

    def behavior_contract(self) -> dict[str, object]:
        return {
            "camera_id": self.camera_id,
            "input_source": self.input_source,
            "codec": self.codec,
            "protocol": self.protocol,
            "resolution": {"width": self.width, "height": self.height},
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps,
            "stream_url": self.stream_url(),
            "hardware_acceleration": self.hardware_acceleration,
        }


def build_camera_stream_profile(
    *,
    drone_id: str,
    encoder_profile: VideoEncodingProfile,
    position: GeoPoint | None = None,
) -> CameraStreamProfile:
    return CameraStreamProfile(
        drone_id=drone_id,
        stream_url=encoder_profile.stream_url(),
        protocol=encoder_profile.protocol,
        camera_id=encoder_profile.camera_id,
        position=position,
    )