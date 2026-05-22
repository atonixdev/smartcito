/**
 * ============================================================================
 * File: webapp/src/api/platform.ts
 * Purpose:
 *   Typed frontend hooks for SmartCito resource APIs: devices, cameras, GPS,
 *   events, map layers, and live WebSocket URLs.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";

import { apiClient, buildWebSocketUrl } from "@/lib/apiClient";

export interface PlatformDevice {
  id: string;
  type: "camera" | "gps" | "iot" | "edge" | string;
  status: "online" | "offline" | "blocked" | string;
  location: { lat: number; lng: number };
  trust_score: number;
}

export interface PlatformEvent {
  id: string;
  kind: string;
  severity: string;
  message: string;
  timestamp: string;
}

export interface DevicesPayload {
  devices: PlatformDevice[];
}

export interface EventsPayload {
  events: PlatformEvent[];
}

const demoDevices: PlatformDevice[] = [
  { id: "cam-001", type: "camera", status: "online", location: { lat: -26.2041, lng: 28.0473 }, trust_score: 96 },
  { id: "gps-001", type: "gps", status: "online", location: { lat: -26.205, lng: 28.048 }, trust_score: 92 },
];

export function useDevices() {
  return useQuery({
    queryKey: ["platform", "devices"],
    queryFn: async () => {
      try {
        return (await apiClient.get<DevicesPayload>("/devices")).devices;
      } catch {
        return demoDevices;
      }
    },
    refetchInterval: 10_000,
  });
}

export function useEvents() {
  return useQuery({
    queryKey: ["platform", "events"],
    queryFn: async () => {
      try {
        return (await apiClient.get<EventsPayload>("/events")).events;
      } catch {
        return [];
      }
    },
    refetchInterval: 10_000,
  });
}

export const liveUrls = {
  gps: () => buildWebSocketUrl("/ws/gps"),
  events: () => buildWebSocketUrl("/ws/events"),
};
