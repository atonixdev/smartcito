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
  device_type: "usb" | "camera" | "gps" | "iot";
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

export interface SmartMapOverview {
  devices: SmartMapDevice[];
  heatmap: SmartMapHeatPoint[];
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
];

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