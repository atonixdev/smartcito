import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { GeoPoint } from "./droneGateway";

const missionControl = axios.create({
  baseURL: import.meta.env.VITE_MISSION_CONTROL_BASE_URL ?? "/mission-control",
  timeout: 10_000,
});

export type MissionAssetType = "drone" | "robot";

export interface CityMissionAssignment {
  asset_type: MissionAssetType;
  asset_id: string;
  path: GeoPoint[];
  altitude_m?: number | null;
  speed_mps?: number | null;
}

export interface CityMissionRequest {
  name: string;
  city: string;
  district: string;
  radius_km: number;
  assignments: CityMissionAssignment[];
}

export interface CityMissionDispatchResult {
  asset_type: MissionAssetType;
  asset_id: string;
  accepted: boolean;
  adapter_status: string;
}

export interface CityMission {
  mission_id: string;
  name: string;
  city: string;
  district: string;
  radius_km: number;
  status: "draft" | "uploaded" | "running" | "paused" | "completed" | "failed";
  assignments: CityMissionAssignment[];
  dispatch_results: CityMissionDispatchResult[];
  created_at: string;
  updated_at: string;
}

export async function fetchCityMissions(): Promise<CityMission[]> {
  const { data } = await missionControl.get<CityMission[]>("/city-missions");
  return data;
}

export async function createCityMission(request: CityMissionRequest): Promise<CityMission> {
  const { data } = await missionControl.post<CityMission>("/city-missions", request);
  return data;
}

export function useCityMissions() {
  return useQuery({
    queryKey: ["mission-control", "city-missions"],
    queryFn: fetchCityMissions,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useCreateCityMission() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCityMission,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mission-control", "city-missions"] });
    },
  });
}