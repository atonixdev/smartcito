/**
 * ============================================================================
 * File: webapp/src/api/sensors.ts
 * Purpose:
 *   Typed API helpers for the /sensors and /traffic endpoints, plus React
 *   Query hooks that components can drop in without touching axios.
 * ============================================================================
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";

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

// These calls resolve to:
// frontend /api/v1/sensors/recent -> Vite proxy -> http://localhost:8000/api/v1/sensors/recent
const BACKEND_ENABLED = import.meta.env.VITE_ENABLE_BACKEND === "true";

const demoSensorReadings: SensorReading[] = [
  {
    id: "demo-reading-001",
    sensor_id: "IOT-44",
    kind: "air_quality",
    value: 42,
    unit: "AQI",
    latitude: -1.3102,
    longitude: 36.8388,
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    metadata: { source: "demo", area: "Industrial Area" },
  },
  {
    id: "demo-reading-002",
    sensor_id: "GPS-07",
    kind: "traffic",
    value: 87,
    unit: "vehicles/min",
    latitude: -1.2655,
    longitude: 36.8054,
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    metadata: { source: "demo", area: "Westlands" },
  },
  {
    id: "demo-reading-003",
    sensor_id: "PI-NBO-01",
    kind: "other",
    value: 51,
    unit: "celsius",
    latitude: -1.2921,
    longitude: 36.8219,
    observed_at: new Date().toISOString(),
    received_at: new Date().toISOString(),
    metadata: { source: "demo", metric: "cpu_temp" },
  },
];

const demoTrafficSummary: TrafficSummary = {
  total_samples: 80,
  sensors: [
    {
      sensor_id: "traffic-cbd-001",
      samples: 48,
      average_value: 87,
      unit: "vehicles/min",
    },
    {
      sensor_id: "traffic-westlands-002",
      samples: 32,
      average_value: 54,
      unit: "vehicles/min",
    },
  ],
};

export async function fetchRecentSensors(limit = 50): Promise<SensorReading[]> {
  if (!BACKEND_ENABLED) {
    return demoSensorReadings.slice(0, limit);
  }

  try {
    return await apiClient.get<SensorReading[]>("/sensors/recent", {
      params: { limit },
    });
  } catch {
    return demoSensorReadings.slice(0, limit);
  }
}

export async function fetchTrafficSummary(): Promise<TrafficSummary> {
  if (!BACKEND_ENABLED) {
    return demoTrafficSummary;
  }

  try {
    return await apiClient.get<TrafficSummary>("/traffic/summary");
  } catch {
    return demoTrafficSummary;
  }
}

// ---------- React Query hooks ----------

/** Poll the recent-readings endpoint every 5 seconds for live dashboards. */
export function useRecentSensors(limit = 50) {
  return useQuery({
    queryKey: ["sensors", "recent", limit],
    queryFn: () => fetchRecentSensors(limit),
    refetchInterval: BACKEND_ENABLED ? 5_000 : false,
  });
}

export function useTrafficSummary() {
  return useQuery({
    queryKey: ["traffic", "summary"],
    queryFn: fetchTrafficSummary,
    refetchInterval: BACKEND_ENABLED ? 10_000 : false,
  });
}
