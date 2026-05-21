/**
 * ============================================================================
 * File: webapp/src/api/cameras.ts
 * Purpose:
 *   Typed client helpers for camera fleet registration state.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "./client";

export type CameraDeviceType = "body_camera" | "micro_camera";
export type StreamStatus = "offline" | "connecting" | "live" | "degraded";

export interface CameraLocation {
  lat: number;
  lon: number;
  accuracy_m?: number | null;
}

export interface CameraDevice {
  id: string;
  device_id: string;
  device_type: CameraDeviceType;
  firmware_version: string;
  registered_at: string;
  last_seen_at: string;
  stream_status: StreamStatus;
  location?: CameraLocation | null;
  battery_level?: number | null;
  mounted?: boolean | null;
  tamper_detected: boolean;
}

export const demoCameraFleet: CameraDevice[] = [
  {
    id: "demo-body-001",
    device_id: "demo-body-001",
    device_type: "body_camera",
    firmware_version: "demo-1.0.0",
    registered_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
    stream_status: "live",
    location: { lat: -25.7479, lon: 28.2293, accuracy_m: 4.2 },
    battery_level: 87,
    mounted: true,
    tamper_detected: false,
  },
  {
    id: "demo-micro-007",
    device_id: "demo-micro-007",
    device_type: "micro_camera",
    firmware_version: "demo-2.4.1",
    registered_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
    stream_status: "connecting",
    location: { lat: -26.2041, lon: 28.0473, accuracy_m: 8 },
    battery_level: 52,
    mounted: true,
    tamper_detected: false,
  },
];

export async function fetchCameras(): Promise<CameraDevice[]> {
  const { data } = await api.get<CameraDevice[]>("/cameras");
  return data;
}

export function useCameras() {
  return useQuery({
    queryKey: ["cameras", "fleet"],
    queryFn: fetchCameras,
    refetchInterval: 5_000,
  });
}
