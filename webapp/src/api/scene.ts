/**
 * ============================================================================
 * File: webapp/src/api/scene.ts
 * Purpose:
 *   Typed client for the SmartCito 3D dashboard control-plane scene.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "./client";
import { demoSmartMapDevices } from "./map";

export interface SceneDevice {
  id: string;
  device_id: string;
  name: string;
  device_type: "usb" | "camera" | "gps" | "iot";
  x: number;
  y: number;
  z: number;
  latitude: number;
  longitude: number;
  trust_score: number;
  trust_level: "verified" | "unverified" | "blocked";
  status_color: string;
  camera_feed_url?: string | null;
  sensor_type: string;
  sensor_value?: number | null;
  gps_path_3d: Array<[number, number, number]>;
}

export interface SceneThreat {
  id: string;
  x: number;
  y: number;
  z: number;
  severity: "low" | "medium" | "high" | string;
  radius: number;
  source_device_id: string;
  label: string;
}

export interface SceneOverview {
  devices: SceneDevice[];
  threats: SceneThreat[];
  layers: string[];
  camera_overlay_mode: string;
  security_policy: string;
}

function statusColor(trustScore: number) {
  if (trustScore > 80) {
    return "#67d5a5";
  }
  if (trustScore > 0) {
    return "#f1c96b";
  }
  return "#f87171";
}

function scenePosition(latitude: number, longitude: number): [number, number, number] {
  const anchorLatitude = -25.7479;
  const anchorLongitude = 28.2293;
  return [(longitude - anchorLongitude) * 180, 0.05, (latitude - anchorLatitude) * -180];
}

export const demoSceneOverview: SceneOverview = {
  devices: demoSmartMapDevices.map((device) => {
    const [xPosition, yPosition, zPosition] = scenePosition(device.latitude, device.longitude);
    return {
      id: device.id,
      device_id: device.device_id,
      name: device.name,
      device_type: device.device_type,
      x: xPosition,
      y: yPosition + 0.35,
      z: zPosition,
      latitude: device.latitude,
      longitude: device.longitude,
      trust_score: device.trust_score,
      trust_level: device.trust_level,
      status_color: statusColor(device.trust_score),
      camera_feed_url: device.camera_feed_url,
      sensor_type: device.sensor_type,
      sensor_value: device.sensor_value,
      gps_path_3d: device.gps_path.map(([latitude, longitude]) => scenePosition(latitude, longitude)),
    };
  }),
  threats: [
    {
      id: "demo-threat-air-quality",
      x: -7.41,
      y: 0.04,
      z: 0.32,
      severity: "high",
      radius: 2.4,
      source_device_id: "demo-raspi-edge-001",
      label: "AI watch zone: air-quality",
    },
  ],
  layers: ["city-map", "iot-devices", "gps-paths", "camera-overlays", "threat-waves"],
  camera_overlay_mode: "popup-texture-ready",
  security_policy: "JWT + RBAC required; objects are color-coded by trust score and visible only after map trust policy validation",
};

export async function fetchSceneOverview(): Promise<SceneOverview> {
  const { data } = await api.get<SceneOverview>("/control-plane/scene");
  return data;
}

export function useSceneOverview() {
  return useQuery({
    queryKey: ["control-plane", "scene"],
    queryFn: fetchSceneOverview,
    refetchInterval: 5_000,
  });
}