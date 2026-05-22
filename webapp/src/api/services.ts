import { useQuery } from "@tanstack/react-query";
import { api, gpsApi, locationApi } from "./client";

export interface ServiceHealth {
  name: string;
  status: "live" | "degraded" | "offline";
  detail: string;
}

async function checkService(
  name: string,
  request: () => Promise<unknown>,
): Promise<ServiceHealth> {
  try {
    await request();
    return { name, status: "live", detail: "connected" };
  } catch {
    return { name, status: "offline", detail: "not reachable" };
  }
}

export async function fetchServiceHealth(): Promise<ServiceHealth[]> {
  const [fastapi, location, gps] = await Promise.all([
    checkService("FastAPI Backend", () => api.get("/health/live")),
    checkService("Location / Map API", () => locationApi.get("/health")),
    checkService("GPS Service", () => gpsApi.get("/health")),
  ]);

  return [fastapi, location, gps];
}

export function useServiceHealth() {
  return useQuery({
    queryKey: ["services", "health"],
    queryFn: fetchServiceHealth,
    refetchInterval: 5_000,
  });
}
