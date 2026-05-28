from __future__ import annotations

from hardware.drone_edge.manufacturer_spec import build_manufacturer_spec
from hardware.drone_edge.ros2_contract import build_ros2_node_contract


def build_rfp_packet() -> dict[str, object]:
    spec = build_manufacturer_spec()
    ros2_contract = build_ros2_node_contract()

    return {
        "title": "Orca Drone Platform RFP Packet",
        "document_style": "PDF-ready markdown packet",
        "executive_summary": {
            "procurement_model": "Manufacturer builds the airframe and electronics; Orca owns companion-computer software and cloud stack.",
            "target_architecture": "PX4/ArduPilot + companion computer + RGB/thermal/zoom camera + 4G/5G/WiFi uplink into Orca.",
        },
        "sections": [
            "Program Overview",
            "Reference Architecture",
            "Flight Stack Requirements",
            "Companion Computer Requirements",
            "Camera and Video Requirements",
            "ROS2 Autonomy Node Contract",
            "Power and Form Factor",
            "Connectivity and Interfaces",
            "BOM Response Table",
            "Acceptance Checklist",
            "Vendor Response Questionnaire",
        ],
        "bom_fields": [
            "airframe model",
            "flight controller",
            "companion computer SKU",
            "cpu/gpu class",
            "ram_gb",
            "storage_gb",
            "camera type",
            "camera interface",
            "camera resolution",
            "camera fps",
            "modem type",
            "wifi module",
            "battery capacity",
            "target flight time",
            "payload capacity",
        ],
        "acceptance_checklist": [
            "PX4 or ArduPilot installed and MAVLink reachable from companion computer.",
            "Orca team can SSH into the companion computer.",
            "Orca team can install ROS2 nodes, SDK, and video streamer.",
            "Camera is accessible from user space and can stream H.264 or H.265 over RTSP or WebRTC.",
            "Mission upload and telemetry egress work without vendor cloud dependency.",
            "4G/5G or WiFi uplink reaches Orca cloud endpoints.",
            "Thermal envelope supports sustained encode and ROS2 autonomy runtime.",
        ],
        "vendor_response_questions": [
            "Can you deliver this airframe and electronics while preserving Orca software control?",
            "Which companion computer SKUs do you recommend for ROS2 and H.265 encoding?",
            "What payload and flight-time tradeoffs apply with RGB, thermal, and zoom camera options?",
            "What lead time and MOQ apply for prototype and pilot batches?",
        ],
        "manufacturer_spec": spec,
        "ros2_contract": ros2_contract,
    }