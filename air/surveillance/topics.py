"""
================================================================================
 File: surveillance/topics.py
 Purpose:
   Central Kafka topic names for Orca drone and sensor surveillance flows.
================================================================================
"""

from __future__ import annotations

import os


def env_topic(name: str, default: str) -> str:
    return os.getenv(name, default)


DRONE_TELEMETRY_TOPIC = env_topic("KAFKA_DRONE_TELEMETRY_TOPIC", "orca.drone.telemetry")
DRONE_EVENTS_TOPIC = env_topic("KAFKA_DRONE_EVENTS_TOPIC", "orca.drone.events")
DRONE_MISSIONS_TOPIC = env_topic("KAFKA_DRONE_MISSIONS_TOPIC", "orca.drone.missions")
ROBOT_TELEMETRY_TOPIC = env_topic("KAFKA_ROBOT_TELEMETRY_TOPIC", "orca.robot.telemetry")
ROBOT_EVENTS_TOPIC = env_topic("KAFKA_ROBOT_EVENTS_TOPIC", "orca.robot.events")
ROBOT_MISSIONS_TOPIC = env_topic("KAFKA_ROBOT_MISSIONS_TOPIC", "orca.robot.missions")
DRONE_CAMERA_FRAMES_TOPIC = env_topic("KAFKA_DRONE_CAMERA_FRAMES_TOPIC", "orca.drone.camera.frames")
DRONE_CAMERA_ALERTS_TOPIC = env_topic("KAFKA_DRONE_CAMERA_ALERTS_TOPIC", "orca.drone.camera.alerts")
SENSOR_READINGS_TOPIC = env_topic("KAFKA_SENSOR_READINGS_TOPIC", "orca.sensors.raw")
SENSOR_ALERTS_TOPIC = env_topic("KAFKA_SENSOR_ALERTS_TOPIC", "orca.sensor.alerts")
THREAT_ALERTS_TOPIC = env_topic("KAFKA_THREAT_ALERTS_TOPIC", "orca.threat.alerts")
LOCATION_ENRICHED_TOPIC = env_topic("KAFKA_LOCATION_ENRICHED_TOPIC", "orca.location.enriched")

SURVEILLANCE_TOPICS = {
    "drone_telemetry": DRONE_TELEMETRY_TOPIC,
    "drone_events": DRONE_EVENTS_TOPIC,
    "drone_missions": DRONE_MISSIONS_TOPIC,
    "robot_telemetry": ROBOT_TELEMETRY_TOPIC,
    "robot_events": ROBOT_EVENTS_TOPIC,
    "robot_missions": ROBOT_MISSIONS_TOPIC,
    "drone_camera_frames": DRONE_CAMERA_FRAMES_TOPIC,
    "drone_camera_alerts": DRONE_CAMERA_ALERTS_TOPIC,
    "sensor_readings": SENSOR_READINGS_TOPIC,
    "sensor_alerts": SENSOR_ALERTS_TOPIC,
    "threat_alerts": THREAT_ALERTS_TOPIC,
    "location_enriched": LOCATION_ENRICHED_TOPIC,
}
