# USB Module

## Purpose

Simulation-first USB device detection and driver mapping for SmartCito's device
manager and hardware plug-in flow.

## Technologies Used

- Python 3.11
- FastAPI
- udev-compatible device metadata model

## How To Run Its Container

```bash
docker build -f hardware/usb_module/Dockerfile -t smartcito-usb-module .
docker run --rm -p 8015:8015 smartcito-usb-module
```

## Example Usage

```bash
curl http://localhost:8015/devices
```