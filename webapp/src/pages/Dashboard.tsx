import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import CommandCenterMap from "@/components/CommandCenterMap";
import OperationsSwitcher from "@/components/OperationsSwitcher";

import { useCameras, demoCameraFleet } from "@/api/cameras";
import { useControlPlaneOverview } from "@/api/controlPlane";
import {
  demoCameraFeed,
  demoDroneFleet,
  demoDroneMission,
  demoThreatAlerts,
  useCameraFeeds,
  useDroneFleet,
  useDroneGatewayReady,
  useDroneMissions,
  useMappingOverlays,
  useSendDroneCommand,
  useThreatAlerts,
  type DroneCommandAction,
  type DroneMission,
  type DroneTelemetry,
} from "@/api/droneGateway";
import { useAlerts, useLiveEvents } from "@/api/events";
import { demoSmartMapOverview, useSmartMapOverview, type SmartMapDevice } from "@/api/map";
import { useCreateCityMission, useCityMissions } from "@/api/missionControl";
import { useRealtimeCommandCenter } from "@/api/realtime";
import { demoRobotFleet, useRobotFleet } from "@/api/robotGateway";
import { demoSceneOverview, useSceneOverview } from "@/api/scene";
import { useRecentSensors, type SensorReading } from "@/api/sensors";

type AssetKind = "drone" | "robot" | "camera" | "sensor" | "deterrent" | "alert";
type DashboardScreen = "drone" | "map" | "logs";
type DrawMode = "mission" | "geofence" | "alert-zone" | null;
type FeedMode = "rgb" | "thermal" | "zoom";
type LogFilter = "all" | "telemetry" | "mission" | "camera" | "sensor" | "alert" | "command";
type LogSeverity = "info" | "warning" | "critical";
type CityMapMode = "2d" | "3d" | "street";

interface SelectedAsset {
  kind: AssetKind;
  id: string;
}

interface CommandCenterSensor {
  id: string;
  name: string;
  category: string;
  status: "ok" | "alert" | "offline";
  currentValue: number;
  unit: string;
  lastTriggeredAt: string;
  latitude: number;
  longitude: number;
  linkedCameraIds: string[];
  linkedDroneIds: string[];
  history: SensorReading[];
}

interface DeterrentAsset {
  id: string;
  name: string;
  status: "armed" | "disarmed" | "active";
  zone: string;
  latitude: number;
  longitude: number;
  linkedSensorIds: string[];
  authorizedRoles: string[];
  rule: string;
}

interface RobotAsset {
  id: string;
  name: string;
  status: "nominal" | "degraded" | "offline";
  mission: string;
  batteryPercent: number;
  latitude: number;
  longitude: number;
  routeLabel: string;
}

interface ZoneOverlay {
  id: string;
  label: string;
  kind: "critical" | "restricted" | "geofence";
  top: number;
  left: number;
  width: number;
  height: number;
}

interface MapPoint {
  latitude: number;
  longitude: number;
}

interface CommandLogEntry {
  id: string;
  category: Exclude<LogFilter, "all">;
  severity: LogSeverity;
  message: string;
  timestamp: string;
  assetId?: string;
  sourceLabel: string;
  rawPacket: string;
  rosMessage: string;
}

interface AssetListItem {
  id: string;
  kind: Exclude<AssetKind, "alert">;
  label: string;
  status: string;
  subtitle: string;
  latitude: number;
  longitude: number;
}

const cityName = "Pretoria Command Center";
const operatorName = "Primary Operator";

const demoRobots: RobotAsset[] = [
  {
    id: "robot-patrol-007",
    name: "UGV Patrol 007",
    status: "nominal",
    mission: "Perimeter route alpha",
    batteryPercent: 81,
    latitude: -25.7462,
    longitude: 28.2372,
    routeLabel: "North gate to transit plaza",
  },
  {
    id: "robot-tunnel-003",
    name: "Tunnel Robot 003",
    status: "degraded",
    mission: "Tunnel inspection",
    batteryPercent: 63,
    latitude: -25.7481,
    longitude: 28.2329,
    routeLabel: "Utility tunnel south loop",
  },
];

const citySearchPresets = [
  {
    id: "joburg-winchester",
    city: "Johannesburg",
    district: "Winchester",
    radiusKm: 5,
    detail: "Street-level sweep of Winchester logistics and arterial roads.",
  },
  {
    id: "pretoria-cbd",
    city: "Pretoria",
    district: "CBD",
    radiusKm: 4,
    detail: "Command-center focus around civic district cameras and air corridors.",
  },
  {
    id: "cape-town-foreshore",
    city: "Cape Town",
    district: "Foreshore",
    radiusKm: 6,
    detail: "Waterfront perimeter, transport nodes, and public-safety sensors.",
  },
] as const;

const demoDeterrents: DeterrentAsset[] = [
  {
    id: "deterrent-zone-a-siren",
    name: "Zone A Smart Siren",
    status: "armed",
    zone: "CBD perimeter",
    latitude: -25.7452,
    longitude: 28.2446,
    linkedSensorIds: ["sensor-em-001", "sensor-motion-004"],
    authorizedRoles: ["supervisor", "incident_commander"],
    rule: "If intrusion in Zone A, trigger siren and dispatch nearest drone.",
  },
  {
    id: "deterrent-plaza-light-02",
    name: "Transit Plaza Floodlight",
    status: "disarmed",
    zone: "Transit plaza",
    latitude: -25.7484,
    longitude: 28.2314,
    linkedSensorIds: ["sensor-vibration-002"],
    authorizedRoles: ["supervisor"],
    rule: "Auto-enable on after-hours motion and camera confirmation.",
  },
];

const zoneOverlays: ZoneOverlay[] = [
  { id: "zone-cbd", label: "CBD perimeter", kind: "critical", top: 18, left: 50, width: 24, height: 28 },
  { id: "zone-government", label: "Restricted district", kind: "restricted", top: 46, left: 18, width: 22, height: 20 },
  { id: "zone-logistics", label: "Logistics geofence", kind: "geofence", top: 56, left: 58, width: 20, height: 18 },
];

const fallbackSensors: Array<Omit<CommandCenterSensor, "history">> = [
  {
    id: "sensor-em-001",
    name: "Magnetic Wave Grid A1",
    category: "magnetic/em",
    status: "alert",
    currentValue: 13.4,
    unit: "mT",
    lastTriggeredAt: new Date().toISOString(),
    latitude: -25.7448,
    longitude: 28.2455,
    linkedCameraIds: ["demo-body-001"],
    linkedDroneIds: ["drone-patrol-001"],
  },
  {
    id: "sensor-vibration-002",
    name: "Utility Tunnel Vibration 02",
    category: "vibration",
    status: "ok",
    currentValue: 0.22,
    unit: "g",
    lastTriggeredAt: new Date(Date.now() - 28 * 60 * 1000).toISOString(),
    latitude: -25.7481,
    longitude: 28.232,
    linkedCameraIds: ["demo-micro-007"],
    linkedDroneIds: [],
  },
  {
    id: "sensor-motion-004",
    name: "Perimeter Beam 04",
    category: "motion",
    status: "offline",
    currentValue: 0,
    unit: "state",
    lastTriggeredAt: new Date(Date.now() - 95 * 60 * 1000).toISOString(),
    latitude: -25.7472,
    longitude: 28.2394,
    linkedCameraIds: ["demo-body-001"],
    linkedDroneIds: ["drone-patrol-001"],
  },
];

function formatTime(isoTimestamp: string) {
  return new Intl.DateTimeFormat("en-ZA", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(isoTimestamp));
}

function formatClock(date: Date) {
  return new Intl.DateTimeFormat("en-ZA", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes("critical") || normalized.includes("error") || normalized.includes("offline")) {
    return "critical";
  }
  if (normalized.includes("high") || normalized.includes("alert") || normalized.includes("active") || normalized.includes("armed")) {
    return "warning";
  }
  return "healthy";
}

function toSensorCategory(kind: SensorReading["kind"]) {
  switch (kind) {
    case "air_quality":
      return "air quality";
    case "traffic":
      return "motion";
    case "water":
      return "perimeter";
    case "energy":
      return "magnetic/em";
    case "cctv":
      return "camera trigger";
    default:
      return "sensor";
  }
}

function CommandStatusBadge({ label }: { label: string }) {
  return <span className={`command-badge ${getStatusTone(label)}`}>{label}</span>;
}

function resolveCoordinates(deviceId: string, mapDevices: SmartMapDevice[], fallbackLatitude: number, fallbackLongitude: number) {
  const device = mapDevices.find(
    (candidate) => candidate.device_id === deviceId || candidate.id === deviceId || candidate.name === deviceId,
  );

  return {
    latitude: device?.latitude ?? fallbackLatitude,
    longitude: device?.longitude ?? fallbackLongitude,
  };
}

function buildCsv(records: CommandLogEntry[]) {
  const header = ["timestamp", "type", "severity", "source", "asset_id", "message", "mavlink", "ros2"];
  const rows = records.map((record) => [
    record.timestamp,
    record.category,
    record.severity,
    record.sourceLabel,
    record.assetId ?? "",
    record.message,
    record.rawPacket,
    record.rosMessage,
  ]);

  return [header, ...rows]
    .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n");
}

function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}

export default function Dashboard() {
  const [clock, setClock] = useState(() => new Date());
  const [activeScreen, setActiveScreen] = useState<DashboardScreen>("map");
  const [selectedAsset, setSelectedAsset] = useState<SelectedAsset | null>(null);
  const [selectedDroneId, setSelectedDroneId] = useState("");
  const [selectedMissionId, setSelectedMissionId] = useState("");
  const [selectedAlertId, setSelectedAlertId] = useState("");
  const [selectedFeedMode, setSelectedFeedMode] = useState<FeedMode>("rgb");
  const [drawMode, setDrawMode] = useState<DrawMode>("mission");
  const [drawPoints, setDrawPoints] = useState<MapPoint[]>([]);
  const [logFilter, setLogFilter] = useState<LogFilter>("all");
  const [logSeverityFilter, setLogSeverityFilter] = useState<"all" | LogSeverity>("all");
  const [logDroneFilter, setLogDroneFilter] = useState("all");
  const [logDateFilter, setLogDateFilter] = useState("");
  const [selectedLogId, setSelectedLogId] = useState("");
  const [localLogs, setLocalLogs] = useState<CommandLogEntry[]>([]);
  const [assetFilter, setAssetFilter] = useState("");
  const [mapMode, setMapMode] = useState<CityMapMode>("3d");
  const [selectedSearchId, setSelectedSearchId] = useState(citySearchPresets[0].id);
  const [selectedRobotIds, setSelectedRobotIds] = useState<string[]>([]);
  const deferredAssetFilter = useDeferredValue(assetFilter);
  const [recordingEnabled, setRecordingEnabled] = useState(false);
  const realtime = useRealtimeCommandCenter(true);

  const gatewayReady = useDroneGatewayReady();
  const droneFleetQuery = useDroneFleet();
  const droneMissionsQuery = useDroneMissions();
  const cameraFeedsQuery = useCameraFeeds();
  const threatAlertsQuery = useThreatAlerts();
  const mappingOverlaysQuery = useMappingOverlays();
  const cameraQuery = useCameras();
  const recentSensorsQuery = useRecentSensors(18);
  const liveEventsQuery = useLiveEvents();
  const eventAlertsQuery = useAlerts();
  const controlPlaneQuery = useControlPlaneOverview();
  const sendDroneCommand = useSendDroneCommand();
  const smartMapQuery = useSmartMapOverview();
  const sceneOverviewQuery = useSceneOverview();
  const robotFleetQuery = useRobotFleet();
  const cityMissionsQuery = useCityMissions();
  const createCityMission = useCreateCityMission();

  const realtimeSurveillance = realtime.snapshot?.surveillance;
  const realtimeControlPlane = realtime.snapshot?.control_plane as {
    data_flow?: Array<{ destination: string; state: string }>;
    security?: { audit_pipeline_status?: string };
    controls?: Array<unknown>;
  } | undefined;
  const realtimeMap = realtime.snapshot?.map as { devices?: SmartMapDevice[] } | undefined;
  const realtimeFleet = realtimeSurveillance?.drones as unknown as typeof demoDroneFleet | undefined;
  const realtimeMissions = realtimeSurveillance?.missions as unknown as DroneMission[] | undefined;
  const realtimeCameraFeeds = realtimeSurveillance?.camera_feeds as unknown as Array<typeof demoCameraFeed> | undefined;
  const realtimeThreatAlerts = realtimeSurveillance?.threat_alerts as unknown as typeof demoThreatAlerts | undefined;
  const realtimeEvents = realtime.snapshot?.events as Array<{
    event_id: string;
    source: string;
    event_type: string;
    occurred_at: string;
  }> | undefined;
  const realtimeAlerts = realtime.snapshot?.alerts as Array<{
    id: string;
    severity: string;
    title: string;
    message: string;
    created_at: string;
  }> | undefined;

  useEffect(() => {
    const timerId = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timerId);
  }, []);

  const fleet =
    realtimeFleet && (Array.isArray(realtimeFleet.drones) || Array.isArray(realtimeFleet.registry))
      ? realtimeFleet
      : droneFleetQuery.data && (droneFleetQuery.data.drones.length > 0 || droneFleetQuery.data.registry.length > 0)
        ? droneFleetQuery.data
        : demoDroneFleet;

  const droneTelemetries = fleet.drones.length > 0 ? fleet.drones : demoDroneFleet.drones;
  const droneRegistry = fleet.registry.length > 0 ? fleet.registry : demoDroneFleet.registry;
  const missionItems = Array.isArray(realtimeMissions) && realtimeMissions.length > 0
    ? realtimeMissions
    : droneMissionsQuery.data && droneMissionsQuery.data.length > 0
      ? droneMissionsQuery.data
      : [demoDroneMission];
  const cameraDevices = cameraQuery.data && cameraQuery.data.length > 0 ? cameraQuery.data : demoCameraFleet;
  const cameraFeeds = Array.isArray(realtimeCameraFeeds) && realtimeCameraFeeds.length > 0
    ? realtimeCameraFeeds
    : cameraFeedsQuery.data && cameraFeedsQuery.data.length > 0
      ? cameraFeedsQuery.data
      : [demoCameraFeed];
  const smartMapOverview = smartMapQuery.data && smartMapQuery.data.devices.length > 0
    ? smartMapQuery.data
    : demoSmartMapOverview;
  const mapDevices = realtimeMap?.devices && realtimeMap.devices.length > 0
    ? realtimeMap.devices
    : smartMapOverview.devices;
  const threatAlerts = Array.isArray(realtimeThreatAlerts) && realtimeThreatAlerts.length > 0
    ? realtimeThreatAlerts
    : threatAlertsQuery.data && threatAlertsQuery.data.length > 0
      ? threatAlertsQuery.data
      : demoThreatAlerts;
  const eventAlerts = realtimeAlerts ?? eventAlertsQuery.data ?? [];
  const liveEvents = realtimeEvents ?? liveEventsQuery.data ?? [];
  const robotFleet = robotFleetQuery.data && robotFleetQuery.data.registry.length > 0 ? robotFleetQuery.data : demoRobotFleet;
  const robotRegistry = robotFleet.registry;
  const robotTelemetries = robotFleet.robots;
  const robotRoutes = robotFleet.routes;
  const sceneOverview = sceneOverviewQuery.data && sceneOverviewQuery.data.devices.length > 0
    ? sceneOverviewQuery.data
    : demoSceneOverview;
  const cameraCorridors = smartMapOverview.camera_corridors;
  const overlayCounts = realtimeSurveillance?.mapping_overlays && typeof realtimeSurveillance.mapping_overlays === "object"
    ? (realtimeSurveillance.mapping_overlays as { drones: unknown[]; sensors: unknown[]; threats: unknown[]; geofences: unknown[] })
    : mappingOverlaysQuery.data ?? { drones: [], sensors: [], threats: [], geofences: [] };
  const serviceHealth = controlPlaneQuery.data;
  const recentReadings = recentSensorsQuery.data ?? [];

  const sensors: CommandCenterSensor[] = fallbackSensors.map((sensor) => ({
    ...sensor,
    history: recentReadings.filter((reading) => reading.sensor_id === sensor.id).slice(0, 4),
  }));

  for (const reading of recentReadings) {
    if (sensors.some((sensor) => sensor.id === reading.sensor_id)) {
      continue;
    }

    const coordinates = resolveCoordinates(reading.sensor_id, mapDevices, reading.latitude ?? -25.7465, reading.longitude ?? 28.236);
    sensors.push({
      id: reading.sensor_id,
      name: reading.sensor_id,
      category: toSensorCategory(reading.kind),
      status: reading.value > 0.8 ? "alert" : "ok",
      currentValue: reading.value,
      unit: reading.unit,
      lastTriggeredAt: reading.observed_at,
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
      linkedCameraIds: [],
      linkedDroneIds: [],
      history: recentReadings.filter((candidate) => candidate.sensor_id === reading.sensor_id).slice(0, 4),
    });
  }

  const drones: AssetListItem[] = droneRegistry.map((registryEntry, index) => {
    const telemetry = droneTelemetries.find((candidate) => candidate.drone_id === registryEntry.drone_id);
    const coordinates = resolveCoordinates(registryEntry.drone_id, mapDevices, -25.7454 + index * 0.0012, 28.2438 - index * 0.0011);

    return {
      id: registryEntry.drone_id,
      kind: "drone",
      label: registryEntry.model,
      status: telemetry?.status ?? registryEntry.status,
      subtitle: telemetry
        ? `${Math.round(telemetry.battery_percent)}% battery · ${telemetry.flight_mode}`
        : `${registryEntry.protocol} · ${registryEntry.status}`,
      latitude: telemetry?.position.latitude ?? coordinates.latitude,
      longitude: telemetry?.position.longitude ?? coordinates.longitude,
    };
  });

  const cameras: AssetListItem[] = cameraDevices.map((camera, index) => {
    const coordinates = resolveCoordinates(camera.device_id, mapDevices, -25.7479 + index * 0.0012, 28.2293 + index * 0.0011);
    return {
      id: camera.device_id,
      kind: "camera",
      label: camera.device_id,
      status: camera.stream_status,
      subtitle: `${camera.device_type} · ${camera.battery_level ?? 100}% battery`,
      latitude: camera.location?.lat ?? coordinates.latitude,
      longitude: camera.location?.lon ?? coordinates.longitude,
    };
  });

  const sensorAssets: AssetListItem[] = sensors.map((sensor) => ({
    id: sensor.id,
    kind: "sensor",
    label: sensor.name,
    status: sensor.status,
    subtitle: `${sensor.category} · ${sensor.currentValue} ${sensor.unit}`,
    latitude: sensor.latitude,
    longitude: sensor.longitude,
  }));

  const deterrentAssets: AssetListItem[] = demoDeterrents.map((device) => ({
    id: device.id,
    kind: "deterrent",
    label: device.name,
    status: device.status,
    subtitle: `${device.zone} · ${device.authorizedRoles.join(", ")}`,
    latitude: device.latitude,
    longitude: device.longitude,
  }));

  const robotAssets: AssetListItem[] = robotRegistry.map((robot) => {
    const telemetry = robotTelemetries.find((candidate) => candidate.robot_id === robot.robot_id);
    const route = robotRoutes.find((candidate) => candidate.robot_id === robot.robot_id);
    return {
      id: robot.robot_id,
      kind: "robot",
      label: robot.model,
      status: robot.status,
      subtitle: `${route?.name ?? telemetry?.autonomy_state ?? "route follow"} · ${Math.round(telemetry?.battery_percent ?? 0)}% battery`,
      latitude: telemetry?.position.latitude ?? -25.7462,
      longitude: telemetry?.position.longitude ?? 28.2372,
    };
  });

  const assetCatalog = useMemo(
    () => [...drones, ...robotAssets, ...cameras, ...sensorAssets, ...deterrentAssets],
    [cameras, deterrentAssets, drones, robotAssets, sensorAssets],
  );

  const filteredAssets = deferredAssetFilter.trim().length === 0
    ? assetCatalog
    : assetCatalog.filter((asset) =>
        `${asset.label} ${asset.subtitle} ${asset.kind}`.toLowerCase().includes(deferredAssetFilter.toLowerCase()),
      );

  useEffect(() => {
    if (!selectedDroneId && drones.length > 0) {
      setSelectedDroneId(drones[0].id);
    }
  }, [drones, selectedDroneId]);

  useEffect(() => {
    if (!selectedMissionId && missionItems.length > 0) {
      setSelectedMissionId(missionItems[0].mission_id);
    }
  }, [missionItems, selectedMissionId]);

  useEffect(() => {
    if (!selectedAlertId && threatAlerts.length > 0) {
      setSelectedAlertId(threatAlerts[0].alert_id);
    }
  }, [selectedAlertId, threatAlerts]);

  useEffect(() => {
    if (!selectedAsset && drones.length > 0) {
      setSelectedAsset({ kind: "drone", id: drones[0].id });
    }
  }, [drones, selectedAsset]);

  useEffect(() => {
    if (selectedRobotIds.length > 0 || robotRegistry.length === 0) {
      return;
    }

    setSelectedRobotIds(robotRegistry.filter((robot) => robot.status !== "offline").map((robot) => robot.robot_id));
  }, [robotRegistry, selectedRobotIds.length]);

  const focusedDroneId = selectedDroneId || drones[0]?.id || "";
  const activeDroneTelemetry = droneTelemetries.find((telemetry) => telemetry.drone_id === focusedDroneId) ?? droneTelemetries[0] ?? null;
  const activeDroneRegistry = droneRegistry.find((registryEntry) => registryEntry.drone_id === focusedDroneId) ?? droneRegistry[0] ?? null;
  const activeDroneMission = missionItems.find((mission) => mission.mission_id === selectedMissionId)
    ?? missionItems.find((mission) => mission.drone_id === focusedDroneId)
    ?? missionItems[0]
    ?? null;
  const activeDroneFeed = cameraFeeds.find((feed) => feed.drone_id === focusedDroneId) ?? cameraFeeds[0] ?? null;
  const activeThreatAlert = threatAlerts.find((alert) => alert.alert_id === selectedAlertId) ?? threatAlerts[0] ?? null;

  const telemetryPosition = activeDroneTelemetry?.position ?? { latitude: drones[0]?.latitude ?? -25.7454, longitude: drones[0]?.longitude ?? 28.2438, altitude_m: 95 };
  const availableFeedModes = (activeDroneRegistry?.camera_types ?? ["rgb", "thermal", "zoom"])
    .filter((cameraType): cameraType is FeedMode => cameraType === "rgb" || cameraType === "thermal" || cameraType === "zoom");

  function appendLocalLog(
    category: Exclude<LogFilter, "all">,
    message: string,
    options?: { severity?: LogSeverity; assetId?: string; sourceLabel?: string },
  ) {
    setLocalLogs((currentLogs) => [
      {
        id: `${category}-${Date.now()}`,
        category,
        severity: options?.severity ?? "info",
        message,
        timestamp: new Date().toISOString(),
        assetId: options?.assetId,
        sourceLabel: options?.sourceLabel ?? activeDroneRegistry?.model ?? operatorName,
        rawPacket: `MAVLINK[${category.toUpperCase()}] ${message}`,
        rosMessage: `topic=/smartcito/${category} payload=${message}`,
      },
      ...currentLogs,
    ].slice(0, 32));
  }

  function selectAsset(kind: SelectedAsset["kind"], id: string) {
    startTransition(() => setSelectedAsset({ kind, id }));
    if (kind === "drone") {
      setSelectedDroneId(id);
    }
    if (kind === "alert") {
      setSelectedAlertId(id);
    }
  }

  function handleMapClick(nextPoint: MapPoint) {
    if (!drawMode) {
      return;
    }

    setDrawPoints((currentPoints) => [...currentPoints, nextPoint].slice(-12));
  }

  function dispatchDroneAction(action: DroneCommandAction, options?: { target?: MapPoint; altitude_m?: number; zoom_level?: number; gimbal_pitch_deg?: number; gimbal_yaw_deg?: number }) {
    if (!activeDroneRegistry) {
      return;
    }

    sendDroneCommand.mutate({
      drone_id: activeDroneRegistry.drone_id,
      action,
      requested_by: operatorName,
      target: options?.target,
      altitude_m: options?.altitude_m,
      zoom_level: options?.zoom_level,
      gimbal_pitch_deg: options?.gimbal_pitch_deg,
      gimbal_yaw_deg: options?.gimbal_yaw_deg,
    });

    appendLocalLog("command", `${action.replaceAll("_", " ")} sent to ${activeDroneRegistry.drone_id}`, {
      assetId: activeDroneRegistry.drone_id,
      sourceLabel: activeDroneRegistry.model,
      severity: action === "land" ? "warning" : "info",
    });
  }

  function handleGimbalMove(pitchDelta: number, yawDelta: number) {
    dispatchDroneAction("gimbal_move", {
      gimbal_pitch_deg: (activeDroneFeed?.gimbal.pitch_deg ?? 0) + pitchDelta,
      gimbal_yaw_deg: (activeDroneFeed?.gimbal.yaw_deg ?? 0) + yawDelta,
    });
  }

  function handleQuickMissionUpload() {
    const selectedRobots = robotRegistry.filter((robot) => selectedRobotIds.includes(robot.robot_id));
    if (!activeDroneRegistry || drawPoints.length < 2) {
      appendLocalLog("mission", "Quick mission requires at least two map points.", {
        severity: "critical",
        assetId: focusedDroneId,
      });
      return;
    }

    if (selectedRobots.length === 0) {
      appendLocalLog("mission", "Select at least one robot before assigning a city mission.", {
        severity: "warning",
        assetId: focusedDroneId,
      });
      return;
    }

    createCityMission.mutate({
      name: `${selectedSearch.city} ${selectedSearch.district} coordinated patrol`,
      city: selectedSearch.city,
      district: selectedSearch.district,
      radius_km: selectedSearch.radiusKm,
      assignments: [
        {
          asset_type: "drone",
          asset_id: activeDroneRegistry.drone_id,
          altitude_m: activeDroneTelemetry?.position.altitude_m ?? 90,
          speed_mps: activeDroneTelemetry?.speed_mps ?? 8,
          path: drawPoints,
        },
        ...selectedRobots.map((robot) => ({
          asset_type: "robot" as const,
          asset_id: robot.robot_id,
          speed_mps: Math.min(robot.max_speed_mps, 2),
          path: drawPoints.map((point) => ({ latitude: point.latitude, longitude: point.longitude, altitude_m: 0 })),
        })),
      ],
    });

    appendLocalLog("mission", `City mission dispatched to ${activeDroneRegistry.drone_id} and ${selectedRobots.map((robot) => robot.robot_id).join(", ")}`, {
      assetId: activeDroneRegistry.drone_id,
      sourceLabel: activeDroneRegistry.model,
    });
  }

  function toggleRobotSelection(robotId: string) {
    setSelectedRobotIds((currentRobotIds) => (
      currentRobotIds.includes(robotId)
        ? currentRobotIds.filter((currentRobotId) => currentRobotId !== robotId)
        : [...currentRobotIds, robotId]
    ));
  }

  function handleGoHere() {
    const lastPoint = drawPoints.at(-1);
    if (!activeDroneRegistry || !lastPoint) {
      appendLocalLog("mission", "Go Here requires one selected point on the map.", {
        severity: "warning",
        assetId: focusedDroneId,
      });
      return;
    }

    dispatchDroneAction("move_to", { target: lastPoint, altitude_m: activeDroneTelemetry?.position.altitude_m ?? 90 });
    appendLocalLog("mission", `Go Here command queued for ${activeDroneRegistry.drone_id}`, {
      assetId: activeDroneRegistry.drone_id,
      sourceLabel: activeDroneRegistry.model,
    });
  }

  const telemetryLogs: CommandLogEntry[] = droneTelemetries.map((telemetry: DroneTelemetry) => ({
    id: `${telemetry.drone_id}-${telemetry.timestamp}`,
    category: "telemetry",
    severity: telemetry.health_flags.length > 0 ? "critical" : "info",
    message: `${telemetry.drone_id} · ${Math.round(telemetry.battery_percent)}% battery · ${telemetry.flight_mode} · ${telemetry.speed_mps.toFixed(1)} m/s`,
    timestamp: telemetry.timestamp,
    assetId: telemetry.drone_id,
    sourceLabel: telemetry.drone_id,
    rawPacket: `HEARTBEAT mode=${telemetry.flight_mode} battery=${Math.round(telemetry.battery_percent)}`,
    rosMessage: `topic=/drone/${telemetry.drone_id}/telemetry speed=${telemetry.speed_mps.toFixed(1)}`,
  }));

  const missionLogs: CommandLogEntry[] = missionItems.map((mission) => ({
    id: `${mission.mission_id}-mission`,
    category: "mission",
    severity: mission.progress_percent >= 80 ? "info" : "warning",
    message: `${mission.name} · ${mission.progress_percent}% complete · ${mission.waypoints.length} waypoints`,
    timestamp: new Date().toISOString(),
    assetId: mission.drone_id,
    sourceLabel: mission.name,
    rawPacket: `MISSION_ITEM_INT count=${mission.waypoints.length} altitude=${mission.altitude_m}`,
    rosMessage: `topic=/mission/${mission.mission_id}/status progress=${mission.progress_percent}`,
  }));

  const cameraLogs: CommandLogEntry[] = cameraFeeds.map((feed) => ({
    id: `${feed.camera_id}-${feed.drone_id}-camera`,
    category: "camera",
    severity: feed.ai_detections.length > 0 ? "warning" : "info",
    message: `${feed.camera_id} · ${feed.ai_detections.length} detections · zoom ${feed.gimbal.zoom_level}x`,
    timestamp: new Date().toISOString(),
    assetId: feed.drone_id,
    sourceLabel: feed.camera_id,
    rawPacket: `CAMERA_FEEDBACK zoom=${feed.gimbal.zoom_level} yaw=${feed.gimbal.yaw_deg}`,
    rosMessage: `topic=/camera/${feed.camera_id}/detections count=${feed.ai_detections.length}`,
  }));

  const sensorLogs: CommandLogEntry[] = sensors.map((sensor) => ({
    id: `${sensor.id}-${sensor.lastTriggeredAt}`,
    category: "sensor",
    severity: sensor.status === "offline" ? "critical" : sensor.status === "alert" ? "warning" : "info",
    message: `${sensor.name} · ${sensor.currentValue} ${sensor.unit} · ${sensor.status}`,
    timestamp: sensor.lastTriggeredAt,
    assetId: sensor.linkedDroneIds[0],
    sourceLabel: sensor.name,
    rawPacket: `SENSOR_REPORT id=${sensor.id} value=${sensor.currentValue}`,
    rosMessage: `topic=/sensor/${sensor.id}/reading value=${sensor.currentValue}`,
  }));

  const alertLogs: CommandLogEntry[] = eventAlerts.map((entry) => ({
    id: entry.id,
    category: "alert",
    severity: entry.severity.toLowerCase() === "critical" ? "critical" : "warning",
    message: `${entry.title} · ${entry.message}`,
    timestamp: entry.created_at,
    assetId: activeThreatAlert?.source_ids[0],
    sourceLabel: entry.title,
    rawPacket: `ALERT severity=${entry.severity} id=${entry.id}`,
    rosMessage: `topic=/alerts/${entry.id} severity=${entry.severity}`,
  }));

  const eventCommandLogs: CommandLogEntry[] = liveEvents.map((entry) => ({
    id: entry.event_id,
    category: entry.event_type.includes("command") ? "command" : "telemetry",
    severity: entry.event_type.includes("alert") ? "warning" : "info",
    message: `${entry.source} · ${entry.event_type}`,
    timestamp: entry.occurred_at,
    assetId: entry.source,
    sourceLabel: entry.source,
    rawPacket: `EVENT type=${entry.event_type} source=${entry.source}`,
    rosMessage: `topic=/events/${entry.source} type=${entry.event_type}`,
  }));

  const combinedLogs = [...localLogs, ...alertLogs, ...eventCommandLogs, ...telemetryLogs, ...missionLogs, ...cameraLogs, ...sensorLogs]
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime());

  const filteredLogs = combinedLogs.filter((entry) => {
    if (logFilter !== "all" && entry.category !== logFilter) {
      return false;
    }
    if (logSeverityFilter !== "all" && entry.severity !== logSeverityFilter) {
      return false;
    }
    if (logDroneFilter !== "all" && entry.assetId !== logDroneFilter) {
      return false;
    }
    if (logDateFilter) {
      const entryDate = new Date(entry.timestamp).toISOString().slice(0, 10);
      if (entryDate !== logDateFilter) {
        return false;
      }
    }
    return true;
  });

  useEffect(() => {
    if (!selectedLogId && filteredLogs.length > 0) {
      setSelectedLogId(filteredLogs[0].id);
    }
  }, [filteredLogs, selectedLogId]);

  useEffect(() => {
    if (selectedLogId && !filteredLogs.some((entry) => entry.id === selectedLogId)) {
      setSelectedLogId(filteredLogs[0]?.id ?? "");
    }
  }, [filteredLogs, selectedLogId]);

  const selectedLog = filteredLogs.find((entry) => entry.id === selectedLogId) ?? filteredLogs[0] ?? null;
  const selectedAssetSummary = selectedAsset ? assetCatalog.find((asset) => asset.id === selectedAsset.id) ?? null : null;
  const mapAssets = useMemo(
    () => [...drones, ...robotAssets, ...cameras, ...sensorAssets, ...deterrentAssets],
    [cameras, deterrentAssets, drones, robotAssets, sensorAssets],
  );
  const selectedSearch = citySearchPresets.find((preset) => preset.id === selectedSearchId) ?? citySearchPresets[0];

  const systemHealthCards = [
    { label: "Realtime bus", value: realtime.connected ? "streaming" : "fallback polling" },
    { label: "Drone Gateway", value: gatewayReady.data || realtimeSurveillance?.drones ? "online" : "degraded" },
    { label: "Robot Gateway", value: robotRegistry.some((robot) => robot.status !== "offline") ? "online" : "watch" },
    { label: "Kafka", value: (realtimeControlPlane?.data_flow ?? serviceHealth?.data_flow)?.some((stage) => stage.destination === "kafka" && stage.state === "healthy") ? "healthy" : "watch" },
    { label: "Database", value: realtimeControlPlane?.security?.audit_pipeline_status ?? serviceHealth?.security.audit_pipeline_status ?? "watch" },
    { label: "Mission Control", value: missionItems.length > 0 ? "ready" : "watch" },
    { label: "Global alerts", value: `${threatAlerts.length}` },
  ];

  function exportLogs(format: "csv" | "json") {
    if (format === "csv") {
      downloadTextFile(`smartcito-logs-${Date.now()}.csv`, buildCsv(filteredLogs), "text/csv;charset=utf-8");
      return;
    }

    downloadTextFile(
      `smartcito-logs-${Date.now()}.json`,
      JSON.stringify(filteredLogs, null, 2),
      "application/json;charset=utf-8",
    );
  }

  return (
    <section className="command-center" aria-label="City command center dashboard">
      <header className="command-topbar">
        <div className="command-topbar-block">
          <span className="command-kicker">City map dashboard</span>
          <h2>{cityName}</h2>
          <p>Strategic command view for city-wide mapping, device search, geofences, alert zones, drones, robots, cameras, and deterrent assets.</p>
        </div>

        <div className="command-topbar-meta">
          <div>
            <span>System status</span>
            <strong>{gatewayReady.data ? "Nominal" : "Partial visibility"}</strong>
          </div>
          <div>
            <span>Coverage</span>
            <strong>{selectedSearch.city} · {selectedSearch.district}</strong>
          </div>
          <div>
            <span>Local time</span>
            <strong>{formatClock(clock)}</strong>
          </div>
          <button className="command-alert-pill" type="button" onClick={() => setActiveScreen("logs")}>
            {threatAlerts.length} global alerts
          </button>
        </div>
      </header>

      <OperationsSwitcher />

      <nav className="command-tab-nav" aria-label="Dashboard screens">
        {([
          { id: "map", label: "City Map", description: "2D / 3D command view" },
          { id: "logs", label: "Operations Logs", description: "Exports + analysis" },
        ] as const).map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`command-tab ${activeScreen === tab.id ? "is-active" : ""}`}
            onClick={() => setActiveScreen(tab.id)}
          >
            <strong>{tab.label}</strong>
            <span>{tab.description}</span>
          </button>
        ))}
      </nav>

      {activeScreen === "drone" ? (
        <div className="command-screen command-drone-screen">
          <section className="command-panel-shell command-drone-header">
            <div className="command-panel-header">
              <div>
                <span className="command-kicker">Drone Screen</span>
                <h3>Primary flight view</h3>
              </div>
            </div>

            <div className="command-drone-selector-row">
              <label className="command-form-block">
                <span>Drone selector</span>
                <select value={focusedDroneId} onChange={(event) => selectAsset("drone", event.target.value)}>
                  {droneRegistry.map((drone) => (
                    <option key={drone.drone_id} value={drone.drone_id}>{drone.model}</option>
                  ))}
                </select>
              </label>

              <div className="command-chip-row">
                {systemHealthCards.slice(0, 3).map((card) => (
                  <span key={card.label}>{card.label}: {card.value}</span>
                ))}
              </div>
            </div>
          </section>

          <div className="command-drone-layout">
            <section className="command-panel-shell command-drone-video-panel">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">Drone camera feed</span>
                  <h3>Full camera feed</h3>
                </div>
                <CommandStatusBadge label={selectedFeedMode} />
              </div>

              <div className="command-feed-mode-row">
                {availableFeedModes.map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    className={selectedFeedMode === mode ? "is-active" : ""}
                    onClick={() => setSelectedFeedMode(mode)}
                  >
                    {mode.toUpperCase()}
                  </button>
                ))}
              </div>

              <div className="command-video-stage">
                <div className="command-video-feed">
                  <span>{selectedFeedMode.toUpperCase()} camera stream</span>
                  <strong>{activeDroneFeed?.stream_url ?? "Awaiting stream"}</strong>
                </div>
              </div>

              <div className="command-panel-header compact">
                <div>
                  <span className="command-kicker">Gimbal controls</span>
                  <h3>Precise camera handling</h3>
                </div>
              </div>

              <div className="command-gimbal-grid">
                <button type="button" onClick={() => handleGimbalMove(8, 0)}>Tilt up</button>
                <button type="button" onClick={() => handleGimbalMove(-8, 0)}>Tilt down</button>
                <button type="button" onClick={() => handleGimbalMove(0, -12)}>Yaw left</button>
                <button type="button" onClick={() => handleGimbalMove(0, 12)}>Yaw right</button>
              </div>

              <div className="command-action-row">
                <button
                  type="button"
                  onClick={() => appendLocalLog("camera", `Snapshot captured from ${activeDroneFeed?.camera_id ?? focusedDroneId}`, {
                    assetId: focusedDroneId,
                    sourceLabel: activeDroneFeed?.camera_id ?? focusedDroneId,
                  })}
                >
                  Snapshot
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRecordingEnabled((current) => !current);
                    appendLocalLog("camera", `${recordingEnabled ? "Recording stopped" : "Recording started"} for ${focusedDroneId}`, {
                      assetId: focusedDroneId,
                      sourceLabel: activeDroneFeed?.camera_id ?? focusedDroneId,
                      severity: "warning",
                    });
                  }}
                >
                  {recordingEnabled ? "Stop record" : "Record"}
                </button>
              </div>
            </section>

            <aside className="command-panel-shell command-drone-sidebar">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">Drone telemetry panel</span>
                  <h3>Flight telemetry</h3>
                </div>
              </div>

              <div className="command-metrics-grid">
                <div><span>Battery</span><strong>{Math.round(activeDroneTelemetry?.battery_percent ?? 0)}%</strong></div>
                <div><span>GPS</span><strong>{telemetryPosition.latitude.toFixed(4)}, {telemetryPosition.longitude.toFixed(4)}</strong></div>
                <div><span>Altitude</span><strong>{Math.round(telemetryPosition.altitude_m ?? 0)} m</strong></div>
                <div><span>Speed</span><strong>{(activeDroneTelemetry?.speed_mps ?? 0).toFixed(1)} m/s</strong></div>
                <div><span>Heading</span><strong>{Math.round(activeDroneTelemetry?.heading_deg ?? 0)}°</strong></div>
                <div><span>Link quality</span><strong>{Math.round((activeDroneTelemetry?.link_quality ?? 0) * 100)}%</strong></div>
                <div><span>Flight mode</span><strong>{activeDroneTelemetry?.flight_mode ?? "standby"}</strong></div>
                <div><span>Payload status</span><strong>{activeDroneRegistry?.payload_supported ? "ready" : "offline"}</strong></div>
                <div><span>Sensor status</span><strong>{activeDroneRegistry?.sensors.join(", ") ?? "n/a"}</strong></div>
                <div><span>Mission</span><strong>{activeDroneMission?.name ?? "No mission"}</strong></div>
              </div>

              <section className="command-context-card">
                <h4>Mission snapshot</h4>
                <div className="command-mission-card">
                  <div>
                    <span>Progress</span>
                    <strong>{activeDroneMission?.progress_percent ?? 0}%</strong>
                  </div>
                  <div>
                    <span>ETA</span>
                    <strong>{Math.max(6, Math.round((100 - (activeDroneMission?.progress_percent ?? 0)) / 8))} min</strong>
                  </div>
                </div>
              </section>
            </aside>
          </div>

          <section className="command-panel-shell command-flight-bar">
            <div className="command-panel-header">
              <div>
                <span className="command-kicker">Bottom controls</span>
                <h3>Flight controls</h3>
              </div>
            </div>

            <div className="command-flight-controls-grid">
              <button type="button" onClick={() => dispatchDroneAction("takeoff")}>Takeoff</button>
              <button type="button" onClick={() => dispatchDroneAction("land")}>Land</button>
              <button type="button" onClick={() => dispatchDroneAction("return_to_base")}>Return to base</button>
              <button type="button" onClick={() => dispatchDroneAction("hover")}>Hold position</button>
              <button
                type="button"
                className="command-danger-button"
                onClick={() => appendLocalLog("command", `Emergency stop flagged for ${focusedDroneId}`, {
                  severity: "critical",
                  assetId: focusedDroneId,
                  sourceLabel: activeDroneRegistry?.model ?? focusedDroneId,
                })}
              >
                Emergency stop
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {activeScreen === "map" ? (
        <div className="command-screen command-map-screen">
          <div className="command-map-layout">
            <aside className="command-panel-shell command-map-tools">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">City search</span>
                  <h3>Command tools</h3>
                </div>
              </div>

              <label className="command-form-block">
                <span>Mission anchor drone</span>
                <select value={focusedDroneId} onChange={(event) => selectAsset("drone", event.target.value)}>
                  {droneRegistry.map((drone) => (
                    <option key={drone.drone_id} value={drone.drone_id}>{drone.model}</option>
                  ))}
                </select>
              </label>

              <label className="command-form-block">
                <span>City search</span>
                <select value={selectedSearchId} onChange={(event) => setSelectedSearchId(event.target.value)}>
                  {citySearchPresets.map((preset) => (
                    <option key={preset.id} value={preset.id}>{preset.city} → {preset.district} → {preset.radiusKm} km</option>
                  ))}
                </select>
              </label>

              <section className="command-context-card city-search-card">
                <h4>Assign robot fleet</h4>
                <p>Choose which ground units receive the shared city mission plan.</p>
                <div className="command-selection-list" role="group" aria-label="Robot mission assignees">
                  {robotRegistry.map((robot) => (
                    <label key={robot.robot_id} className="command-selection-item">
                      <input
                        type="checkbox"
                        checked={selectedRobotIds.includes(robot.robot_id)}
                        onChange={() => toggleRobotSelection(robot.robot_id)}
                      />
                      <span>{robot.model}</span>
                      <strong>{robot.status}</strong>
                    </label>
                  ))}
                </div>
              </section>

              <section className="command-context-card city-search-card">
                <h4>Search corridor</h4>
                <p>{selectedSearch.detail}</p>
                <div className="command-chip-row">
                  <span>{selectedSearch.city}</span>
                  <span>{selectedSearch.district}</span>
                  <span>{selectedSearch.radiusKm} km radius</span>
                </div>
              </section>

              <div className="command-action-stack">
                <button type="button" onClick={() => { setDrawMode("mission"); appendLocalLog("mission", "City mission planning enabled", { assetId: focusedDroneId }); }}>Create mission</button>
                <button type="button" onClick={() => { setDrawMode("mission"); appendLocalLog("mission", "City patrol route editing enabled", { assetId: focusedDroneId, severity: "warning" }); }}>Edit routes</button>
                <button type="button" onClick={handleQuickMissionUpload}>Assign mission</button>
                <button type="button" onClick={handleGoHere}>Dispatch nearest drone</button>
              </div>

              <label className="command-search">
                <span>Asset search</span>
                <input
                  value={assetFilter}
                  onChange={(event) => setAssetFilter(event.target.value)}
                  placeholder="Drone, robot, camera, sensor, deterrent"
                />
              </label>

              <div className="command-list-block">
                {filteredAssets.slice(0, 8).map((asset) => (
                  <button key={asset.id} type="button" className="command-line-button" onClick={() => selectAsset(asset.kind, asset.id)}>
                    <span>{asset.label}</span>
                    <CommandStatusBadge label={asset.status} />
                  </button>
                ))}
              </div>
            </aside>

            <main className="command-panel-shell command-map-stage-panel">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">CityView</span>
                  <h3>Strategic city map</h3>
                </div>
                <div className="command-map-actions">
                  <button type="button" className={mapMode === "2d" ? "is-active" : ""} onClick={() => setMapMode("2d")}>2D</button>
                  <button type="button" className={mapMode === "3d" ? "is-active" : ""} onClick={() => setMapMode("3d")}>3D</button>
                  <button type="button" className={mapMode === "street" ? "is-active" : ""} onClick={() => setMapMode("street")}>Street</button>
                  <button type="button" className={drawMode === "mission" ? "is-active" : ""} onClick={() => setDrawMode("mission")}>Mission route</button>
                  <button type="button" className={drawMode === "geofence" ? "is-active" : ""} onClick={() => setDrawMode("geofence")}>Geofences</button>
                  <button type="button" className={drawMode === "alert-zone" ? "is-active" : ""} onClick={() => setDrawMode("alert-zone")}>Alert zones</button>
                  <button type="button" onClick={() => setDrawPoints([])}>Clear</button>
                </div>
              </div>

              <div className="command-layer-row">
                <span>{mapMode.toUpperCase()} city view with drones, robots, patrol routes, geofences, cameras, sensors, and deterrents.</span>
                <div>
                  <CommandStatusBadge label={`${overlayCounts.geofences.length || zoneOverlays.length} zones`} />
                  <CommandStatusBadge label={`${threatAlerts.length} alerts`} />
                  <CommandStatusBadge label={`${robotAssets.length} robots`} />
                  <CommandStatusBadge label={`${sensorAssets.length} sensors`} />
                </div>
              </div>

              <div className="command-map-shell">
                <CommandCenterMap
                  assets={mapAssets}
                  threatAlerts={threatAlerts}
                  zones={zoneOverlays}
                  selectedAssetId={selectedAsset?.id ?? focusedDroneId}
                  drawPoints={drawPoints}
                  mode={mapMode}
                  sceneOverview={sceneOverview}
                  cameraCorridors={cameraCorridors}
                  onMapClick={handleMapClick}
                  onSelectAsset={(kind, id) => selectAsset(kind, id)}
                />
              </div>
            </main>

            <aside className="command-panel-shell command-map-side">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">City summary</span>
                  <h3>Strategic details</h3>
                </div>
              </div>

              <div className="command-metrics-grid">
                <div><span>City focus</span><strong>{selectedSearch.city}</strong></div>
                <div><span>District</span><strong>{selectedSearch.district}</strong></div>
                <div><span>Radius</span><strong>{selectedSearch.radiusKm} km</strong></div>
                <div><span>Map mode</span><strong>{mapMode.toUpperCase()}</strong></div>
                <div><span>Robots online</span><strong>{robotAssets.length}</strong></div>
                <div><span>Robot assignees</span><strong>{selectedRobotIds.length}</strong></div>
                <div><span>Cameras online</span><strong>{cameras.length}</strong></div>
                <div><span>Sensors online</span><strong>{sensorAssets.length}</strong></div>
                <div><span>City missions</span><strong>{cityMissionsQuery.data?.length ?? 0}</strong></div>
              </div>

              <section className="command-context-card">
                <h4>Patrol routes</h4>
                <div className="command-history-list">
                  {(robotRoutes.length > 0 ? robotRoutes : demoRobotFleet.routes).slice(0, 4).map((robot, index) => (
                    <div key={robot.route_id} className="command-history-row">
                      <span>Route {index + 1}</span>
                      <strong>{robot.name}</strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="command-context-card">
                <h4>Street-level navigation</h4>
                <div className="command-map-summary">
                  <strong>{selectedSearch.city} → {selectedSearch.district}</strong>
                  <span>{mapMode === "street" ? "Street camera corridors and curb-level navigation are active." : "Switch to Street mode for curb-level navigation lanes."}</span>
                  <CommandStatusBadge label={mapMode === "street" ? "street ready" : "3d overview"} />
                </div>
              </section>

              <section className="command-context-card">
                <h4>Mission logs</h4>
                <div className="command-log-list compact">
                  {combinedLogs.filter((entry) => entry.category === "mission" && entry.assetId === focusedDroneId).slice(0, 5).map((entry) => (
                    <div key={entry.id} className={`command-log-entry ${entry.category}`}>
                      <span>{formatTime(entry.timestamp)}</span>
                      <strong>{entry.severity}</strong>
                      <p>{entry.message}</p>
                    </div>
                  ))}
                </div>
              </section>

              {selectedAssetSummary ? (
                <section className="command-context-card">
                  <h4>Selected asset</h4>
                  <div className="command-map-summary">
                    <strong>{selectedAssetSummary.label}</strong>
                    <span>{selectedAssetSummary.subtitle}</span>
                    <CommandStatusBadge label={selectedAssetSummary.status} />
                  </div>
                </section>
              ) : null}
            </aside>
          </div>

          <footer className="command-panel-shell command-gps-strip">
            <div><span>Lat/Lon</span><strong>{telemetryPosition.latitude.toFixed(5)}, {telemetryPosition.longitude.toFixed(5)}</strong></div>
            <div><span>Altitude</span><strong>{Math.round(telemetryPosition.altitude_m ?? 0)} m</strong></div>
            <div><span>Speed</span><strong>{(activeDroneTelemetry?.speed_mps ?? 0).toFixed(1)} m/s</strong></div>
            <div><span>Heading</span><strong>{Math.round(activeDroneTelemetry?.heading_deg ?? 0)}°</strong></div>
          </footer>
        </div>
      ) : null}

      {activeScreen === "logs" ? (
        <div className="command-screen command-log-screen">
          <section className="command-panel-shell command-log-toolbar">
            <div className="command-panel-header">
              <div>
                <span className="command-kicker">Operations logs</span>
                <h3>Telemetry logs and exports</h3>
              </div>
              <div className="command-export-row">
                <button type="button" onClick={() => exportLogs("csv")}>Export CSV</button>
                <button type="button" onClick={() => exportLogs("json")}>Export JSON</button>
              </div>
            </div>

            <div className="command-log-filter-grid">
              <label className="command-form-block">
                <span>Filter by drone</span>
                <select value={logDroneFilter} onChange={(event) => setLogDroneFilter(event.target.value)}>
                  <option value="all">All drones</option>
                  {droneRegistry.map((drone) => (
                    <option key={drone.drone_id} value={drone.drone_id}>{drone.model}</option>
                  ))}
                </select>
              </label>

              <label className="command-form-block">
                <span>Filter by date</span>
                <input type="date" value={logDateFilter} onChange={(event) => setLogDateFilter(event.target.value)} />
              </label>

              <label className="command-form-block">
                <span>Filter by severity</span>
                <select value={logSeverityFilter} onChange={(event) => setLogSeverityFilter(event.target.value as "all" | LogSeverity)}>
                  <option value="all">All severities</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="critical">Critical</option>
                </select>
              </label>
            </div>

            <div className="command-log-filters">
              {(["all", "telemetry", "mission", "camera", "sensor", "alert", "command"] as const).map((filterOption) => (
                <button
                  key={filterOption}
                  type="button"
                  className={logFilter === filterOption ? "is-active" : ""}
                  onClick={() => setLogFilter(filterOption)}
                >
                  {filterOption}
                </button>
              ))}
            </div>
          </section>

          <div className="command-log-grid">
            <section className="command-panel-shell command-log-list-panel">
              <div className="command-log-list tall">
                {filteredLogs.map((entry) => (
                  <button
                    key={entry.id}
                    type="button"
                    className={`command-log-entry ${entry.category} ${selectedLog?.id === entry.id ? "is-selected" : ""}`}
                    onClick={() => setSelectedLogId(entry.id)}
                  >
                    <span>{formatTime(entry.timestamp)}</span>
                    <strong>{entry.category}</strong>
                    <p>{entry.message}</p>
                  </button>
                ))}
              </div>
            </section>

            <aside className="command-panel-shell command-log-detail">
              <div className="command-panel-header">
                <div>
                  <span className="command-kicker">Log inspection</span>
                  <h3>Raw MAVLink and ROS2</h3>
                </div>
                {selectedLog ? <CommandStatusBadge label={selectedLog.severity} /> : null}
              </div>

              {selectedLog ? (
                <div className="command-context-stack">
                  <section className="command-context-card">
                    <h4>{selectedLog.sourceLabel}</h4>
                    <div className="command-metrics-grid">
                      <div><span>Type</span><strong>{selectedLog.category}</strong></div>
                      <div><span>Severity</span><strong>{selectedLog.severity}</strong></div>
                      <div><span>Timestamp</span><strong>{formatTime(selectedLog.timestamp)}</strong></div>
                      <div><span>Drone</span><strong>{selectedLog.assetId ?? "n/a"}</strong></div>
                    </div>
                  </section>

                  <section className="command-context-card">
                    <h4>Message</h4>
                    <p>{selectedLog.message}</p>
                  </section>

                  <section className="command-context-card">
                    <h4>Raw MAVLink packets</h4>
                    <pre className="command-code-block">{selectedLog.rawPacket}</pre>
                  </section>

                  <section className="command-context-card">
                    <h4>ROS2 messages</h4>
                    <pre className="command-code-block">{selectedLog.rosMessage}</pre>
                  </section>
                </div>
              ) : (
                <section className="command-context-card">
                  <h4>No logs available</h4>
                  <p>Adjust the filters or wait for the realtime stream to emit new records.</p>
                </section>
              )}
            </aside>
          </div>

          <section className="command-panel-shell command-log-health-row">
            <div className="command-health-grid">
              {systemHealthCards.map((card) => (
                <article key={card.label} className="command-health-card">
                  <span>{card.label}</span>
                  <strong>{card.value}</strong>
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}