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