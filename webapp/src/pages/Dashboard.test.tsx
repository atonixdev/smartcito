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
  demoSmartMapDevices: [
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

describe("Dashboard", () => {
  it("renders the command center layout", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /pretoria command center/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /operational map and live layers/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /drone view/i })).toBeInTheDocument();
    expect(screen.getByText(/flight controls/i)).toBeInTheDocument();
    expect(screen.getByText(/live telemetry and logs/i)).toBeInTheDocument();
    expect(screen.getByText(/telemetry, alerts, and commands/i)).toBeInTheDocument();
  });
});