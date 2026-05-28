import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import RobotDashboard from "./RobotDashboard";

vi.mock("@/components/CommandCenterMap", () => ({
  default: () => <div aria-label="Orca city command map" />,
}));

vi.mock("@/api/map", () => ({
  demoSmartMapDevices: [
    {
      id: "demo-map-camera-001",
      device_id: "demo-body-001",
      name: "Pretoria Camera Node",
      device_type: "camera",
      latitude: -25.7479,
      longitude: 28.2293,
      trust_score: 92,
      trust_level: "verified",
      camera_feed_url: "rtsp://edge/demo-body-001/camera",
      sensor_type: "camera-feed",
      sensor_value: 0.74,
      gps_path: [[-25.749, 28.2281], [-25.7479, 28.2293]],
      last_seen_at: new Date().toISOString(),
    },
  ],
  useSmartMapOverview: () => ({
    data: {
      devices: [
        {
          id: "demo-map-camera-001",
          device_id: "demo-body-001",
          name: "Pretoria Camera Node",
          device_type: "camera",
          latitude: -25.7479,
          longitude: 28.2293,
          trust_score: 92,
          trust_level: "verified",
          camera_feed_url: "rtsp://edge/demo-body-001/camera",
          sensor_type: "camera-feed",
          sensor_value: 0.74,
          gps_path: [[-25.749, 28.2281], [-25.7479, 28.2293]],
          last_seen_at: new Date().toISOString(),
        },
      ],
    },
  }),
}));

vi.mock("@/api/sensors", () => ({
  useRecentSensors: () => ({
    data: [
      {
        id: "reading-1",
        sensor_id: "robot-prox-1",
        kind: "energy",
        value: 0.7,
        unit: "m",
        latitude: -25.7462,
        longitude: 28.2372,
        observed_at: new Date().toISOString(),
        received_at: new Date().toISOString(),
        metadata: {},
      },
    ],
  }),
}));

vi.mock("@/api/robotGateway", () => ({
  demoRobotFleet: {
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
    ],
    registry: [
      {
        robot_id: "robot-patrol-007",
        model: "Orca Patrol UGV",
        firmware_version: "ugv-2.4.1",
        max_speed_mps: 3.5,
        battery_capacity_mah: 18000,
        camera_ids: ["front-main"],
        sensors: ["lidar", "ultrasonic", "ir"],
        autonomy_modes: ["manual", "route_follow"],
        lidar_supported: true,
        status: "online",
        protocol: "simulated",
        last_seen_at: new Date().toISOString(),
      },
    ],
    routes: [
      {
        route_id: "route-1",
        robot_id: "robot-patrol-007",
        name: "Perimeter patrol alpha",
        status: "assigned",
        checkpoints: ["North gate", "Transit plaza"],
        path: [
          { latitude: -25.7467, longitude: 28.2368, altitude_m: 0 },
          { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
        ],
        updated_at: new Date().toISOString(),
      },
    ],
  },
  useRobotGatewayReady: () => ({ data: { registry: "in-memory" } }),
  useRobotFleet: () => ({
    data: {
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
      ],
      registry: [
        {
          robot_id: "robot-patrol-007",
          model: "Orca Patrol UGV",
          firmware_version: "ugv-2.4.1",
          max_speed_mps: 3.5,
          battery_capacity_mah: 18000,
          camera_ids: ["front-main"],
          sensors: ["lidar", "ultrasonic", "ir"],
          autonomy_modes: ["manual", "route_follow"],
          lidar_supported: true,
          status: "online",
          protocol: "simulated",
          last_seen_at: new Date().toISOString(),
        },
      ],
      routes: [
        {
          route_id: "route-1",
          robot_id: "robot-patrol-007",
          name: "Perimeter patrol alpha",
          status: "assigned",
          checkpoints: ["North gate", "Transit plaza"],
          path: [
            { latitude: -25.7467, longitude: 28.2368, altitude_m: 0 },
            { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
          ],
          updated_at: new Date().toISOString(),
        },
      ],
    },
  }),
  useSendRobotCommand: () => ({ isPending: false, mutate: vi.fn() }),
}));

vi.mock("@/api/droneGateway", () => ({
  useMappingGeofences: () => ({
    data: {
      geojson: { type: "FeatureCollection", features: [] },
      overlays: [],
    },
  }),
  useCityMapPayload: () => ({
    data: {
      html: "<div>map</div>",
      geojson_layers: {
        sensors: { type: "FeatureCollection", features: [] },
        cameras: { type: "FeatureCollection", features: [] },
        robot_paths: { type: "FeatureCollection", features: [] },
        mission_routes: { type: "FeatureCollection", features: [] },
      },
      marker_layers: {},
    },
  }),
}));

describe("RobotDashboard", () => {
  it("renders the ground robotics operator view", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/dashboard/robot"]}>
          <RobotDashboard />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /Ground Robotics Control/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Ground navigation map/i })).toBeInTheDocument();
    expect(screen.getByText(/Forward vision/i)).toBeInTheDocument();
    expect(screen.getByText(/Patrol routes/i)).toBeInTheDocument();
    expect(screen.getByText(/Health and obstacle channels/i)).toBeInTheDocument();
  });
});