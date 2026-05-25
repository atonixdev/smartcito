import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import Dashboard from "./Dashboard";

vi.mock("@/components/CommandCenterMap", () => ({
  default: () => <div aria-label="SmartCito city command map" />,
}));

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
}));

vi.mock("@/api/cameras", () => ({
  useCameras: () => ({
    data: [
      {
        id: "demo-body-001",
        device_id: "demo-body-001",
        device_type: "body_camera",
        firmware_version: "demo-1.0.0",
        registered_at: new Date().toISOString(),
        last_seen_at: new Date().toISOString(),
        stream_status: "live",
        location: { lat: -25.7479, lon: 28.2293, accuracy_m: 4.2 },
        battery_level: 87,
        mounted: true,
        tamper_detected: false,
      },
    ],
    isLoading: false,
    isError: false,
  }),
  demoCameraFleet: [
    {
      id: "demo-body-001",
      device_id: "demo-body-001",
      device_type: "body_camera",
      firmware_version: "demo-1.0.0",
      registered_at: new Date().toISOString(),
      last_seen_at: new Date().toISOString(),
      stream_status: "live",
      location: { lat: -25.7479, lon: 28.2293, accuracy_m: 4.2 },
      battery_level: 87,
      mounted: true,
      tamper_detected: false,
    },
  ],
}));

vi.mock("@/api/map", () => ({
  demoSmartMapOverview: {
    devices: [
      {
        id: "demo-map-camera-001",
        device_id: "demo-body-001",
        name: "Pretoria Camera Node",
        device_type: "camera",
        latitude: -25.7479,
        longitude: 28.2293,
        trust_score: 96,
        trust_level: "verified",
        camera_feed_url: "rtsp://demo/pretoria-camera-001",
        sensor_type: "camera-feed",
        sensor_value: 0.67,
        gps_path: [[-25.749, 28.2281], [-25.7484, 28.2287], [-25.7479, 28.2293]],
        last_seen_at: new Date().toISOString(),
      },
    ],
    heatmap: [],
    camera_corridors: [
      {
        id: "demo-map-camera-001-corridor",
        source_device_id: "demo-body-001",
        label: "Pretoria Camera Node corridor",
        polygon: [[-25.7475, 28.2298], [-25.7482, 28.2289], [-25.7491, 28.2282], [-25.7484, 28.2291]],
        coverage_score: 0.78,
      },
    ],
    visible_layers: ["verified-devices"],
    security_policy: "verified devices only",
  },
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
      heatmap: [],
      camera_corridors: [
        {
          id: "demo-map-camera-001-corridor",
          source_device_id: "demo-body-001",
          label: "Pretoria Camera Node corridor",
          polygon: [[-25.7475, 28.2298], [-25.7482, 28.2289], [-25.7491, 28.2282], [-25.7484, 28.2291]],
          coverage_score: 0.78,
        },
      ],
      visible_layers: ["verified-devices"],
      security_policy: "verified devices only",
    },
  }),
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
        model: "SmartCito Simulated Patrol Drone",
        firmware_version: "sim-1.0.0",
        max_speed_mps: 18,
        max_altitude_m: 500,
        battery_capacity_mah: 6000,
        camera_types: ["rgb", "thermal", "zoom"],
        sensors: ["gps", "imu", "barometer"],
        payload_supported: true,
        status: "online",
        protocol: "simulated",
        last_seen_at: new Date().toISOString(),
      },
    ],
  },
  demoDroneMission: {
    mission_id: "mission-patrol-cbd-001",
    drone_id: "drone-patrol-001",
    name: "CBD perimeter patrol",
    status: "uploaded",
    altitude_m: 95,
    speed_mps: 8,
    progress_percent: 42,
    waypoints: [
      { latitude: -25.7479, longitude: 28.2293, altitude_m: 95, hold_seconds: 10 },
      { latitude: -25.7454, longitude: 28.2438, altitude_m: 95, hold_seconds: 12 },
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
      alert_id: "threat-drone-patrol-001",
      title: "High surveillance event: perimeter motion",
      threat_level: "high",
      source_ids: ["drone-patrol-001", "perimeter-sensor-003"],
      confidence: 0.86,
      recommended_actions: ["notify-operator"],
    },
  ],
  useDroneGatewayReady: () => ({
    data: {
      service: "drone-gateway",
      topics: {
        telemetry: "smartcito.drone.telemetry",
        events: "smartcito.drone.events",
      },
      protocols: ["simulated", "mavlink"],
      registry: "synced",
    },
    isError: false,
  }),
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
          model: "SmartCito Simulated Patrol Drone",
          firmware_version: "sim-1.0.0",
          max_speed_mps: 18,
          max_altitude_m: 500,
          battery_capacity_mah: 6000,
          camera_types: ["rgb", "thermal", "zoom"],
          sensors: ["gps", "imu", "barometer"],
          payload_supported: true,
          status: "online",
          protocol: "simulated",
          last_seen_at: new Date().toISOString(),
        },
      ],
    },
  }),
  useDroneGatewayMetrics: () => ({ data: 'smartcito_drone_gateway_events_total{event="commands_accepted"} 1' }),
  useDroneMissions: () => ({ data: [] }),
  useMappingOverlays: () => ({ data: { drones: [], sensors: [], threats: [], geofences: [] } }),
  useCameraFeeds: () => ({
    data: [
      {
        drone_id: "drone-patrol-001",
        stream_url: "rtsp://drone-patrol-001/camera/main",
        preview_url: "/drone-camera/streams/drone-patrol-001/preview",
        camera_id: "demo-body-001",
        ai_detections: [{ label: "vehicle", confidence: 0.91 }],
        gimbal: { pitch_deg: -18, yaw_deg: 32, zoom_level: 3 },
      },
    ],
  }),
  useThreatAlerts: () => ({
    data: [
      {
        alert_id: "threat-drone-patrol-001",
        title: "High surveillance event: perimeter motion",
        threat_level: "high",
        source_ids: ["drone-patrol-001", "sensor-em-001"],
        confidence: 0.86,
        recommended_actions: ["notify-operator", "dispatch-nearest-drone"],
      },
    ],
  }),
  useUploadDroneMission: () => ({ isPending: false, mutate: vi.fn() }),
  useSendDroneCommand: () => ({ isPending: false, mutate: vi.fn(), data: undefined }),
}));

vi.mock("@/api/sensors", () => ({
  useRecentSensors: () => ({
    data: [
      {
        id: "reading-1",
        sensor_id: "sensor-em-001",
        kind: "energy",
        value: 13.4,
        unit: "mT",
        latitude: -25.7448,
        longitude: 28.2455,
        observed_at: new Date().toISOString(),
        received_at: new Date().toISOString(),
        metadata: {},
      },
    ],
  }),
}));

vi.mock("@/api/events", () => ({
  useLiveEvents: () => ({
    data: [
      {
        event_id: "evt-1",
        source: "drone-gateway",
        entity_id: "drone-patrol-001",
        event_type: "command.accepted",
        occurred_at: new Date().toISOString(),
        received_at: new Date().toISOString(),
        payload: {},
        metadata: {},
      },
    ],
  }),
  useAlerts: () => ({
    data: [
      {
        id: "alert-1",
        severity: "high",
        title: "Perimeter breach",
        message: "Motion and magnetic spike detected",
        created_at: new Date().toISOString(),
        payload: {},
      },
    ],
  }),
}));

vi.mock("@/api/realtime", () => ({
  useRealtimeCommandCenter: () => ({ snapshot: null, connected: false }),
}));

vi.mock("@/api/robotGateway", () => ({
  demoRobotFleet: {
    robots: [
      {
        robot_id: "robot-patrol-007",
        protocol: "simulated",
        position: { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
        speed_mps: 1.4,
        heading_deg: 118,
        battery_percent: 81,
        autonomy_state: "route_follow",
        status: "patrolling",
        slam_state: "locked",
        timestamp: new Date().toISOString(),
      },
      {
        robot_id: "robot-tunnel-003",
        protocol: "simulated",
        position: { latitude: -25.7481, longitude: 28.2329, altitude_m: 0 },
        speed_mps: 1.1,
        heading_deg: 92,
        battery_percent: 63,
        autonomy_state: "inspection",
        status: "degraded",
        slam_state: "limited",
        timestamp: new Date().toISOString(),
      },
    ],
    registry: [
      {
        robot_id: "robot-patrol-007",
        model: "UGV Patrol 007",
        firmware_version: "sim-1.0.0",
        max_speed_mps: 3,
        battery_capacity_mah: 10000,
        sensors: ["lidar"],
        payload_supported: true,
        status: "online",
        protocol: "simulated",
        last_seen_at: new Date().toISOString(),
      },
      {
        robot_id: "robot-tunnel-003",
        model: "Tunnel Robot 003",
        firmware_version: "sim-1.0.0",
        max_speed_mps: 2,
        battery_capacity_mah: 9200,
        sensors: ["lidar"],
        payload_supported: false,
        status: "degraded",
        protocol: "simulated",
        last_seen_at: new Date().toISOString(),
      },
    ],
    routes: [
      {
        route_id: "route-robot-1",
        robot_id: "robot-patrol-007",
        name: "North gate to transit plaza",
        checkpoints: ["north gate", "transit plaza"],
        path: [
          { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
          { latitude: -25.7471, longitude: 28.2351, altitude_m: 0 },
        ],
        updated_at: new Date().toISOString(),
      },
    ],
  },
  useRobotFleet: () => ({
    data: {
      robots: [
        {
          robot_id: "robot-patrol-007",
          protocol: "simulated",
          position: { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
          speed_mps: 1.4,
          heading_deg: 118,
          battery_percent: 81,
          autonomy_state: "route_follow",
          status: "patrolling",
          slam_state: "locked",
          timestamp: new Date().toISOString(),
        },
        {
          robot_id: "robot-tunnel-003",
          protocol: "simulated",
          position: { latitude: -25.7481, longitude: 28.2329, altitude_m: 0 },
          speed_mps: 1.1,
          heading_deg: 92,
          battery_percent: 63,
          autonomy_state: "inspection",
          status: "degraded",
          slam_state: "limited",
          timestamp: new Date().toISOString(),
        },
      ],
      registry: [
        {
          robot_id: "robot-patrol-007",
          model: "UGV Patrol 007",
          firmware_version: "sim-1.0.0",
          max_speed_mps: 3,
          battery_capacity_mah: 10000,
          sensors: ["lidar"],
          payload_supported: true,
          status: "online",
          protocol: "simulated",
          last_seen_at: new Date().toISOString(),
        },
        {
          robot_id: "robot-tunnel-003",
          model: "Tunnel Robot 003",
          firmware_version: "sim-1.0.0",
          max_speed_mps: 2,
          battery_capacity_mah: 9200,
          sensors: ["lidar"],
          payload_supported: false,
          status: "degraded",
          protocol: "simulated",
          last_seen_at: new Date().toISOString(),
        },
      ],
      routes: [
        {
          route_id: "route-robot-1",
          robot_id: "robot-patrol-007",
          name: "North gate to transit plaza",
          checkpoints: ["north gate", "transit plaza"],
          path: [
            { latitude: -25.7462, longitude: 28.2372, altitude_m: 0 },
            { latitude: -25.7471, longitude: 28.2351, altitude_m: 0 },
          ],
          updated_at: new Date().toISOString(),
        },
      ],
    },
  }),
}));

vi.mock("@/api/missionControl", () => ({
  useCityMissions: () => ({ data: [] }),
  useCreateCityMission: () => ({ isPending: false, mutate: vi.fn() }),
}));

vi.mock("@/api/scene", () => ({
  demoSceneOverview: {
    devices: [],
    threats: [],
    camera_corridors: [],
    layers: ["city-map"],
    camera_overlay_mode: "corridor",
    security_policy: "verified-devices",
  },
  useSceneOverview: () => ({
    data: {
      devices: [],
      threats: [],
      camera_corridors: [],
      layers: ["city-map"],
      camera_overlay_mode: "corridor",
      security_policy: "verified-devices",
    },
  }),
}));

describe("Dashboard", () => {
  it("renders the command center layout", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/dashboard/cityview"]}>
          <Dashboard />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /pretoria command center/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /City Map/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Operations Logs/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Strategic city map/i })).toBeInTheDocument();
    expect(screen.getByText(/Johannesburg → Winchester → 5 km/i)).toBeInTheDocument();
    expect(screen.getByText(/Street-level navigation/i)).toBeInTheDocument();
    expect(screen.getByRole("group", { name: /robot mission assignees/i })).toBeInTheDocument();
    expect(screen.getByText(/2 robots/i)).toBeInTheDocument();
  });
});