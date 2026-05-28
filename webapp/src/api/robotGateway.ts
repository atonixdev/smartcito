import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const robotGateway = axios.create({
  baseURL: import.meta.env.VITE_ROBOT_GATEWAY_BASE_URL ?? "/robot-gateway",
  timeout: 10_000,
});

export type RobotStatus = "idle" | "patrolling" | "holding" | "inspecting" | "docking" | "offline" | "error";
export type RobotRegistryStatus = "online" | "degraded" | "offline" | "maintenance";
export type RobotCommandAction = "move_forward" | "move_reverse" | "turn_left" | "turn_right" | "hold" | "dock" | "set_waypoint" | "follow_route";

export interface GeoPoint {
  latitude: number;
  longitude: number;
  altitude_m?: number | null;
}

export interface RobotGatewayReady {
  service: string;
  topics: Record<string, string>;
  protocols: string[];
  registry: string;
}

export interface RobotCapabilities {
  robot_id: string;
  model: string;
  firmware_version: string;
  max_speed_mps: number;
  battery_capacity_mah: number;
  camera_ids: string[];
  sensors: string[];
  autonomy_modes: string[];
  lidar_supported: boolean;
  status: RobotRegistryStatus;
  protocol: string;
  last_seen_at: string;
}

export interface RobotTelemetry {
  robot_id: string;
  protocol: string;
  position: GeoPoint;
  speed_mps: number;
  heading_deg: number;
  battery_percent: number;
  autonomy_state: string;
  status: RobotStatus;
  slam_state: string;
  health_flags: string[];
  timestamp: string;
  capabilities?: RobotCapabilities | null;
}

export interface RobotPatrolRoute {
  route_id: string;
  robot_id: string;
  name: string;
  status: "draft" | "assigned" | "running" | "paused" | "completed";
  checkpoints: string[];
  path: GeoPoint[];
  updated_at: string;
}

export interface RobotFleet {
  robots: RobotTelemetry[];
  registry: RobotCapabilities[];
  routes: RobotPatrolRoute[];
}

export interface RobotCommand {
  robot_id: string;
  action: RobotCommandAction;
  target?: GeoPoint | null;
  path?: GeoPoint[];
  requested_by?: string;
}

export interface RobotCommandAck {
  command_id: string;
  robot_id: string;
  action: RobotCommandAction;
  accepted: boolean;
  adapter_status: string;
}

export const demoRobotFleet: RobotFleet = {
  robots: [
    {
      robot_id: "robot-patrol-007",
      protocol: "simulated",
      position: { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
      speed_mps: 1.8,
      heading_deg: 124,
      battery_percent: 81,
      autonomy_state: "route_follow",
      status: "patrolling",
      slam_state: "locked",
      health_flags: [],
      timestamp: new Date().toISOString(),
    },
    {
      robot_id: "robot-tunnel-003",
      protocol: "simulated",
      position: { latitude: -25.7481, longitude: 28.2329, altitude_m: 0 },
      speed_mps: 1.1,
      heading_deg: 88,
      battery_percent: 63,
      autonomy_state: "inspection_hold",
      status: "inspecting",
      slam_state: "constrained",
      health_flags: ["wheel-slip"],
      timestamp: new Date().toISOString(),
    },
  ],
  registry: [
    {
      robot_id: "robot-patrol-007",
      model: "Orca Patrol UGV",
      firmware_version: "ugv-2.4.1",
      max_speed_mps: 3.5,
      battery_capacity_mah: 18000,
      camera_ids: ["front-main", "rear-assist"],
      sensors: ["lidar", "ultrasonic", "ir", "imu", "vibration"],
      autonomy_modes: ["manual", "route_follow", "inspection_hold", "dock"],
      lidar_supported: true,
      status: "online",
      protocol: "simulated",
      last_seen_at: new Date().toISOString(),
    },
    {
      robot_id: "robot-tunnel-003",
      model: "Orca Tunnel Inspector",
      firmware_version: "tunnel-1.8.0",
      max_speed_mps: 2.2,
      battery_capacity_mah: 15000,
      camera_ids: ["nav-main"],
      sensors: ["lidar", "ultrasonic", "gas", "thermal", "wheel-slip"],
      autonomy_modes: ["manual", "inspection_hold", "dock"],
      lidar_supported: true,
      status: "degraded",
      protocol: "simulated",
      last_seen_at: new Date().toISOString(),
    },
  ],
  routes: [
    {
      route_id: "route-robot-patrol-007",
      robot_id: "robot-patrol-007",
      name: "Perimeter patrol alpha",
      status: "assigned",
      checkpoints: ["North gate", "Utility corridor", "Transit plaza", "Depot entry"],
      path: [
        { latitude: -25.7467, longitude: 28.2368, altitude_m: 0 },
        { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
      ],
      updated_at: new Date().toISOString(),
    },
    {
      route_id: "route-robot-tunnel-003",
      robot_id: "robot-tunnel-003",
      name: "Tunnel south loop",
      status: "assigned",
      checkpoints: ["Tunnel south", "Valve chamber", "Service hatch", "Return bay"],
      path: [
        { latitude: -25.7486, longitude: 28.2324, altitude_m: 0 },
        { latitude: -25.7481, longitude: 28.2329, altitude_m: 0 },
      ],
      updated_at: new Date().toISOString(),
    },
  ],
};

export async function fetchRobotGatewayReady(): Promise<RobotGatewayReady> {
  const { data } = await robotGateway.get<RobotGatewayReady>("/ready");
  return data;
}

export async function fetchRobotFleet(): Promise<RobotFleet> {
  const { data } = await robotGateway.get<RobotFleet>("/robots");
  return data;
}

export async function sendRobotCommand(command: RobotCommand): Promise<RobotCommandAck> {
  const { data } = await robotGateway.post<RobotCommandAck>(`/robots/${command.robot_id}/commands`, command);
  return data;
}

export function useRobotGatewayReady() {
  return useQuery({
    queryKey: ["robot-gateway", "ready"],
    queryFn: fetchRobotGatewayReady,
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useRobotFleet() {
  return useQuery({
    queryKey: ["robot-gateway", "fleet"],
    queryFn: fetchRobotFleet,
    refetchInterval: 5_000,
    retry: 1,
  });
}

export function useSendRobotCommand() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendRobotCommand,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["robot-gateway", "fleet"] });
    },
  });
}