import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Dashboard from "./Dashboard";

vi.mock("@/api/controlPlane", () => ({
  useControlPlaneOverview: () => ({
    data: {
      devices: [
        {
          id: "usb-1",
          name: "USB GPS Receiver",
          category: "gps",
          trust_level: "verified",
          driver_container: "usb-service",
          endpoint: "/dev/ttyUSB0",
          firmware_version: "1.0.0",
          authenticated: true,
          signed_driver: true,
          last_seen_at: new Date().toISOString(),
        },
      ],
      security: {
        encryption_status: "ok",
        iam_status: "ok",
        audit_pipeline_status: "ok",
        quantum_safe_status: "ok",
        intrusion_alerts: [],
      },
      data_flow: [
        {
          id: "ingest",
          name: "Ingestion",
          protocol: "mqtt",
          state: "healthy",
          throughput_hint: "streaming",
          destination: "kafka",
        },
      ],
      controls: [
        {
          id: "usb-service",
          name: "USB Driver Service",
          description: "maps drivers",
          state: "running",
          policy_mode: "verified-only",
          action_label: "stop",
        },
      ],
    },
  }),
  useUpdateOperatorControl: () => ({ isPending: false, mutate: vi.fn() }),
}));

vi.mock("@/api/cameras", () => ({
  useCameras: () => ({ data: [], isLoading: false, isError: false }),
  demoCameraFleet: [],
}));

vi.mock("@/api/map", () => ({
  useSmartMapOverview: () => ({
    data: {
      devices: [
        {
          id: "raspi-edge-001",
          device_id: "raspi-edge-001",
          name: "Raspberry Pi Edge Node",
          device_type: "iot",
          latitude: -25.7461,
          longitude: 28.1881,
          trust_score: 92,
          trust_level: "verified",
          camera_feed_url: "rtsp://edge/raspi-edge-001/camera",
          sensor_type: "air-quality",
          sensor_value: 0.74,
          gps_path: [[-25.7472, 28.1868], [-25.7461, 28.1881]],
          last_seen_at: new Date().toISOString(),
        },
      ],
      heatmap: [],
      visible_layers: ["verified-devices"],
      security_policy: "verified devices only",
    },
  }),
}));

describe("Dashboard", () => {
  it("renders control-plane modules", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /Device Manager/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /SmartCito Map Integration/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Security Monitor/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Data Flow View/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Operator Controls/i })).toBeInTheDocument();
  });
});