# Micro Cameras

Reference design for ultra-compact Orca micro cameras.

## Capabilities

- compact camera module for discreet or temporary deployment
- magnetic mount for rapid placement and repositioning
- low-power operation with rechargeable micro-battery packs
- secure RTSP or HTTP/2 streaming into the ingestion layer
- mount / removal detection via magnetic or Hall-effect sensing

## Reference Build

- low-power camera module with hardware H.264/H.265 encoding
- microcontroller or compact Linux board for control-plane logic
- Hall-effect or reed-switch sensor for magnetic mount detection
- compact battery controller with charge and health reporting
- secure element for device identity if available

## Deployment Model

Micro cameras are suited to:
- temporary surveillance zones
- covert asset protection scenarios subject to policy approval
- pop-up events and mobile command posts

## Required Events

- `camera.mounted`
- `camera.removed`
- `camera.stream.started`
- `camera.stream.stopped`
- `camera.tamper.detected`
- `camera.battery.low`

All events must be auditable and flow into the Orca API.
