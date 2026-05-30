"""
================================================================================
 File: hardware/usb_module/detector.py
 Purpose:
   Simulation-first USB device discovery surface. In CI and local development,
   returns a stable list of signed and unsigned devices that the dashboard can
   render and security policy can classify.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(slots=True)
class UsbDevice:
    id: str
    name: str
    category: str
    trust_level: str
    driver_container: str
    endpoint: str
    firmware_version: str
    authenticated: bool
    signed_driver: bool
    last_seen_at: datetime


def detect_usb_devices() -> list[UsbDevice]:
    now = datetime.now(UTC)
    return [
        UsbDevice(
            id="usb-gps-001",
            name="USB GPS Receiver",
            category="gps",
            trust_level="verified",
            driver_container="usb-service",
            endpoint="/dev/ttyUSB0",
            firmware_version="3.2.1",
            authenticated=True,
            signed_driver=True,
            last_seen_at=now,
        ),
        UsbDevice(
            id="usb-sensor-004",
            name="Field Sensor Bridge",
            category="iot",
            trust_level="unverified",
            driver_container="usb-service",
            endpoint="/dev/ttyUSB1",
            firmware_version="1.9.0",
            authenticated=False,
            signed_driver=False,
            last_seen_at=now - timedelta(minutes=2),
        ),
    ]