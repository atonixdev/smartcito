/**
 * ============================================================================
 * File: webapp/src/api/controlPlane.ts
 * Purpose:
 *   Typed dashboard control-plane client for device manager, security monitor,
 *   data flow view, and operator controls.
 * ============================================================================
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";

export type DeviceTrustLevel = "verified" | "unverified" | "blocked";
export type OperatorControlState = "running" | "stopped" | "degraded";
export type PipelineState = "healthy" | "degraded" | "blocked";

export interface ManagedDevice {
  id: string;
  name: string;
  category: "usb" | "camera" | "gps" | "iot";
  trust_level: DeviceTrustLevel;
  driver_container: string;
  endpoint: string;
  firmware_version: string;
  authenticated: boolean;
  signed_driver: boolean;
  last_seen_at: string;
}

export interface SecurityAlert {
  id: string;
  severity: string;
  title: string;
  status: string;
}

export interface SecurityMonitorStatus {
  encryption_status: string;
  iam_status: string;
  audit_pipeline_status: string;
  quantum_safe_status: string;
  intrusion_alerts: SecurityAlert[];
}

export interface DataFlowStage {
  id: string;
  name: string;
  protocol: string;
  state: PipelineState;
  throughput_hint: string;
  destination: string;
}

export interface OperatorControl {
  id: string;
  name: string;
  description: string;
  state: OperatorControlState;
  policy_mode: string;
  action_label: string;
}

export interface ControlPlaneOverview {
  devices: ManagedDevice[];
  security: SecurityMonitorStatus;
  data_flow: DataFlowStage[];
  controls: OperatorControl[];
}

export async function fetchControlPlaneOverview(): Promise<ControlPlaneOverview> {
  const { data } = await api.get<ControlPlaneOverview>("/control-plane/overview");
  return data;
}

export function useControlPlaneOverview() {
  return useQuery({
    queryKey: ["control-plane", "overview"],
    queryFn: fetchControlPlaneOverview,
    refetchInterval: 5_000,
  });
}

export function useUpdateOperatorControl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ controlId, desiredState }: { controlId: string; desiredState: OperatorControlState }) => {
      const { data } = await api.post<OperatorControl>(`/control-plane/operator-controls/${controlId}`, {
        desired_state: desiredState,
      });
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["control-plane", "overview"] });
    },
  });
}