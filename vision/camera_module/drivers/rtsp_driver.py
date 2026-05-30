"""RTSP stream validation helpers for Orca camera integrations."""

from __future__ import annotations

from dataclasses import dataclass
import socket
import ssl
from urllib.parse import urlparse


@dataclass(slots=True)
class RtspStreamConfig:
    """Normalized RTSP connection details for a camera feed."""

    device_id: str
    stream_uri: str
    protocol: str = "rtsp"
    secure_transport: bool = True


@dataclass(slots=True)
class RtspStreamProbe:
    """Observed RTSP probe result for one stream URI."""

    stream_uri: str
    status_code: int
    server_header: str | None
    secure_transport: bool


def _parse_rtsp_response(raw_response: bytes, stream_uri: str) -> RtspStreamProbe:
    """Parse the RTSP status line and server header from a response payload."""
    text = raw_response.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Empty RTSP response")

    parts = lines[0].split()
    if len(parts) < 2 or not parts[1].isdigit():
        raise ValueError(f"Invalid RTSP status line: {lines[0]}")

    server_header = None
    for line in lines[1:]:
        if line.lower().startswith("server:"):
            server_header = line.split(":", 1)[1].strip()
            break

    secure_transport = urlparse(stream_uri).scheme == "rtsps"
    return RtspStreamProbe(
        stream_uri=stream_uri,
        status_code=int(parts[1]),
        server_header=server_header,
        secure_transport=secure_transport,
    )


def build_rtsp_stream_config(device_id: str, host: str, path: str = "/stream/main") -> RtspStreamConfig:
    """Construct a canonical RTSP stream descriptor for contributors to extend."""
    return RtspStreamConfig(
        device_id=device_id,
        stream_uri=f"rtsp://{host}{path}",
    )


def validate_rtsp_stream(stream_uri: str, timeout: float = 5.0) -> RtspStreamProbe:
    """Open a socket to an RTSP endpoint and issue an OPTIONS probe."""
    parsed = urlparse(stream_uri)
    host = parsed.hostname
    if host is None:
        raise ValueError(f"Invalid RTSP URI: {stream_uri}")

    is_secure = parsed.scheme == "rtsps"
    port = parsed.port or (322 if is_secure else 554)
    request_target = stream_uri
    request = (
        f"OPTIONS {request_target} RTSP/1.0\r\n"
        "CSeq: 1\r\n"
        "User-Agent: Orca/0.1\r\n\r\n"
    ).encode("utf-8")

    with socket.create_connection((host, port), timeout=timeout) as sock:
        connection = ssl.create_default_context().wrap_socket(sock, server_hostname=host) if is_secure else sock
        connection.sendall(request)
        response = connection.recv(4096)

    return _parse_rtsp_response(response, stream_uri)
