/**
 * ============================================================================
 * File: webapp/src/api/droneGateway.ts
 * Purpose:
 *   Typed React Query client for the Orca Drone Gateway. The dashboard
 *   talks to the gateway through the web proxy, never directly to drones.
 * ============================================================================
 */

import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const droneGateway = axios.create({
  baseURL: import.meta.env.VITE_DRONE_GATEWAY_BASE_URL ?? "/drone-gateway",
  timeout: 10_000,
});

const missionControl = axios.create({
  baseURL: import.meta.env.VITE_MISSION_CONTROL_BASE_URL ?? "/mission-control",
  timeout: 10_000,
});

const droneCamera = axios.create({
  baseURL: import.meta.env.VITE_DRONE_CAMERA_BASE_URL ?? "/drone-camera",
  timeout: 10_000,
});

const threatDetection = axios.create({
  baseURL: import.meta.env.VITE_THREAT_DETECTION_BASE_URL ?? "/threat-detection",
  timeout: 10_000,
});

const mappingGeospatial = axios.create({
  baseURL: import.meta.env.VITE_MAPPING_GEOSPATIAL_BASE_URL ?? "/mapping-geospatial",
  timeout: 10_000,
});

export type DroneStatus = "idle" | "in_mission" | "hovering" | "returning" | "landed" | "error";
export type DroneCommandAction =
  | "takeoff"
  | "land"
  | "move_to"
  | "change_altitude"
  | "follow_path"
  | "hover"
  | "return_to_base"
  | "start_camera_stream"
  | "stop_camera_stream"
  | "camera_zoom"
  | "gimbal_move";

export interface GeoPoint {
  latitude: number;
  longitude: number;
  altitude_m?: number | null;
}

export interface DroneGatewayReady {
  service: string;
  topics: Record<string, string>;
  protocols: string[];
  registry: string;
}

export interface DroneCapabilities {
  drone_id: string;
  model: string;
  firmware_version: string;
  max_speed_mps: number;
  max_altitude_m: number;
  battery_capacity_mah: number;
  camera_types: string[];
  sensors: string[];
  payload_supported: boolean;
  status: "online" | "offline" | "maintenance";
  protocol: string;
  last_seen_at: string;
}

export interface DroneTelemetry {
  drone_id: string;
  protocol: string;
  position: GeoPoint;
  speed_mps: number;
  heading_deg: number;
  battery_percent: number;
  link_quality?: number | null;
  flight_mode: string;
  status: DroneStatus;
  health_flags: string[];
  timestamp: string;
  capabilities?: DroneCapabilities | null;
}

export interface DroneFleet {
  drones: DroneTelemetry[];
  registry: DroneCapabilities[];
}

export interface DroneCommand {
  drone_id: string;
  action: DroneCommandAction;
  target?: GeoPoint | null;
  path?: GeoPoint[];
  altitude_m?: number | null;
  camera_id?: string | null;
  zoom_level?: number | null;
  gimbal_pitch_deg?: number | null;
  gimbal_yaw_deg?: number | null;
  requested_by?: string;
}

export interface DroneCommandAck {
  command_id: string;
  drone_id: string;
  action: DroneCommandAction;
  accepted: boolean;
  adapter_status: string;
}

export interface DroneConnectionRequest {
  drone_id: string;
  protocol: "mavlink" | "rest" | "websocket" | "vendor-sdk" | "simulated";
  endpoint?: string | null;
  auth_profile?: string | null;
}

export interface MissionWaypoint extends GeoPoint {
  hold_seconds?: number;
}

export interface DroneMission {
  mission_id: string;
  drone_id: string;
  name: string;
  status: "draft" | "uploaded" | "running" | "paused" | "completed" | "failed";
  altitude_m: number;
  speed_mps: number;
  progress_percent: number;
  waypoints: MissionWaypoint[];
}

export interface MissionUploadRequest {
  drone_id: string;
  name: string;
  altitude_m: number;
  speed_mps: number;
  waypoints: MissionWaypoint[];
}

export interface CameraFeedStatus {
  drone_id: string;
  stream_url: string;
  preview_url?: string | null;
  camera_id: string;
  ai_detections: Array<{ label: string; confidence: number }>;
  gimbal: { pitch_deg: number; yaw_deg: number; zoom_level: number };
}

export interface ThreatAlertSummary {
  alert_id: string;
  title: string;
  threat_level: "low" | "medium" | "high" | "critical";
  source_ids: string[];
  confidence: number;
  recommended_actions: string[];
}

export interface MappingOverlaySummary {
  drones: unknown[];
  sensors: unknown[];
  threats: unknown[];
  geofences: unknown[];
}

export interface MappingGeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    id?: string;
    geometry: { type: string; coordinates: unknown };
    properties?: Record<string, unknown>;
  }>;
}

export interface MappingGeofenceDataset {
  geojson: MappingGeoJsonFeatureCollection;
  overlays: Array<{
    overlay_id: string;
    overlay_type: string;
    label: string;
    position?: GeoPoint | null;
    metadata: Record<string, unknown>;
  }>;
}

export interface MappingSearchResult {
  name: string;
  display_name: string;
  type: string;
  zone: string;
  geometry: { type: string; coordinates: unknown };
}

export interface MappingSearchResponse {
  query: string;
  radius_km: number;
  source: string;
  results: MappingSearchResult[];
  geojson: MappingGeoJsonFeatureCollection;
  radius: { type: string; coordinates: unknown } | null;
}

export interface MappingCityMapResponse {
  html: string;
  geojson_layers: Record<string, MappingGeoJsonFeatureCollection | { type: string; coordinates: unknown } | null>;
  marker_layers: Record<string, Array<Record<string, unknown>>>;
}

export const demoDroneFleet: DroneFleet = {
  drones: [
    {
      drone_id: "drone-patrol-001",
      protocol: "simulated",
      position: { latitude: -25.7454, longitude: 28.2438, altitude_m: 95 },
      speed_mps: 8.2,
      heading_deg: 90,
      battery_percent: 87,
      link_quality: 0.96,
      flight_mode: "patrol",
      status: "in_mission",
      health_flags: [],
      timestamp: new Date().toISOString(),
    },
  ],
  registry: [
    {
      drone_id: "drone-patrol-001",
      model: "Orca Simulated Patrol Drone",
      firmware_version: "sim-1.0.0",
      max_speed_mps: 18,
      max_altitude_m: 500,
      battery_capacity_mah: 6000,
      camera_types: ["rgb", "thermal", "zoom"],
      sensors: ["gps", "imu", "barometer", "link-quality"],
      payload_supported: true,
      status: "online",
      protocol: "simulated",
      last_seen_at: new Date().toISOString(),
    },
  ],
};

export const demoDroneMission: DroneMission = {
  mission_id: "mission-patrol-cbd-001",
  drone_id: "drone-patrol-001",
  name: "CBD perimeter patrol",
  status: "uploaded",
  altitude_m: 95,
  speed_mps: 8,
  progress_percent: 42,
  waypoints: [
    { latitude: -25.7479, longitude: 28.2293, altitude_m: 95, hold_seconds: 10 },
    { latitude: -25.7461, longitude: 28.2361, altitude_m: 95, hold_seconds: 8 },
    { latitude: -25.7454, longitude: 28.2438, altitude_m: 95, hold_seconds: 12 },
  ],
};

export const demoCameraFeed: CameraFeedStatus = {
  drone_id: "drone-patrol-001",
  stream_url: "rtsp://drone-patrol-001/camera/main",
  preview_url: "/drone-camera/streams/drone-patrol-001/preview",
  camera_id: "rgb-main",
  ai_detections: [
    { label: "vehicle", confidence: 0.91 },
    { label: "perimeter motion", confidence: 0.82 },
  ],
  gimbal: { pitch_deg: -18, yaw_deg: 32, zoom_level: 3 },
};

export const demoThreatAlerts: ThreatAlertSummary[] = [
  {
    alert_id: "threat-drone-patrol-001",
    title: "High surveillance event: perimeter motion",
    threat_level: "high",
    source_ids: ["drone-patrol-001", "perimeter-sensor-003"],
    confidence: 0.86,
    recommended_actions: ["notify-operator", "start-recording", "dispatch-nearest-drone"],
  },
];

export async function fetchDroneGatewayReady(): Promise<DroneGatewayReady> {
  const { data } = await droneGateway.get<DroneGatewayReady>("/ready");
  return data;
}

export async function fetchDroneFleet(): Promise<DroneFleet> {
  const { data } = await droneGateway.get<DroneFleet>("/drones");
  return data;
}

export async function fetchDroneMetrics(): Promise<string> {
  const { data } = await droneGateway.get<string>("/metrics", { responseType: "text" });
  return data;
}

export async function connectDrone(request: DroneConnectionRequest): Promise<DroneCapabilities> {
  const { data } = await droneGateway.post<DroneCapabilities>("/connect", request);
  return data;
}

export async function sendDroneCommand(command: DroneCommand): Promise<DroneCommandAck> {
  const { data } = await droneGateway.post<DroneCommandAck>(`/drones/${command.drone_id}/commands`, command);
  return data;
}

export async function fetchDroneMissions(): Promise<DroneMission[]> {
  const { data } = await missionControl.get<DroneMission[]>("/missions");
  return data;
}

export async function uploadDroneMission(request: MissionUploadRequest): Promise<DroneMission> {
  const { data } = await missionControl.post<DroneMission>("/missions", request);
  return data;
}

export async function fetchCameraFeeds(): Promise<CameraFeedStatus[]> {
  const { data } = await droneCamera.get<CameraFeedStatus[]>("/feeds");
  return data;
}

export async function fetchThreatAlerts(): Promise<ThreatAlertSummary[]> {
  const { data } = await threatDetection.get<{ alerts: ThreatAlertSummary[] } | ThreatAlertSummary[]>("/alerts");
  return Array.isArray(data) ? data : data.alerts;
}

export async function fetchMappingOverlays(): Promise<MappingOverlaySummary> {
  const { data } = await mappingGeospatial.get<MappingOverlaySummary>("/overlays");
  return data;
}

export async function fetchMappingGeofences(): Promise<MappingGeofenceDataset> {
  const { data } = await mappingGeospatial.get<MappingGeofenceDataset>("/geofences");
  return data;
}

export async function searchMappingLocations(query: string, radiusKm: number): Promise<MappingSearchResponse> {
  const { data } = await mappingGeospatial.get<MappingSearchResponse>("/search", {
    params: { query, radius_km: radiusKm },
  });
  return data;
}

export async function fetchCityMapPayload(): Promise<MappingCityMapResponse> {
  const { data } = await mappingGeospatial.get<MappingCityMapResponse>("/maps/city");
  return data;
}

export function useDroneGatewayReady() {
  return useQuery({
    queryKey: ["drone-gateway", "ready"],
    queryFn: fetchDroneGatewayReady,
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useDroneFleet() {
  return useQuery({
    queryKey: ["drone-gateway", "fleet"],
    queryFn: fetchDroneFleet,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useDroneGatewayMetrics() {
  return useQuery({
    queryKey: ["drone-gateway", "metrics"],
    queryFn: fetchDroneMetrics,
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useConnectDrone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: connectDrone,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["drone-gateway", "fleet"] }),
        queryClient.invalidateQueries({ queryKey: ["drone-gateway", "ready"] }),
        queryClient.invalidateQueries({ queryKey: ["drone-gateway", "metrics"] }),
      ]);
    },
  });
}

export function useSendDroneCommand() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendDroneCommand,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["drone-gateway", "fleet"] }),
        queryClient.invalidateQueries({ queryKey: ["drone-gateway", "metrics"] }),
      ]);
    },
  });
}

export function useDroneMissions() {
  return useQuery({
    queryKey: ["mission-control", "missions"],
    queryFn: fetchDroneMissions,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useUploadDroneMission() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadDroneMission,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mission-control", "missions"] });
    },
  });
}

export function useCameraFeeds() {
  return useQuery({
    queryKey: ["drone-camera", "feeds"],
    queryFn: fetchCameraFeeds,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useThreatAlerts() {
  return useQuery({
    queryKey: ["threat-detection", "alerts"],
    queryFn: fetchThreatAlerts,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useMappingOverlays() {
  return useQuery({
    queryKey: ["mapping-geospatial", "overlays"],
    queryFn: fetchMappingOverlays,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useMappingGeofences() {
  return useQuery({
    queryKey: ["mapping-geospatial", "geofences"],
    queryFn: fetchMappingGeofences,
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useMappingSearch(query: string, radiusKm: number) {
  return useQuery({
    queryKey: ["mapping-geospatial", "search", query, radiusKm],
    queryFn: () => searchMappingLocations(query, radiusKm),
    enabled: query.trim().length > 0,
    refetchInterval: 30_000,
    retry: 1,
  });
}

export function useCityMapPayload() {
  return useQuery({
    queryKey: ["mapping-geospatial", "city-map"],
    queryFn: fetchCityMapPayload,
    refetchInterval: 15_000,
    retry: 1,
  });
}
