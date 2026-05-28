# USB Module

## Purpose

Simulation-first USB device detection and driver mapping for Orca's device
manager and hardware plug-in flow.

## Container Image

- Build file: `hardware/usb_module/Dockerfile`
- What the image does: runs the FastAPI USB device service on port `8015` for enumerating attached devices and driver matches.
- What ships in the image: the `hardware/` package, including the USB module, and this README at `/app/hardware/usb_module/README.md`.

## Technologies Used

- Python 3.11
- FastAPI
- udev-compatible device metadata model

## How To Run Its Container

```bash
docker build -f hardware/usb_module/Dockerfile -t orca-usb-module .
docker run --rm -p 8015:8015 orca-usb-module
```

## Example Usage

```bash
curl http://localhost:8015/devices
```