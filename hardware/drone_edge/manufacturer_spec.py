from __future__ import annotations


def build_manufacturer_spec() -> dict[str, object]:
    return {
        "platform_goal": "PX4/ArduPilot airframe with a SmartCito-managed companion computer and cloud-controlled surveillance stack.",
        "flight_stack": {
            "autopilot": ["PX4", "ArduPilot"],
            "required_protocols": ["MAVLink", "mission upload", "telemetry egress"],
            "integration_requirements": [
                "Companion computer must access MAVLink over UART, USB, or Ethernet.",
                "Mission upload and telemetry must be available without vendor lock-in.",
            ],
        },
        "companion_computer": {
            "compute": ["Jetson", "Raspberry Pi", "custom ARM/CPU-GPU module"],
            "requirements": [
                "Enough CPU/GPU for H.264/H.265 encoding and ROS2 autonomy nodes.",
                "RAM and storage sized for video buffering, logs, and AI models.",
                "SSH access and full software installation rights for SmartCito software.",
            ],
            "interfaces": ["Ethernet", "USB", "UART", "4G/5G modem", "WiFi"],
        },
        "camera": {
            "types": ["RGB", "thermal", "zoom"],
            "interfaces": ["CSI", "USB", "HDMI", "MIPI"],
            "operational_requirements": [
                "Camera must be accessible from the companion computer user space.",
                "Companion computer must be able to encode and stream video via RTSP or WebRTC.",
                "Resolution, FPS, and bitrate must be configurable in SmartCito software.",
            ],
        },
        "power_and_form_factor": {
            "targets": ["battery size", "flight time", "payload capacity", "sensor expansion budget"],
            "access_requirements": [
                "Airframe must expose maintenance access to the companion computer and camera wiring.",
                "Thermal design must support sustained encoder and ROS2 workloads.",
            ],
        },
        "operator_access": {
            "required": [
                "SSH access to companion computer",
                "Install SmartCito SDK, ROS2 nodes, and video streamer",
                "Access MAVLink directly from companion computer",
            ],
        },
        "delivery_workflow": [
            "Manufacturer builds airframe, power system, and electronics to this spec.",
            "SmartCito team owns companion-computer software, camera behavior, SDK, and cloud stack.",
            "Flight validation uses PX4/ArduPilot plus SmartCito Mission Control, Camera Service, and Dashboard.",
        ],
    }