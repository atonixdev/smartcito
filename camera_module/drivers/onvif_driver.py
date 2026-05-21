"""ONVIF discovery/control helpers for SmartCito camera integrations."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx


@dataclass(slots=True)
class OnvifDeviceProfile:
    """Normalized ONVIF device information."""

    device_id: str
    management_url: str
    media_url: str
    manufacturer: str
    model: str
    firmware_version: str
    serial_number: str


SOAP_GET_DEVICE_INFORMATION = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <s:Body>
    <tds:GetDeviceInformation/>
  </s:Body>
</s:Envelope>
"""


def _parse_device_information(xml_text: str, management_url: str) -> OnvifDeviceProfile:
    """Parse a GetDeviceInformation SOAP response into a normalized profile."""
    root = ElementTree.fromstring(xml_text)

    values = {
        "manufacturer": "unknown",
        "model": "unknown",
        "firmware_version": "unknown",
        "serial_number": "unknown",
        "hardware_id": "unknown",
    }
    for tag_name, field_name in (
        ("Manufacturer", "manufacturer"),
        ("Model", "model"),
        ("FirmwareVersion", "firmware_version"),
        ("SerialNumber", "serial_number"),
        ("HardwareId", "hardware_id"),
    ):
        element = root.find(f".//{{*}}{tag_name}")
        if element is not None and element.text:
            values[field_name] = element.text.strip()

    parsed = urlparse(management_url)
    host = parsed.hostname or "camera"
    device_id = values["serial_number"] if values["serial_number"] != "unknown" else f"onvif-{host}"
    return OnvifDeviceProfile(
        device_id=device_id,
        management_url=management_url,
        media_url=f"rtsp://{host}/stream/main",
        manufacturer=values["manufacturer"],
        model=values["model"],
        firmware_version=values["firmware_version"],
        serial_number=values["serial_number"],
    )


def fetch_onvif_device_information(
    management_url: str,
    username: str,
    password: str,
    timeout: float = 5.0,
) -> OnvifDeviceProfile:
    """Probe an ONVIF device service and return normalized device metadata."""
    response = httpx.post(
        management_url,
        content=SOAP_GET_DEVICE_INFORMATION,
        headers={
            "Content-Type": "application/soap+xml; charset=utf-8",
            "User-Agent": "SmartCito/0.1",
        },
        auth=(username, password),
        timeout=timeout,
    )
    response.raise_for_status()
    return _parse_device_information(response.text, management_url)


def discover_onvif_device(host: str, username: str, password: str) -> OnvifDeviceProfile:
    """Probe the default ONVIF device service on a given host."""
    management_url = f"http://{host}/onvif/device_service"
    return fetch_onvif_device_information(management_url, username, password)
