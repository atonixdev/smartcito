import { startTransition, useDeferredValue, useEffect, useState, type MouseEvent } from "react";

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
  useUploadDroneMission,
  type DroneCommandAction,
  type DroneMission,
  type DroneTelemetry,
} from "@/api/droneGateway";
import { useAlerts, useLiveEvents } from "@/api/events";
import { demoSmartMapDevices, useSmartMapOverview, type SmartMapDevice } from "@/api/map";
import { useRecentSensors, type SensorReading } from "@/api/sensors";

type AssetKind = "drone" | "camera" | "sensor" | "deterrent" | "alert";
type DrawMode = "mission" | "geofence" | "alert-zone" | null;
type LogFilter = "all" | "alerts" | "commands" | "errors";

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
  category: "telemetry" | "alert" | "command" | "error";
  message: string;
  timestamp: string;
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
const cityBounds = {
  north: -25.742,
  south: -25.7525,
  west: 28.226,
  east: 28.2485,
};

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

function projectPoint(latitude: number, longitude: number) {
  const left = ((longitude - cityBounds.west) / (cityBounds.east - cityBounds.west)) * 100;
  const top = ((cityBounds.north - latitude) / (cityBounds.north - cityBounds.south)) * 100;

  return {
    left: `${Math.min(96, Math.max(4, left)).toFixed(2)}%`,
    top: `${Math.min(95, Math.max(5, top)).toFixed(2)}%`,
  };
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

export default function Dashboard() {
  const [clock, setClock] = useState(() => new Date());
  const [assetFilter, setAssetFilter] = useState("");
  const deferredAssetFilter = useDeferredValue(assetFilter);
  const [selectedAsset, setSelectedAsset] = useState<SelectedAsset | null>(null);
  const [drawMode, setDrawMode] = useState<DrawMode>("mission");
  const [drawPoints, setDrawPoints] = useState<MapPoint[]>([]);
  const [logFilter, setLogFilter] = useState<LogFilter>("all");
  const [localLogs, setLocalLogs] = useState<CommandLogEntry[]>([]);
  const [selectedMissionId, setSelectedMissionId] = useState("");
  const [selectedAlertId, setSelectedAlertId] = useState("");
  const [selectedCityCamera, setSelectedCityCamera] = useState("");

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
  const uploadMission = useUploadDroneMission();
  const smartMapQuery = useSmartMapOverview();

  useEffect(() => {
    const timerId = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timerId);
  }, []);

  const fleet =
    droneFleetQuery.data && (droneFleetQuery.data.drones.length > 0 || droneFleetQuery.data.registry.length > 0)
      ? droneFleetQuery.data
      : demoDroneFleet;
  const droneTelemetries = fleet.drones.length > 0 ? fleet.drones : demoDroneFleet.drones;
  const droneRegistry = fleet.registry.length > 0 ? fleet.registry : demoDroneFleet.registry;
  const missionItems = droneMissionsQuery.data && droneMissionsQuery.data.length > 0
    ? droneMissionsQuery.data
    : [demoDroneMission];
  const cameraDevices = cameraQuery.data && cameraQuery.data.length > 0 ? cameraQuery.data : demoCameraFleet;
  const cameraFeeds = cameraFeedsQuery.data && cameraFeedsQuery.data.length > 0 ? cameraFeedsQuery.data : [demoCameraFeed];
  const mapDevices = smartMapQuery.data && smartMapQuery.data.devices.length > 0 ? smartMapQuery.data.devices : demoSmartMapDevices;
  const threatAlerts = threatAlertsQuery.data && threatAlertsQuery.data.length > 0
    ? threatAlertsQuery.data
    : demoThreatAlerts;
  const eventAlerts = eventAlertsQuery.data ?? [];
  const liveEvents = liveEventsQuery.data ?? [];
  const overlayCounts = mappingOverlaysQuery.data ?? { drones: [], sensors: [], threats: [], geofences: [] };
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
    const feed = cameraFeeds.find((candidate) => candidate.camera_id === camera.device_id) ?? cameraFeeds[index] ?? cameraFeeds[0];

    return {
      id: camera.device_id,
      kind: "camera",
      label: camera.device_id,
      status: camera.stream_status,
      subtitle: feed ? `PTZ ${feed.gimbal.zoom_level}x · ${feed.ai_detections.length} detections` : camera.device_type,
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

  const assetCatalog = [...drones, ...cameras, ...sensorAssets, ...deterrentAssets];
  const filteredAssets = deferredAssetFilter.trim().length === 0
    ? assetCatalog
    : assetCatalog.filter((asset) =>
        `${asset.label} ${asset.subtitle} ${asset.kind}`.toLowerCase().includes(deferredAssetFilter.toLowerCase()),
      );

  useEffect(() => {
    if (!selectedAsset && filteredAssets.length > 0) {
      setSelectedAsset({ kind: filteredAssets[0].kind, id: filteredAssets[0].id });
    }
  }, [filteredAssets, selectedAsset]);

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
    if (!selectedCityCamera && cameras.length > 0) {
      setSelectedCityCamera(cameras[0].id);
    }
  }, [cameras, selectedCityCamera]);

  function appendLocalLog(category: CommandLogEntry["category"], message: string) {
    setLocalLogs((currentLogs) => [
      {
        id: `${category}-${Date.now()}`,
        category,
        message,
        timestamp: new Date().toISOString(),
      },
      ...currentLogs,
    ].slice(0, 16));
  }

  function selectAsset(kind: SelectedAsset["kind"], id: string) {
    startTransition(() => setSelectedAsset({ kind, id }));
  }

  function handleMapClick(event: MouseEvent<HTMLDivElement>) {
    if (!drawMode) {
      return;
    }

    const bounds = event.currentTarget.getBoundingClientRect();
    const xRatio = (event.clientX - bounds.left) / bounds.width;
    const yRatio = (event.clientY - bounds.top) / bounds.height;
    const nextPoint = {
      latitude: cityBounds.north - yRatio * (cityBounds.north - cityBounds.south),
      longitude: cityBounds.west + xRatio * (cityBounds.east - cityBounds.west),
    };

    setDrawPoints((currentPoints) => [...currentPoints, nextPoint].slice(-8));
  }

  const activeDroneTelemetry = selectedAsset?.kind === "drone"
    ? droneTelemetries.find((telemetry) => telemetry.drone_id === selectedAsset.id) ?? null
    : null;
  const activeDroneRegistry = selectedAsset?.kind === "drone"
    ? droneRegistry.find((registryEntry) => registryEntry.drone_id === selectedAsset.id) ?? null
    : null;
  const activeDroneMission = selectedAsset?.kind === "drone"
    ? missionItems.find((mission) => mission.drone_id === selectedAsset.id) ?? missionItems[0] ?? null
    : null;
  const activeCamera = selectedAsset?.kind === "camera"
    ? cameraDevices.find((camera) => camera.device_id === selectedAsset.id) ?? null
    : null;
  const activeCameraFeed = selectedAsset?.kind === "camera"
    ? cameraFeeds.find((feed) => feed.camera_id === selectedAsset.id || feed.camera_id === selectedCityCamera) ?? cameraFeeds[0] ?? null
    : null;
  const activeSensor = selectedAsset?.kind === "sensor"
    ? sensors.find((sensor) => sensor.id === selectedAsset.id) ?? null
    : null;
  const activeDeterrent = selectedAsset?.kind === "deterrent"
    ? demoDeterrents.find((device) => device.id === selectedAsset.id) ?? null
    : null;
  const activeThreatAlert = selectedAsset?.kind === "alert"
    ? threatAlerts.find((alert) => alert.alert_id === selectedAsset.id) ?? null
    : threatAlerts.find((alert) => alert.alert_id === selectedAlertId) ?? null;

  const linkedAlerts = threatAlerts.filter((alert) => {
    if (!selectedAsset || selectedAsset.kind === "alert") {
      return false;
    }
    return alert.source_ids.includes(selectedAsset.id);
  });

  const commandLogsFromEvents: CommandLogEntry[] = liveEvents.slice(0, 10).map((entry) => ({
    id: entry.event_id,
    category: entry.event_type.includes("command") ? "command" : entry.event_type.includes("alert") ? "alert" : "telemetry",
    message: `${entry.source} · ${entry.event_type}`,
    timestamp: entry.occurred_at,
  }));

  const alertLogs: CommandLogEntry[] = eventAlerts.slice(0, 8).map((entry) => ({
    id: entry.id,
    category: entry.severity.toLowerCase() === "critical" ? "error" : "alert",
    message: `${entry.title} · ${entry.message}`,
    timestamp: entry.created_at,
  }));

  const telemetryLogs: CommandLogEntry[] = droneTelemetries.slice(0, 4).map((telemetry: DroneTelemetry) => ({
    id: `${telemetry.drone_id}-${telemetry.timestamp}`,
    category: telemetry.health_flags.length > 0 ? "error" : "telemetry",
    message: `${telemetry.drone_id} · ${Math.round(telemetry.battery_percent)}% · ${telemetry.flight_mode} · ${telemetry.speed_mps.toFixed(1)} m/s`,
    timestamp: telemetry.timestamp,
  }));

  const combinedLogs = [...localLogs, ...alertLogs, ...commandLogsFromEvents, ...telemetryLogs]
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
    .slice(0, 18)
    .filter((entry) => {
      if (logFilter === "all") {
        return true;
      }
      if (logFilter === "alerts") {
        return entry.category === "alert";
      }
      if (logFilter === "commands") {
        return entry.category === "command";
      }
      return entry.category === "error";
    });

  const systemHealthCards = [
    { label: "Drone Gateway", value: gatewayReady.data ? "online" : "degraded" },
    { label: "Kafka", value: serviceHealth?.data_flow.some((stage) => stage.destination === "kafka" && stage.state === "healthy") ? "healthy" : "watch" },
    { label: "Database", value: serviceHealth?.security.audit_pipeline_status ?? "watch" },
    { label: "Mission Control", value: missionItems.length > 0 ? "ready" : "watch" },
    { label: "Services", value: `${serviceHealth?.controls.length ?? 0} active` },
  ];

  function dispatchDroneAction(action: DroneCommandAction) {
    if (!activeDroneRegistry) {
      return;
    }

    sendDroneCommand.mutate({
      drone_id: activeDroneRegistry.drone_id,
      action,
      requested_by: operatorName,
    });
    appendLocalLog("command", `${action} dispatched to ${activeDroneRegistry.drone_id}`);
  }

  function assignMission(mission: DroneMission) {
    if (!activeDroneRegistry) {
      return;
    }

    appendLocalLog("command", `Mission ${mission.name} assigned to ${activeDroneRegistry.drone_id}`);
  }

  function uploadQuickMission() {
    if (!activeDroneRegistry || drawPoints.length < 2) {
      appendLocalLog("error", "Quick mission requires a selected drone and at least two map points.");
      return;
    }

    uploadMission.mutate({
      drone_id: activeDroneRegistry.drone_id,
      name: `Quick mission ${new Date().toLocaleTimeString("en-ZA")}`,
      altitude_m: activeDroneTelemetry?.position.altitude_m ?? 90,
      speed_mps: activeDroneTelemetry?.speed_mps ?? 8,
      waypoints: drawPoints,
    });
    appendLocalLog("command", `Quick mission uploaded for ${activeDroneRegistry.drone_id}`);
    setDrawPoints([]);
  }

  const linkedCameraAssets = activeSensor
    ? cameras.filter((camera) => activeSensor.linkedCameraIds.includes(camera.id))
    : [];

  return (
    <section className="command-center" aria-label="City command center dashboard">
      <header className="command-topbar">
        <div className="command-topbar-block">
          <span className="command-kicker">City command center</span>
          <h2>{cityName}</h2>
          <p>One operator surface for drones, city cameras, sensors, deterrents, missions, and alerts.</p>
        </div>

        <div className="command-topbar-meta">
          <div>
            <span>System status</span>
            <strong>{gatewayReady.data ? "Nominal" : "Partial visibility"}</strong>
          </div>
          <div>
            <span>Operator</span>
            <strong>{operatorName}</strong>
          </div>
          <div>
            <span>Local time</span>
            <strong>{formatClock(clock)}</strong>
          </div>
          <button
            className="command-alert-pill"
            type="button"
            onClick={() => threatAlerts[0] && selectAsset("alert", threatAlerts[0].alert_id)}
          >
            {threatAlerts.length} global alerts
          </button>
        </div>
      </header>

      <div className="command-layout">
        <aside className="command-left-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">Assets</span>
              <h3>Fleet and field inventory</h3>
            </div>
            <span className="command-count">{assetCatalog.length}</span>
          </div>

          <label className="command-search">
            <span>Search assets</span>
            <input
              value={assetFilter}
              onChange={(event) => setAssetFilter(event.target.value)}
              placeholder="Drone, camera, sensor, deterrent"
            />
          </label>

          <div className="command-asset-groups">
            <section>
              <div className="command-subsection-header">
                <h4>Drones</h4>
                <span>{drones.length}</span>
              </div>
              <div className="command-asset-list">
                {filteredAssets.filter((asset) => asset.kind === "drone").map((asset) => (
                  <button
                    className={`command-asset-card ${selectedAsset?.id === asset.id ? "is-selected" : ""}`}
                    key={asset.id}
                    type="button"
                    onClick={() => selectAsset(asset.kind, asset.id)}
                  >
                    <div>
                      <strong>{asset.label}</strong>
                      <span>{asset.subtitle}</span>
                    </div>
                    <CommandStatusBadge label={asset.status} />
                  </button>
                ))}
              </div>
            </section>

            <section>
              <div className="command-subsection-header">
                <h4>Cameras</h4>
                <span>{cameras.length}</span>
              </div>
              <div className="command-asset-list compact">
                {filteredAssets.filter((asset) => asset.kind === "camera").map((asset) => (
                  <button
                    className={`command-asset-row ${selectedAsset?.id === asset.id ? "is-selected" : ""}`}
                    key={asset.id}
                    type="button"
                    onClick={() => {
                      setSelectedCityCamera(asset.id);
                      selectAsset(asset.kind, asset.id);
                    }}
                  >
                    <span>{asset.label}</span>
                    <CommandStatusBadge label={asset.status} />
                  </button>
                ))}
              </div>
            </section>

            <section>
              <div className="command-subsection-header">
                <h4>Sensors</h4>
                <span>{sensorAssets.length}</span>
              </div>
              <div className="command-asset-list compact">
                {filteredAssets.filter((asset) => asset.kind === "sensor").map((asset) => (
                  <button
                    className={`command-asset-row ${selectedAsset?.id === asset.id ? "is-selected" : ""}`}
                    key={asset.id}
                    type="button"
                    onClick={() => selectAsset(asset.kind, asset.id)}
                  >
                    <span>{asset.label}</span>
                    <CommandStatusBadge label={asset.status} />
                  </button>
                ))}
              </div>
            </section>

            <section>
              <div className="command-subsection-header">
                <h4>Deterrents</h4>
                <span>{deterrentAssets.length}</span>
              </div>
              <div className="command-asset-list compact">
                {filteredAssets.filter((asset) => asset.kind === "deterrent").map((asset) => (
                  <button
                    className={`command-asset-row ${selectedAsset?.id === asset.id ? "is-selected" : ""}`}
                    key={asset.id}
                    type="button"
                    onClick={() => selectAsset(asset.kind, asset.id)}
                  >
                    <span>{asset.label}</span>
                    <CommandStatusBadge label={asset.status} />
                  </button>
                ))}
              </div>
            </section>
          </div>

          <section className="command-alert-stack">
            <div className="command-subsection-header">
              <h4>Active alerts</h4>
              <span>{threatAlerts.length}</span>
            </div>
            <div className="command-alert-list">
              {threatAlerts.map((alert) => (
                <button
                  className={`command-alert-card ${selectedAsset?.id === alert.alert_id ? "is-selected" : ""}`}
                  key={alert.alert_id}
                  type="button"
                  onClick={() => {
                    setSelectedAlertId(alert.alert_id);
                    selectAsset("alert", alert.alert_id);
                  }}
                >
                  <div>
                    <strong>{alert.title}</strong>
                    <span>{alert.source_ids.join(", ")}</span>
                  </div>
                  <CommandStatusBadge label={alert.threat_level} />
                </button>
              ))}
            </div>
          </section>
        </aside>

        <main className="command-center-panel">
          <section className="command-map-panel">
            <div className="command-panel-header">
              <div>
                <span className="command-kicker">City map</span>
                <h3>Operational map and live layers</h3>
              </div>
              <div className="command-map-actions">
                <button type="button" onClick={() => setDrawMode("mission")} className={drawMode === "mission" ? "is-active" : ""}>Mission route</button>
                <button type="button" onClick={() => setDrawMode("geofence")} className={drawMode === "geofence" ? "is-active" : ""}>Geofence</button>
                <button type="button" onClick={() => setDrawMode("alert-zone")} className={drawMode === "alert-zone" ? "is-active" : ""}>Alert zone</button>
                <button type="button" onClick={() => setDrawPoints([])}>Clear</button>
              </div>
            </div>

            <div className="command-layer-row">
              <span>OpenStreetMap-ready city layer</span>
              <div>
                <CommandStatusBadge label={`${overlayCounts.geofences.length || zoneOverlays.length} zones`} />
                <CommandStatusBadge label={`${threatAlerts.length} alerts`} />
                <CommandStatusBadge label={`${cameraFeeds.length} live feeds`} />
              </div>
            </div>

            <div className="command-map-surface" onClick={handleMapClick} role="presentation">
              <div className="command-map-grid" />
              <div className="command-map-roads" />

              {zoneOverlays.map((zone) => (
                <div
                  className={`command-zone command-zone-${zone.kind}`}
                  key={zone.id}
                  style={{ top: `${zone.top}%`, left: `${zone.left}%`, width: `${zone.width}%`, height: `${zone.height}%` }}
                >
                  <span>{zone.label}</span>
                </div>
              ))}

              {activeThreatAlert ? (
                <div
                  className="command-heat command-heat-critical"
                  style={projectPoint(
                    assetCatalog.find((asset) => asset.id === activeThreatAlert.source_ids[0])?.latitude ?? -25.745,
                    assetCatalog.find((asset) => asset.id === activeThreatAlert.source_ids[0])?.longitude ?? 28.244,
                  )}
                />
              ) : null}

              {threatAlerts.slice(1, 3).map((alert) => {
                const linkedAsset = assetCatalog.find((asset) => asset.id === alert.source_ids[0]);
                return linkedAsset ? (
                  <div className="command-heat" key={alert.alert_id} style={projectPoint(linkedAsset.latitude, linkedAsset.longitude)} />
                ) : null;
              })}

              {cameras.map((camera) => {
                const position = projectPoint(camera.latitude, camera.longitude);
                return (
                  <div className="command-camera-cluster" key={camera.id} style={position}>
                    <button
                      className={`command-map-marker camera ${selectedAsset?.id === camera.id ? "is-selected" : ""}`}
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        setSelectedCityCamera(camera.id);
                        selectAsset("camera", camera.id);
                      }}
                    >
                      C
                    </button>
                    <div className="command-camera-fov" />
                  </div>
                );
              })}

              {drones.map((drone) => {
                const position = projectPoint(drone.latitude, drone.longitude);
                const heading = droneTelemetries.find((telemetry) => telemetry.drone_id === drone.id)?.heading_deg ?? 90;
                return (
                  <button
                    className={`command-map-marker drone ${selectedAsset?.id === drone.id ? "is-selected" : ""}`}
                    key={drone.id}
                    type="button"
                    style={{ ...position, transform: `translate(-50%, -50%) rotate(${heading}deg)` }}
                    onClick={(event) => {
                      event.stopPropagation();
                      selectAsset("drone", drone.id);
                    }}
                  >
                    ▲
                  </button>
                );
              })}

              {sensorAssets.map((sensor) => (
                <button
                  className={`command-map-marker sensor ${selectedAsset?.id === sensor.id ? "is-selected" : ""}`}
                  key={sensor.id}
                  type="button"
                  style={projectPoint(sensor.latitude, sensor.longitude)}
                  onClick={(event) => {
                    event.stopPropagation();
                    selectAsset("sensor", sensor.id);
                  }}
                >
                  S
                </button>
              ))}

              {deterrentAssets.map((device) => (
                <button
                  className={`command-map-marker deterrent ${selectedAsset?.id === device.id ? "is-selected" : ""}`}
                  key={device.id}
                  type="button"
                  style={projectPoint(device.latitude, device.longitude)}
                  onClick={(event) => {
                    event.stopPropagation();
                    selectAsset("deterrent", device.id);
                  }}
                >
                  D
                </button>
              ))}

              {drawPoints.length > 0 ? (
                <svg className="command-draw-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <polyline
                    fill="none"
                    points={drawPoints
                      .map((point) => {
                        const left = ((point.longitude - cityBounds.west) / (cityBounds.east - cityBounds.west)) * 100;
                        const top = ((cityBounds.north - point.latitude) / (cityBounds.north - cityBounds.south)) * 100;
                        return `${left},${top}`;
                      })
                      .join(" ")}
                    stroke="rgba(233, 192, 98, 0.92)"
                    strokeDasharray="3 2"
                    strokeWidth="0.5"
                  />
                </svg>
              ) : null}
            </div>

            <div className="command-map-footer">
              <div>
                <strong>Draw mode</strong>
                <span>{drawMode ?? "off"}</span>
              </div>
              <div>
                <strong>Selected points</strong>
                <span>{drawPoints.length}</span>
              </div>
              <div>
                <strong>Linked layers</strong>
                <span>{overlayCounts.threats.length || threatAlerts.length} threat overlays · {overlayCounts.sensors.length || sensorAssets.length} sensors</span>
              </div>
            </div>
          </section>
        </main>

        <aside className="command-right-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">Context</span>
              <h3>
                {selectedAsset?.kind === "drone" && "Drone view"}
                {selectedAsset?.kind === "camera" && "City camera view"}
                {selectedAsset?.kind === "sensor" && "Sensor and deterrent view"}
                {selectedAsset?.kind === "deterrent" && "Deterrent control view"}
                {selectedAsset?.kind === "alert" && "Threat intelligence view"}
                {!selectedAsset && "Select an asset"}
              </h3>
            </div>
            {selectedAsset ? <CommandStatusBadge label={selectedAsset.kind} /> : null}
          </div>

          {selectedAsset?.kind === "drone" && activeDroneRegistry ? (
            <div className="command-context-stack">
              <section className="command-context-card">
                <h4>{activeDroneRegistry.model}</h4>
                <div className="command-metrics-grid">
                  <div><span>Status</span><strong>{activeDroneTelemetry?.status ?? activeDroneRegistry.status}</strong></div>
                  <div><span>Battery</span><strong>{Math.round(activeDroneTelemetry?.battery_percent ?? 0)}%</strong></div>
                  <div><span>Position</span><strong>{(activeDroneTelemetry?.position.latitude ?? drones[0]?.latitude ?? 0).toFixed(4)}, {(activeDroneTelemetry?.position.longitude ?? drones[0]?.longitude ?? 0).toFixed(4)}</strong></div>
                  <div><span>Altitude</span><strong>{Math.round(activeDroneTelemetry?.position.altitude_m ?? activeDroneMission?.altitude_m ?? 0)} m</strong></div>
                  <div><span>Speed</span><strong>{(activeDroneTelemetry?.speed_mps ?? activeDroneMission?.speed_mps ?? 0).toFixed(1)} m/s</strong></div>
                  <div><span>Heading</span><strong>{Math.round(activeDroneTelemetry?.heading_deg ?? 0)}°</strong></div>
                </div>

                <div className="command-chip-row">
                  {activeDroneRegistry.camera_types.map((cameraType) => <span key={cameraType}>{cameraType}</span>)}
                  {activeDroneRegistry.sensors.map((sensor) => <span key={sensor}>{sensor}</span>)}
                  {activeDroneRegistry.payload_supported ? <span>payload enabled</span> : null}
                </div>

                <div className="command-mission-card">
                  <div>
                    <span>Mission</span>
                    <strong>{activeDroneMission?.name ?? "No mission assigned"}</strong>
                  </div>
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

              <section className="command-context-card">
                <h4>Flight controls</h4>
                <div className="command-control-grid">
                  <button type="button" onClick={() => dispatchDroneAction("takeoff")}>Takeoff</button>
                  <button type="button" onClick={() => dispatchDroneAction("land")}>Land</button>
                  <button type="button" onClick={() => dispatchDroneAction("return_to_base")}>Return to base</button>
                  <button type="button" onClick={() => dispatchDroneAction("hover")}>Hold position</button>
                </div>

                <div className="command-form-block">
                  <label>
                    <span>Assign mission</span>
                    <select value={selectedMissionId} onChange={(event) => setSelectedMissionId(event.target.value)}>
                      {missionItems.map((mission) => (
                        <option key={mission.mission_id} value={mission.mission_id}>{mission.name}</option>
                      ))}
                    </select>
                  </label>
                  <div className="command-inline-actions">
                    <button
                      type="button"
                      onClick={() => {
                        const mission = missionItems.find((candidate) => candidate.mission_id === selectedMissionId);
                        if (mission) {
                          assignMission(mission);
                        }
                      }}
                    >
                      Assign mission
                    </button>
                    <button type="button" onClick={uploadQuickMission}>Create quick mission</button>
                  </div>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Linked alerts</h4>
                <div className="command-list-block">
                  {linkedAlerts.length > 0 ? linkedAlerts.map((alert) => (
                    <button key={alert.alert_id} type="button" className="command-line-button" onClick={() => selectAsset("alert", alert.alert_id)}>
                      <span>{alert.title}</span>
                      <CommandStatusBadge label={alert.threat_level} />
                    </button>
                  )) : <p>No active alerts linked to this drone.</p>}
                </div>
              </section>
            </div>
          ) : null}

          {selectedAsset?.kind === "camera" && activeCamera ? (
            <div className="command-context-stack">
              <section className="command-context-card">
                <h4>{activeCamera.device_id}</h4>
                <div className="command-video-shell">
                  <div className="command-video-feed">
                    <span>Live surveillance feed</span>
                    <strong>{activeCameraFeed?.stream_url ?? "Awaiting stream"}</strong>
                  </div>
                </div>
                <div className="command-metrics-grid">
                  <div><span>Stream status</span><strong>{activeCamera.stream_status}</strong></div>
                  <div><span>Battery</span><strong>{activeCamera.battery_level ?? 100}%</strong></div>
                  <div><span>Pan</span><strong>{activeCameraFeed?.gimbal.yaw_deg ?? 0}°</strong></div>
                  <div><span>Tilt</span><strong>{activeCameraFeed?.gimbal.pitch_deg ?? 0}°</strong></div>
                  <div><span>Zoom</span><strong>{activeCameraFeed?.gimbal.zoom_level ?? 1}x</strong></div>
                  <div><span>Detections</span><strong>{activeCameraFeed?.ai_detections.length ?? 0}</strong></div>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Camera controls</h4>
                <div className="command-control-grid">
                  <button type="button" onClick={() => appendLocalLog("command", `Pan left on ${activeCamera.device_id}`)}>Pan left</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Tilt up on ${activeCamera.device_id}`)}>Tilt up</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Zoom in on ${activeCamera.device_id}`)}>Zoom in</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Snapshot captured from ${activeCamera.device_id}`)}>Snapshot</button>
                  <button type="button" onClick={() => appendLocalLog("alert", `Operator tagged suspicious activity on ${activeCamera.device_id}`)}>Tag event</button>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Linked sensors and alerts</h4>
                <div className="command-list-block">
                  {sensors.filter((sensor) => sensor.linkedCameraIds.includes(activeCamera.device_id)).map((sensor) => (
                    <button key={sensor.id} type="button" className="command-line-button" onClick={() => selectAsset("sensor", sensor.id)}>
                      <span>{sensor.name}</span>
                      <CommandStatusBadge label={sensor.status} />
                    </button>
                  ))}
                </div>
                <div className="command-list-block">
                  {threatAlerts.filter((alert) => alert.source_ids.includes(activeCamera.device_id)).map((alert) => (
                    <button key={alert.alert_id} type="button" className="command-line-button" onClick={() => selectAsset("alert", alert.alert_id)}>
                      <span>{alert.title}</span>
                      <CommandStatusBadge label={alert.threat_level} />
                    </button>
                  ))}
                </div>
              </section>
            </div>
          ) : null}

          {selectedAsset?.kind === "sensor" && activeSensor ? (
            <div className="command-context-stack">
              <section className="command-context-card">
                <h4>{activeSensor.name}</h4>
                <div className="command-metrics-grid">
                  <div><span>Status</span><strong>{activeSensor.status}</strong></div>
                  <div><span>Current reading</span><strong>{activeSensor.currentValue} {activeSensor.unit}</strong></div>
                  <div><span>Threshold</span><strong>{activeSensor.category === "magnetic/em" ? "8.0 mT" : "operator-defined"}</strong></div>
                  <div><span>Last triggered</span><strong>{formatTime(activeSensor.lastTriggeredAt)}</strong></div>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Linked assets</h4>
                <div className="command-list-block">
                  {linkedCameraAssets.map((camera) => (
                    <button key={camera.id} type="button" className="command-line-button" onClick={() => selectAsset("camera", camera.id)}>
                      <span>{camera.label}</span>
                      <CommandStatusBadge label={camera.status} />
                    </button>
                  ))}
                  {drones.filter((drone) => activeSensor.linkedDroneIds.includes(drone.id)).map((drone) => (
                    <button key={drone.id} type="button" className="command-line-button" onClick={() => selectAsset("drone", drone.id)}>
                      <span>{drone.label}</span>
                      <CommandStatusBadge label={drone.status} />
                    </button>
                  ))}
                </div>
              </section>

              <section className="command-context-card">
                <h4>Recent history</h4>
                <div className="command-history-list">
                  {activeSensor.history.length > 0 ? activeSensor.history.map((entry) => (
                    <div key={`${entry.sensor_id}-${entry.observed_at}`} className="command-history-row">
                      <span>{formatTime(entry.observed_at)}</span>
                      <strong>{entry.value} {entry.unit}</strong>
                    </div>
                  )) : <p>No recent history returned by Sensor Gateway.</p>}
                </div>
              </section>
            </div>
          ) : null}

          {selectedAsset?.kind === "deterrent" && activeDeterrent ? (
            <div className="command-context-stack">
              <section className="command-context-card">
                <h4>{activeDeterrent.name}</h4>
                <div className="command-metrics-grid">
                  <div><span>Status</span><strong>{activeDeterrent.status}</strong></div>
                  <div><span>Zone</span><strong>{activeDeterrent.zone}</strong></div>
                  <div><span>Roles</span><strong>{activeDeterrent.authorizedRoles.join(", ")}</strong></div>
                  <div><span>Rule</span><strong>{activeDeterrent.rule}</strong></div>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Controls</h4>
                <div className="command-control-grid">
                  <button type="button" onClick={() => appendLocalLog("command", `${activeDeterrent.name} activated`)}>Activate</button>
                  <button type="button" onClick={() => appendLocalLog("command", `${activeDeterrent.name} deactivated`)}>Deactivate</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Automation rule updated for ${activeDeterrent.name}`)}>Set automatic rule</button>
                </div>
              </section>
            </div>
          ) : null}

          {selectedAsset?.kind === "alert" && activeThreatAlert ? (
            <div className="command-context-stack">
              <section className="command-context-card">
                <h4>{activeThreatAlert.title}</h4>
                <div className="command-metrics-grid">
                  <div><span>Severity</span><strong>{activeThreatAlert.threat_level}</strong></div>
                  <div><span>Confidence</span><strong>{Math.round(activeThreatAlert.confidence * 100)}%</strong></div>
                  <div><span>Linked assets</span><strong>{activeThreatAlert.source_ids.join(", ")}</strong></div>
                  <div><span>Map response</span><strong>Zoom to threat cluster</strong></div>
                </div>
              </section>

              <section className="command-context-card">
                <h4>Suggested actions</h4>
                <div className="command-list-block">
                  {activeThreatAlert.recommended_actions.map((action) => (
                    <button key={action} type="button" className="command-line-button" onClick={() => appendLocalLog("command", `${action} triggered from ${activeThreatAlert.alert_id}`)}>
                      <span>{action.replaceAll("-", " ")}</span>
                      <CommandStatusBadge label={activeThreatAlert.threat_level} />
                    </button>
                  ))}
                </div>
              </section>

              <section className="command-context-card">
                <h4>Alert response controls</h4>
                <div className="command-control-grid">
                  <button type="button" onClick={() => appendLocalLog("command", `Alert ${activeThreatAlert.alert_id} acknowledged`)}>Acknowledge</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Alert ${activeThreatAlert.alert_id} assigned to ${operatorName}`)}>Assign to operator</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Nearest drone dispatched for ${activeThreatAlert.alert_id}`)}>Dispatch nearest drone</button>
                  <button type="button" onClick={() => appendLocalLog("command", `Linked deterrent activated for ${activeThreatAlert.alert_id}`)}>Activate deterrent</button>
                </div>
              </section>
            </div>
          ) : null}
        </aside>
      </div>

      <footer className="command-bottom-bar">
        <section className="command-system-health">
          <div className="command-panel-header compact">
            <div>
              <span className="command-kicker">Bottom bar</span>
              <h3>Live telemetry and logs</h3>
            </div>
          </div>

          <div className="command-health-grid">
            {systemHealthCards.map((card) => (
              <article key={card.label} className="command-health-card">
                <span>{card.label}</span>
                <strong>{card.value}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="command-live-log">
          <div className="command-log-header">
            <div>
              <span className="command-kicker">Event stream</span>
              <h3>Telemetry, alerts, and commands</h3>
            </div>
            <div className="command-log-filters">
              {(["all", "alerts", "commands", "errors"] as const).map((filterOption) => (
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
          </div>

          <div className="command-log-list">
            {combinedLogs.map((entry) => (
              <div className={`command-log-entry ${entry.category}`} key={entry.id}>
                <span>{formatTime(entry.timestamp)}</span>
                <strong>{entry.category}</strong>
                <p>{entry.message}</p>
              </div>
            ))}
          </div>
        </section>
      </footer>
    </section>
  );
}
