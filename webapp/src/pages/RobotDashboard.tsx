import { useMemo, useState } from "react";

import CommandCenterMap from "@/components/CommandCenterMap";
import OperationsSwitcher from "@/components/OperationsSwitcher";
import { demoSmartMapDevices, useSmartMapOverview } from "@/api/map";
import { demoRobotFleet, useRobotFleet, useRobotGatewayReady, useSendRobotCommand } from "@/api/robotGateway";
import { useRecentSensors } from "@/api/sensors";

type RobotSensorStatus = "nominal" | "watch" | "offline";

interface RobotSensor {
  id: string;
  label: string;
  value: string;
  status: RobotSensorStatus;
}

const robotZones = [
  { id: "robot-zone-1", label: "Tunnel patrol zone", kind: "restricted" as const, top: 42, left: 28, width: 19, height: 18 },
  { id: "robot-zone-2", label: "Depot patrol lane", kind: "geofence" as const, top: 56, left: 54, width: 22, height: 14 },
];

function sensorTone(status: RobotSensorStatus) {
  if (status === "offline") {
    return "critical";
  }
  if (status === "watch") {
    return "warning";
  }
  return "healthy";
}

export default function RobotDashboard() {
  const [selectedRobotId, setSelectedRobotId] = useState(demoRobotFleet.registry[0].robot_id);
  const readyQuery = useRobotGatewayReady();
  const fleetQuery = useRobotFleet();
  const sendRobotCommand = useSendRobotCommand();
  const mapQuery = useSmartMapOverview();
  const sensorQuery = useRecentSensors(8);

  const fleet = fleetQuery.data && fleetQuery.data.registry.length > 0 ? fleetQuery.data : demoRobotFleet;
  const registry = fleet.registry;
  const telemetry = fleet.robots;
  const routes = fleet.routes;
  const selectedTelemetry = telemetry.find((robot) => robot.robot_id === selectedRobotId) ?? telemetry[0];
  const selectedRegistry = registry.find((robot) => robot.robot_id === selectedRobotId) ?? registry[0];
  const selectedRoutes = routes.filter((route) => route.robot_id === (selectedTelemetry?.robot_id ?? selectedRegistry?.robot_id));
  const mapDevices = mapQuery.data?.devices?.length ? mapQuery.data.devices : demoSmartMapDevices;
  const liveReadings = sensorQuery.data ?? [];

  const selectedRobot = {
    id: selectedTelemetry?.robot_id ?? selectedRegistry?.robot_id ?? demoRobotFleet.registry[0].robot_id,
    name: selectedRegistry?.model ?? "Robot unit",
    role: selectedTelemetry?.autonomy_state?.replaceAll("_", " ") ?? "robot operator",
    batteryPercent: Math.round(selectedTelemetry?.battery_percent ?? 0),
    speedMps: selectedTelemetry?.speed_mps ?? 0,
    headingDeg: selectedTelemetry?.heading_deg ?? 0,
    autonomyState: selectedTelemetry?.autonomy_state ?? "manual",
    status: selectedRegistry?.status === "degraded" ? "degraded" : selectedRegistry?.status === "offline" ? "offline" : "nominal",
    latitude: selectedTelemetry?.position.latitude ?? -25.7462,
    longitude: selectedTelemetry?.position.longitude ?? 28.2372,
    cameraFeed: selectedRegistry?.camera_ids[0] ? `rtsp://${selectedTelemetry?.robot_id ?? selectedRegistry.robot_id}/${selectedRegistry.camera_ids[0]}` : "Awaiting camera registration",
    lidarCoverage: selectedRegistry?.lidar_supported ? `${Math.max(18, Math.round((selectedRegistry.max_speed_mps ?? 2) * 9))} m active sweep` : "LIDAR unavailable",
    patrolRoute: selectedRoutes.flatMap((route) => route.checkpoints),
    sensors: (selectedRegistry?.sensors ?? []).map((sensorName) => ({
      id: sensorName,
      label: sensorName.replaceAll("-", " "),
      value: selectedTelemetry?.health_flags.includes(sensorName) ? "attention" : sensorName === "lidar" ? selectedTelemetry?.slam_state ?? "mapping" : "online",
      status: selectedTelemetry?.health_flags.includes(sensorName) ? "watch" : "nominal",
    })) as RobotSensor[],
  };

  function sendAction(action: "move_forward" | "move_reverse" | "turn_left" | "turn_right" | "hold" | "dock" | "set_waypoint" | "follow_route") {
    sendRobotCommand.mutate({
      robot_id: selectedRobot.id,
      action,
      path: action === "follow_route" ? selectedRoutes[0]?.path : undefined,
      target: action === "set_waypoint" ? { latitude: selectedRobot.latitude + 0.0004, longitude: selectedRobot.longitude + 0.0004, altitude_m: 0 } : undefined,
      requested_by: "robot-dashboard",
    });
  }

  const mapAssets = useMemo(
    () => [
      ...registry.map((robot) => {
        const activeTelemetry = telemetry.find((candidate) => candidate.robot_id === robot.robot_id);
        return {
          id: robot.robot_id,
        kind: "robot" as const,
          label: robot.model,
          status: robot.status,
          subtitle: `${activeTelemetry?.autonomy_state ?? "manual"} · ${Math.round(activeTelemetry?.battery_percent ?? 0)}% battery`,
          latitude: activeTelemetry?.position.latitude ?? -25.7462,
          longitude: activeTelemetry?.position.longitude ?? 28.2372,
        };
      }),
      ...mapDevices.slice(0, 4).map((device) => ({
        id: device.device_id,
        kind: device.device_type === "camera" ? "camera" as const : "sensor" as const,
        label: device.name,
        status: device.trust_level,
        subtitle: `${device.device_type} · ${device.sensor_type}`,
        latitude: device.latitude,
        longitude: device.longitude,
      })),
    ],
    [mapDevices, registry, telemetry],
  );

  const threatAlerts = liveReadings.slice(0, 2).map((reading, index) => ({
    alert_id: `robot-reading-${index}`,
    title: `${reading.sensor_id} activity`,
    threat_level: reading.value > 1 ? "critical" : "warning",
    source_ids: [selectedRobot.id],
  }));

  return (
    <section className="command-center operations-page robot-dashboard" aria-label="Robot operations dashboard">
      <header className="command-topbar operations-topbar">
        <div className="command-topbar-block">
          <span className="command-kicker">Robot dashboard</span>
          <h2>Ground Robotics Control</h2>
          <p>Separate operator view for UGV patrol, tunnel robotics, navigation control, and SLAM-assisted situational awareness.</p>
        </div>

        <div className="command-topbar-meta">
          <div>
            <span>Selected robot</span>
            <strong>{selectedRobot.name}</strong>
          </div>
          <div>
            <span>Autonomy</span>
            <strong>{selectedRobot.autonomyState}</strong>
          </div>
          <div>
            <span>Battery</span>
            <strong>{selectedRobot.batteryPercent}%</strong>
          </div>
          <div>
            <span>Gateway</span>
            <strong>{readyQuery.data?.registry ?? "demo"}</strong>
          </div>
        </div>
      </header>

      <OperationsSwitcher />

      <div className="robot-dashboard-layout">
        <section className="command-panel-shell robot-primary-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">Robot camera feed</span>
              <h3>Forward vision</h3>
            </div>
            <label className="command-form-block robot-selector">
              <span>Robot unit</span>
              <select value={selectedRobot.id} onChange={(event) => setSelectedRobotId(event.target.value)}>
                {registry.map((robot) => (
                  <option key={robot.robot_id} value={robot.robot_id}>{robot.model}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="robot-camera-stage">
            <span>Live robot stream</span>
            <strong>{selectedRobot.cameraFeed}</strong>
          </div>

          <div className="robot-control-grid">
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("move_forward")}>Forward</button>
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("hold")}>Hold</button>
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("move_reverse")}>Reverse</button>
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("turn_left")}>Turn left</button>
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("set_waypoint")}>Waypoint</button>
            <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("turn_right")}>Turn right</button>
          </div>
        </section>

        <aside className="command-panel-shell robot-telemetry-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">Robot telemetry</span>
              <h3>Mobility state</h3>
            </div>
          </div>

          <div className="command-metrics-grid">
            <div><span>Speed</span><strong>{selectedRobot.speedMps.toFixed(1)} m/s</strong></div>
            <div><span>Heading</span><strong>{selectedRobot.headingDeg}°</strong></div>
            <div><span>Battery</span><strong>{selectedRobot.batteryPercent}%</strong></div>
            <div><span>Role</span><strong>{selectedRobot.role}</strong></div>
            <div><span>LIDAR</span><strong>{selectedRobot.lidarCoverage}</strong></div>
            <div><span>Status</span><strong>{selectedRobot.status}</strong></div>
          </div>

          <section className="command-context-card">
            <h4>Patrol routes</h4>
            <div className="command-history-list">
              {(selectedRobot.patrolRoute.length > 0 ? selectedRobot.patrolRoute : ["No route assigned"]).map((checkpoint, index) => (
                <div key={checkpoint} className="command-history-row">
                  <span>Route {index + 1}</span>
                  <strong>{checkpoint}</strong>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>

      <div className="robot-dashboard-layout secondary">
        <section className="command-panel-shell robot-map-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">LIDAR / SLAM map</span>
              <h3>Ground navigation map</h3>
            </div>
          </div>

          <div className="robot-slam-stage">
            <div className="robot-slam-grid" aria-hidden="true" />
            <div className="robot-slam-overlay">
              <span>SLAM confidence</span>
              <strong>{selectedTelemetry?.slam_state === "locked" ? "96%" : "82%"}</strong>
              <p>{selectedRobot.lidarCoverage} with active obstacle replay for corridor navigation.</p>
            </div>
          </div>

          <div className="command-map-shell robot-map-shell">
            <CommandCenterMap
              assets={mapAssets}
              threatAlerts={threatAlerts}
              zones={robotZones}
              selectedAssetId={selectedRobot.id}
              drawPoints={[]}
              onMapClick={() => undefined}
              onSelectAsset={(kind, id) => {
                if (kind === "robot") {
                  setSelectedRobotId(id);
                }
              }}
            />
          </div>
        </section>

        <aside className="command-panel-shell robot-sensor-panel">
          <div className="command-panel-header">
            <div>
              <span className="command-kicker">Robot sensors</span>
              <h3>Health and obstacle channels</h3>
            </div>
          </div>

          <div className="robot-sensor-list">
            {selectedRobot.sensors.map((sensor) => (
              <article key={sensor.id} className="robot-sensor-card">
                <div>
                  <strong>{sensor.label}</strong>
                  <span>{sensor.value}</span>
                </div>
                <span className={`command-badge ${sensorTone(sensor.status)}`}>{sensor.status}</span>
              </article>
            ))}
          </div>

          <section className="command-context-card">
            <h4>Navigation controls</h4>
            <div className="command-action-stack robot-action-stack">
              <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("follow_route")}>Resume patrol</button>
              <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("dock")}>Dock robot</button>
              <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("set_waypoint")}>Set waypoint</button>
              <button type="button" disabled={sendRobotCommand.isPending} onClick={() => sendAction("hold")}>Send inspection mission</button>
            </div>
          </section>
        </aside>
      </div>
    </section>
  );
}