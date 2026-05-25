/**
 * ============================================================================
 * File: webapp/src/api/map.ts
 * Purpose:
 *   Typed client for the SmartCito IoT -> GPS -> Map -> Camera control-plane
 *   integration.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "./client";

export interface SmartMapDevice {
  id: string;
  device_id: string;
  name: string;
  device_type: "usb" | "camera" | "gps" | "iot" | "drone" | "robot" | "sensor";
  latitude: number;
  longitude: number;
  trust_score: number;
  trust_level: "verified" | "unverified" | "blocked";
  camera_feed_url?: string | null;
  sensor_type: string;
  sensor_value?: number | null;
  gps_path: Array<[number, number]>;
  last_seen_at: string;
}

export interface SmartMapHeatPoint {
  latitude: number;
  longitude: number;
  intensity: number;
  label: string;
}

export interface SmartMapCameraCorridor {
  id: string;
  source_device_id: string;
  label: string;
  polygon: Array<[number, number]>;
  coverage_score: number;
}

export interface SmartMapOverview {
  devices: SmartMapDevice[];
  heatmap: SmartMapHeatPoint[];
  camera_corridors: SmartMapCameraCorridor[];
  visible_layers: string[];
  security_policy: string;
}

export const demoSmartMapDevices: SmartMapDevice[] = [
  {
    id: "demo-map-camera-001",
    device_id: "demo-map-camera-001",
    name: "Pretoria Camera Node",
    device_type: "camera",
    latitude: -25.7479,
    longitude: 28.2293,
    trust_score: 96,
    trust_level: "verified",
    camera_feed_url: "rtsp://demo/pretoria-camera-001",
    sensor_type: "camera-feed",
    sensor_value: 0.67,
    gps_path: [[-25.749, 28.2281], [-25.7484, 28.2287], [-25.7479, 28.2293]],
    last_seen_at: new Date().toISOString(),
  },
  {
    id: "demo-raspi-edge-001",
    device_id: "demo-raspi-edge-001",
    name: "Raspberry Pi Edge Node",
    device_type: "iot",
    latitude: -25.7461,
    longitude: 28.1881,
    trust_score: 92,
    trust_level: "verified",
    camera_feed_url: "rtsp://demo/raspi-edge-001/camera",
    sensor_type: "air-quality",
    sensor_value: 0.74,
    gps_path: [[-25.7472, 28.1868], [-25.7467, 28.1875], [-25.7461, 28.1881]],
    last_seen_at: new Date().toISOString(),
  },
  {
    id: "demo-usb-gps-001",
    device_id: "demo-usb-gps-001",
    name: "USB GPS Receiver",
    device_type: "gps",
    latitude: -25.7469,
    longitude: 28.2299,
    trust_score: 100,
    trust_level: "verified",
    camera_feed_url: null,
    sensor_type: "gps",
    sensor_value: 0.55,
    gps_path: [[-25.748, 28.2287], [-25.7474, 28.2293], [-25.7469, 28.2299]],
    last_seen_at: new Date().toISOString(),
  },
  {
    id: "demo-drone-patrol-001",
    device_id: "demo-drone-patrol-001",
    name: "Drone Patrol Unit 001",
    device_type: "drone",
    latitude: -25.7454,
    longitude: 28.2438,
    trust_score: 94,
    trust_level: "verified",
    camera_feed_url: "rtsp://demo/drone-patrol-001/camera",
    sensor_type: "drone-telemetry",
    sensor_value: 0.88,
    gps_path: [[-25.7479, 28.2293], [-25.7461, 28.2361], [-25.7454, 28.2438]],
    last_seen_at: new Date().toISOString(),
  },
  {
    id: "demo-robot-patrol-007",
    device_id: "demo-robot-patrol-007",
    name: "UGV Patrol 007",
    device_type: "robot",
    latitude: -25.7462,
    longitude: 28.2372,
    trust_score: 89,
    trust_level: "verified",
    camera_feed_url: "rtsp://demo/robot-patrol-007/front-camera",
    sensor_type: "lidar-slam",
    sensor_value: 0.81,
    gps_path: [[-25.7472, 28.2364], [-25.7468, 28.2369], [-25.7462, 28.2372]],
    last_seen_at: new Date().toISOString(),
  },
  {
    id: "demo-perimeter-sensor-003",
    device_id: "demo-perimeter-sensor-003",
    name: "Perimeter Motion Sensor 003",
    device_type: "sensor",
    latitude: -25.7448,
    longitude: 28.2455,
    trust_score: 91,
    trust_level: "verified",
    camera_feed_url: null,
    sensor_type: "motion",
    sensor_value: 0.92,
    gps_path: [[-25.7452, 28.2442], [-25.7448, 28.2455]],
    last_seen_at: new Date().toISOString(),
  },
];

export const demoSmartMapOverview: SmartMapOverview = {
  devices: demoSmartMapDevices,
  heatmap: demoSmartMapDevices.map((device) => ({
    latitude: device.latitude,
    longitude: device.longitude,
    intensity: Math.min(Math.max(device.sensor_value ?? 0.45, 0.15), 1),
    label: `${device.name} ${device.sensor_type}`,
  })),
  camera_corridors: [
    {
      id: "demo-map-camera-001-corridor",
      source_device_id: "demo-map-camera-001",
      label: "Pretoria Camera Node corridor",
      polygon: [
        [-25.74753, 28.22978],
        [-25.74827, 28.22882],
        [-25.74972, 28.22738],
        [-25.74886, 28.22838],
      ],
      coverage_score: 0.78,
    },
  ],
  visible_layers: ["verified-devices", "camera-overlays", "gps-paths", "sensor-heatmap", "drone-patrols", "threat-zones"],
  security_policy: "verified devices only; trust score must be greater than 80; drone, sensor, camera, and map updates are audited",
};

export async function fetchSmartMapOverview(): Promise<SmartMapOverview> {
  const { data } = await api.get<SmartMapOverview>("/control-plane/map");
  return data;
}

export function useSmartMapOverview() {
  return useQuery({
    queryKey: ["control-plane", "map"],
    queryFn: fetchSmartMapOverview,
    refetchInterval: 5_000,
  });
}