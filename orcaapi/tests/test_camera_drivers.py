"""
================================================================================
 File: orcaapi/tests/test_camera_drivers.py
 Purpose: Parser-level tests for ONVIF and RTSP driver helpers.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from camera_module.drivers.onvif_driver import _parse_device_information  # noqa: E402
from camera_module.drivers.rtsp_driver import _parse_rtsp_response  # noqa: E402


def test_parse_onvif_device_information_extracts_core_fields() -> None:
    xml_payload = """
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
      <s:Body>
        <tds:GetDeviceInformationResponse xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
          <tds:Manufacturer>Acme Vision</tds:Manufacturer>
          <tds:Model>StreetCam Pro</tds:Model>
          <tds:FirmwareVersion>4.2.1</tds:FirmwareVersion>
          <tds:SerialNumber>SC-00077</tds:SerialNumber>
          <tds:HardwareId>rev-b</tds:HardwareId>
        </tds:GetDeviceInformationResponse>
      </s:Body>
    </s:Envelope>
    """

    profile = _parse_device_information(xml_payload, "http://camera-a/onvif/device_service")
    assert profile.device_id == "SC-00077"
    assert profile.manufacturer == "Acme Vision"
    assert profile.model == "StreetCam Pro"
    assert profile.media_url == "rtsp://camera-a/stream/main"


def test_parse_rtsp_response_extracts_status_and_server() -> None:
    raw = b"RTSP/1.0 200 OK\r\n" b"CSeq: 1\r\n" b"Server: SmartCam/9.1\r\n\r\n"

    probe = _parse_rtsp_response(raw, "rtsp://camera-a/stream/main")
    assert probe.status_code == 200
    assert probe.server_header == "SmartCam/9.1"
    assert probe.secure_transport is False
