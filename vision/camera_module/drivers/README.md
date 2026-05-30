# Camera Drivers

Vendor-specific and protocol-specific camera drivers live here.

## Purpose

This folder standardizes how contributors add support for new camera vendors
without changing the rest of Orca.

## Supported Standards

- ONVIF for interoperable IP camera control and discovery
- RTSP for media streaming
- HTTP/2 for secure control-plane and metadata exchange
- WebRTC where low-latency streaming is required

## Driver Layout

```
camera_module/drivers/
├── onvif/
├── rtsp/
├── <vendor-name>/
└── README.md
```

Each driver folder should include:
- transport and authentication assumptions
- capability mapping to Orca camera metadata
- tests or fixtures for discovery and stream setup
- a local README describing supported devices

## Rules

- Normalize camera metadata before it leaves the driver boundary.
- Prefer open standards before vendor-private APIs.
- Do not bypass the security posture in [`../../security/SECURITY_POSTURE.md`](../../security/SECURITY_POSTURE.md).
