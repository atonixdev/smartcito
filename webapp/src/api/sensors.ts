/**
 * ============================================================================
 * File: frontend/src/api/sensors.ts
 * Purpose:
 *   Typed API helpers for the /sensors and /traffic endpoints, plus React
 *   Query hooks that components can drop in without touching axios.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export type SensorKind =
  | "traffic"
  | "air_quality"
  | "water"
  | "energy"
  | "cctv"
  | "other";

export interface SensorReading {
  id: string;
  sensor_id: string;
  kind: SensorKind;
  value: number;
  unit: string;
  latitude?: number | null;
  longitude?: number | null;
  observed_at: string;
  received_at: string;
  metadata: Record<string, string>;
}

export interface TrafficSummaryItem {
  sensor_id: string;
  samples: number;
  average_value: number;
  unit: string;
}

export interface TrafficSummary {
  total_samples: number;
  sensors: TrafficSummaryItem[];
}

// ---------- Raw fetchers ----------

export async function fetchRecentSensors(limit = 50): Promise<SensorReading[]> {
  const { data } = await api.get<SensorReading[]>("/sensors/recent", {
    params: { limit },
  });
  return data;
}

export async function fetchTrafficSummary(): Promise<TrafficSummary> {
  const { data } = await api.get<TrafficSummary>("/traffic/summary");
  return data;
}

// ---------- React Query hooks ----------

/** Poll the recent-readings endpoint every 5 seconds for live dashboards. */
export function useRecentSensors(limit = 50) {
  return useQuery({
    queryKey: ["sensors", "recent", limit],
    queryFn: () => fetchRecentSensors(limit),
    refetchInterval: 5_000,
  });
}

export function useTrafficSummary() {
  return useQuery({
    queryKey: ["traffic", "summary"],
    queryFn: fetchTrafficSummary,
    refetchInterval: 10_000,
  });
}
