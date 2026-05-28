import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import DroneDashboard from "./DroneDashboard";

vi.mock("@/components/CommandCenterMap", () => ({
  default: () => <div aria-label="Orca city command map" />,
}));

vi.mock("@/api/droneGateway", () => ({
  demoDroneFleet: {
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
        camera_types: ["rgb", "thermal"],
        sensors: ["gps", "imu"],
        payload_supported: true,
        status: "online",
        protocol: "simulated",
        last_seen_at: new Date().toISOString(),
      },
    ],
  },
  demoDroneMission: {
    mission_id: "mission-1",
    drone_id: "drone-patrol-001",
    name: "CBD patrol",
    status: "uploaded",
    altitude_m: 95,
    speed_mps: 8,
    progress_percent: 42,
    waypoints: [
      { latitude: -25.7479, longitude: 28.2293, altitude_m: 95, hold_seconds: 10 },
      { latitude: -25.7461, longitude: 28.2361, altitude_m: 95, hold_seconds: 8 },
    ],
  },
  demoCameraFeed: {
    drone_id: "drone-patrol-001",
    stream_url: "rtsp://drone-patrol-001/camera/main",
    preview_url: "/drone-camera/streams/drone-patrol-001/preview",
    camera_id: "rgb-main",
    ai_detections: [{ label: "vehicle", confidence: 0.91 }],
    gimbal: { pitch_deg: -18, yaw_deg: 32, zoom_level: 3 },
  },
  demoThreatAlerts: [
    {
      alert_id: "threat-1",
      title: "Perimeter motion",
      threat_level: "high",
      source_ids: ["drone-patrol-001"],
      confidence: 0.86,
      recommended_actions: ["notify-operator"],
    },
  ],
  useDroneGatewayReady: () => ({ data: { registry: "online", service: "drone-gateway", protocols: ["simulated"] } }),
  useDroneFleet: () => ({
    data: {
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
          camera_types: ["rgb", "thermal"],
          sensors: ["gps", "imu"],
          payload_supported: true,
          status: "online",
          protocol: "simulated",
          last_seen_at: new Date().toISOString(),
        },
      ],
    },
  }),
  useDroneGatewayMetrics: () => ({ data: "orca_drone_gateway_events_total{event=\"telemetry_received\"} 4" }),
  useDroneMissions: () => ({
    data: [
      {
        mission_id: "mission-1",
        drone_id: "drone-patrol-001",
        name: "CBD patrol",
        status: "uploaded",
        altitude_m: 95,
        speed_mps: 8,
        progress_percent: 42,
        waypoints: [
          { latitude: -25.7479, longitude: 28.2293, altitude_m: 95, hold_seconds: 10 },
          { latitude: -25.7461, longitude: 28.2361, altitude_m: 95, hold_seconds: 8 },
        ],
      },
    ],
  }),
  useMappingOverlays: () => ({ data: { geofences: [{ id: "zone-1" }], sensors: [{ id: "sensor-1" }], threats: [], drones: [] } }),
  useMappingGeofences: () => ({ data: { geojson: { type: "FeatureCollection", features: [] }, overlays: [] } }),
  useCityMapPayload: () => ({
    data: {
      html: "<div>map</div>",
      geojson_layers: {
        sensors: { type: "FeatureCollection", features: [] },
        cameras: { type: "FeatureCollection", features: [] },
        drone_paths: { type: "FeatureCollection", features: [] },
        mission_routes: { type: "FeatureCollection", features: [] },
      },
      marker_layers: {},
    },
  }),
  useCameraFeeds: () => ({
    data: [
      {
        drone_id: "drone-patrol-001",
        stream_url: "rtsp://drone-patrol-001/camera/main",
        preview_url: "/drone-camera/streams/drone-patrol-001/preview",
        camera_id: "rgb-main",
        ai_detections: [{ label: "vehicle", confidence: 0.91 }],
        gimbal: { pitch_deg: -18, yaw_deg: 32, zoom_level: 3 },
      },
    ],
  }),
  useThreatAlerts: () => ({
    data: [
      {
        alert_id: "threat-1",
        title: "Perimeter motion",
        threat_level: "high",
        source_ids: ["drone-patrol-001"],
        confidence: 0.86,
        recommended_actions: ["notify-operator"],
      },
    ],
  }),
  useConnectDrone: () => ({ isPending: false, mutate: vi.fn() }),
  useSendDroneCommand: () => ({ isPending: false, mutate: vi.fn() }),
  useUploadDroneMission: () => ({ isPending: false, mutate: vi.fn() }),
}));

describe("DroneDashboard", () => {
  it("renders the drone operator map with centralized geographic layers", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/dashboard/drone"]}>
          <DroneDashboard />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /Flight Operations Console/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Live Map View/i })).toBeInTheDocument();
    expect(screen.getByText(/Mission Planner/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Orca city command map/i)).toBeInTheDocument();
  });
});