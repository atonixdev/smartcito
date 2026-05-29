/**
 * ============================================================================
 * File: webapp/src/components/DroneOperationsPanel.tsx
 * Purpose:
 *   Drone operations dashboard sections: status, capabilities, map context,
 *   mission planner, camera feed, and threat detection.
 * ============================================================================
 */

import { useEffect, useMemo, useState } from "react";

import CommandCenterMap from "@/components/CommandCenterMap";
import {
  type DroneCapabilities,
  type DroneTelemetry,
  type MissionWaypoint,
  useCameraFeeds,
  useCityMapPayload,
  useConnectDrone,
  useDroneFleet,
  useDroneGatewayMetrics,
  useDroneGatewayReady,
  useDroneMissions,
  useMappingGeofences,
  useMappingOverlays,
  useSendDroneCommand,
  useThreatAlerts,
  useUploadDroneMission,
} from "@/api/droneGateway";

function statusClass(status?: string) {
  if (!status) {
    return "connecting";
  }
  if (["online", "running", "synced", "ready", "configured", "routed", "in_mission", "uploaded"].some((value) => status.includes(value))) {
    return "live";
  }
  if (["maintenance", "draft", "paused"].some((value) => status.includes(value))) {
    return "connecting";
  }
  return "degraded";
}

function telemetryFor(capability: DroneCapabilities | undefined, telemetry: DroneTelemetry[]) {
  if (!capability) {
    return telemetry[0];
  }
  return telemetry.find((item) => item.drone_id === capability.drone_id) ?? telemetry[0];
}

function metricValue(metrics: string | undefined, event: string) {
  const line = metrics?.split("\n").find((entry) => entry.includes(`event="${event}"`));
  return line?.split(" ").at(-1) ?? "0";
}

const serviceRegistry = [
  ["Gateway", "drone-gateway"],
  ["Mission", "mission-control"],
  ["Mapping", "mapping-geospatial"],
  ["Camera", "drone-camera"],
  ["Threat", "threat-detection"],
];

export default function DroneOperationsPanel() {
  const ready = useDroneGatewayReady();
  const fleetQuery = useDroneFleet();
  const metrics = useDroneGatewayMetrics();
  const missionsQuery = useDroneMissions();
  const mappingQuery = useMappingOverlays();
  const mappingGeofencesQuery = useMappingGeofences();
  const cityMapPayloadQuery = useCityMapPayload();
  const cameraQuery = useCameraFeeds();
  const threatQuery = useThreatAlerts();
  const connectDrone = useConnectDrone();
  const sendCommand = useSendDroneCommand();
  const uploadMission = useUploadDroneMission();
  const [waypoints, setWaypoints] = useState<MissionWaypoint[]>([]);

  const fleet = fleetQuery.data;
  const registry = fleet?.registry ?? [];
  const telemetry = fleet?.drones ?? [];
  const selectedCapability = registry[0];
  const selectedTelemetry = telemetryFor(selectedCapability, telemetry);
  const selectedDroneId = selectedCapability?.drone_id ?? selectedTelemetry?.drone_id ?? "drone-patrol-001";
  const activeMission = missionsQuery.data?.[0];
  const cameraFeed = cameraQuery.data?.[0];
  const alerts = threatQuery.data ?? [];
  const overlays = mappingQuery.data;
  const liveGeofences = mappingGeofencesQuery.data;
  const cityMapPayload = cityMapPayloadQuery.data ?? null;
  const registryStatus = ready.data?.registry ?? (ready.isError ? "offline" : "connecting");
  const commandPending = sendCommand.isPending || connectDrone.isPending || uploadMission.isPending;
  const primaryAlert = alerts[0];
  const heading = selectedTelemetry?.heading_deg ?? 0;
  const missionProgress = Math.max(0, Math.min(100, activeMission?.progress_percent ?? 0));

  const serviceHeartbeat = useMemo(
    () =>
      serviceRegistry.map(([label, fallback]) => ({
        label,
        value:
          label === "Gateway"
            ? ready.data?.service ?? fallback
            : label === "Threat"
              ? `${alerts.length} active`
              : fallback,
        status: label === "Gateway" ? statusClass(registryStatus) : "live",
      })),
    [alerts.length, ready.data?.service, registryStatus],
  );

  const mapAssets = useMemo(
    () => telemetry.map((item) => ({
      id: item.drone_id,
      kind: "drone" as const,
      label: item.drone_id,
      status: item.status,
      subtitle: `${item.flight_mode} · ${Math.round(item.battery_percent)}% battery`,
      latitude: item.position.latitude,
      longitude: item.position.longitude,
    })),
    [telemetry],
  );

  const mapGeoJsonLayers = [
    { id: "geofences", data: liveGeofences?.geojson ?? null, color: "#57c7d4" },
    { id: "sensors", data: cityMapPayload?.geojson_layers?.sensors ?? null, color: "#f1c96b" },
    { id: "cameras", data: cityMapPayload?.geojson_layers?.cameras ?? null, color: "#ffd776" },
    { id: "drone-paths", data: cityMapPayload?.geojson_layers?.drone_paths ?? null, color: "#8fb6ff" },
    { id: "mission-routes", data: cityMapPayload?.geojson_layers?.mission_routes ?? null, color: "#8fe5db" },
  ];

  const waypointSummary = useMemo(
    () =>
      waypoints.length > 0
        ? waypoints.map((point, index) => `${index + 1}: ${point.latitude.toFixed(4)}, ${point.longitude.toFixed(4)}`).join(" | ")
        : "No route loaded",
    [waypoints],
  );

  useEffect(() => {
    if (waypoints.length === 0 && activeMission?.waypoints?.length) {
      setWaypoints(activeMission.waypoints);
    }
  }, [activeMission?.waypoints, waypoints.length]);

  function addWaypoint() {
    const last =
      waypoints.at(-1) ??
      activeMission?.waypoints?.[0] ?? {
        latitude: selectedTelemetry?.position.latitude ?? 0,
        longitude: selectedTelemetry?.position.longitude ?? 0,
        altitude_m: selectedTelemetry?.position.altitude_m ?? 95,
        hold_seconds: 10,
      };
    setWaypoints((current) => [
      ...current,
      {
        latitude: last.latitude + 0.0005,
        longitude: last.longitude + 0.0007,
        altitude_m: activeMission?.altitude_m ?? selectedTelemetry?.position.altitude_m ?? 95,
        hold_seconds: 10,
      },
    ]);
  }

  function uploadPatrolMission() {
    uploadMission.mutate({
      drone_id: selectedDroneId,
      name: "Dashboard patrol route",
      altitude_m: activeMission?.altitude_m ?? selectedTelemetry?.position.altitude_m ?? 95,
      speed_mps: activeMission?.speed_mps ?? 8,
      waypoints,
    });
  }

  function liftDown() {
    const currentAltitude = selectedTelemetry?.position.altitude_m ?? activeMission?.altitude_m ?? 95;
    const nextAltitude = Math.max(20, Math.round(currentAltitude - 10));
    sendCommand.mutate({
      drone_id: selectedDroneId,
      action: "change_altitude",
      altitude_m: nextAltitude,
      requested_by: "dashboard",
    });
  }

  function dragRoute() {
    setWaypoints((current) =>
      current.map((point, index) => ({
        ...point,
        latitude: point.latitude + (index % 2 === 0 ? 0.00015 : -0.0001),
        longitude: point.longitude + 0.00035,
      })),
    );
  }

  return (
    <article className="panel panel-wide drone-operations-panel">
      <header className="panel-header drone-gateway-header">
        <div>
          <h3>Drone Operations</h3>
          <p className="muted">Real-time flight simulation surface with mission control, map overlays, and threat response.</p>
        </div>
        <span className={`status-pill ${statusClass(registryStatus)}`}>{registryStatus}</span>
      </header>

      <div className="drone-service-strip" aria-label="Drone service chain">
        {serviceHeartbeat.map((service) => (
          <div key={service.label}>
            <span>{service.label}</span>
            <strong>{service.value}</strong>
            <em className={`drone-heartbeat ${service.status}`}>{service.status}</em>
          </div>
        ))}
      </div>

      <section className="drone-sim-hud" aria-label="Drone simulation heads-up display">
        <article className="drone-sim-stage">
          <div className="drone-gateway-card-header">
            <h4>Flight HUD</h4>
            <span className={`status-pill ${statusClass(selectedTelemetry?.status)}`}>{selectedTelemetry?.status ?? "syncing"}</span>
          </div>
          <div className="drone-hud-stage">
            <div className="drone-hud-grid" />
            <div className="drone-hud-horizon" style={{ transform: `rotate(${heading - 90}deg)` }} />
            <div className="drone-hud-core">
              <span>{selectedDroneId}</span>
              <strong>{Math.round(selectedTelemetry?.speed_mps ?? 0)} m/s</strong>
            </div>
          </div>
          <div className="drone-progress-meta">
            <span>Mission progress</span>
            <strong>{missionProgress}%</strong>
          </div>
          <div className="drone-progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={missionProgress}>
            <span style={{ width: `${missionProgress}%` }} />
          </div>
        </article>

        <article className="drone-gateway-card drone-radar-panel">
          <div className="drone-gateway-card-header">
            <h4>Threat Radar</h4>
            <span className={`status-pill ${statusClass(primaryAlert?.threat_level)}`}>{primaryAlert?.threat_level ?? "clear"}</span>
          </div>
          <div className="drone-radar-list">
            {alerts.map((alert) => (
              <div key={alert.alert_id} className="drone-radar-row">
                <strong>{alert.title}</strong>
                <span>{Math.round(alert.confidence * 100)}% confidence</span>
                <div className="drone-radar-track">
                  <span style={{ width: `${Math.round(alert.confidence * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="drone-chip-row">
            {(primaryAlert?.recommended_actions ?? []).map((action) => (
              <span key={action} className="drone-chip muted-chip">{action}</span>
            ))}
          </div>
        </article>
      </section>

      <div className="drone-operations-grid">
        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Drone Status Panel</h4>
            <span className={`status-pill ${statusClass(selectedTelemetry?.status)}`}>{selectedTelemetry?.status ?? "unknown"}</span>
          </div>
          <dl className="drone-facts compact">
            <div><dt>Battery</dt><dd>{selectedTelemetry?.battery_percent ?? "--"}%</dd></div>
            <div><dt>GPS</dt><dd>{selectedTelemetry ? `${selectedTelemetry.position.latitude.toFixed(4)}, ${selectedTelemetry.position.longitude.toFixed(4)}` : "--"}</dd></div>
            <div><dt>Speed</dt><dd>{selectedTelemetry?.speed_mps ?? "--"} m/s</dd></div>
            <div><dt>Altitude</dt><dd>{selectedTelemetry?.position.altitude_m ?? "--"} m</dd></div>
            <div><dt>Heading</dt><dd>{selectedTelemetry?.heading_deg ?? "--"} deg</dd></div>
            <div><dt>Flight mode</dt><dd>{selectedTelemetry?.flight_mode ?? "--"}</dd></div>
            <div><dt>Link quality</dt><dd>{selectedTelemetry?.link_quality ? `${Math.round(selectedTelemetry.link_quality * 100)}%` : "--"}</dd></div>
            <div><dt>Telemetry rate</dt><dd>{metricValue(metrics.data, "telemetry_received")}</dd></div>
          </dl>
        </section>

        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Drone Capability Panel</h4>
            <span className={`status-pill ${statusClass(selectedCapability?.status)}`}>{selectedCapability?.status ?? "registry"}</span>
          </div>
          <dl className="drone-facts compact">
            <div><dt>Max speed</dt><dd>{selectedCapability?.max_speed_mps ?? "--"} m/s</dd></div>
            <div><dt>Max altitude</dt><dd>{selectedCapability?.max_altitude_m ?? "--"} m</dd></div>
            <div><dt>Payload</dt><dd>{selectedCapability?.payload_supported ? "supported" : "not listed"}</dd></div>
            <div><dt>Firmware</dt><dd>{selectedCapability?.firmware_version ?? "--"}</dd></div>
            <div><dt>Battery capacity</dt><dd>{selectedCapability?.battery_capacity_mah ?? "--"} mAh</dd></div>
            <div><dt>Protocol</dt><dd>{selectedCapability?.protocol ?? ready.data?.protocols[0] ?? "simulated"}</dd></div>
          </dl>
          <div className="drone-chip-row">
            {(selectedCapability?.camera_types ?? []).map((camera) => <span key={camera} className="drone-chip">{camera}</span>)}
            {(selectedCapability?.sensors ?? []).map((sensor) => <span key={sensor} className="drone-chip muted-chip">{sensor}</span>)}
          </div>
        </section>

        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Live Map View</h4>
            <span className="muted">map overlays</span>
          </div>
          <dl className="drone-facts compact">
            <div><dt>Drone position</dt><dd>{selectedDroneId}</dd></div>
            <div><dt>Drone path</dt><dd>{waypoints.length} points</dd></div>
            <div><dt>Geofences</dt><dd>{overlays?.geofences.length ?? 3}</dd></div>
            <div><dt>Patrol routes</dt><dd>{activeMission?.status ?? "--"}</dd></div>
            <div><dt>Sensors</dt><dd>{overlays?.sensors.length ?? 1}</dd></div>
            <div><dt>Threat overlays</dt><dd>{overlays?.threats.length ?? alerts.length}</dd></div>
          </dl>
          <p className="muted drone-command-status">{waypointSummary}</p>
          <div className="command-map-shell">
            <CommandCenterMap
              assets={mapAssets}
              threatAlerts={alerts}
              zones={[]}
              selectedAssetId={selectedDroneId}
              drawPoints={[]}
              onMapClick={() => undefined}
              onSelectAsset={() => undefined}
              geoJsonLayers={mapGeoJsonLayers}
            />
          </div>
        </section>

        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Mission Planner</h4>
            <span className={`status-pill ${statusClass(activeMission?.status)}`}>{activeMission?.progress_percent ?? 0}%</span>
          </div>
          <dl className="drone-facts compact">
            <div><dt>Mission</dt><dd>{activeMission?.name ?? "--"}</dd></div>
            <div><dt>Altitude</dt><dd>{activeMission?.altitude_m ?? "--"} m</dd></div>
            <div><dt>Speed</dt><dd>{activeMission?.speed_mps ?? "--"} m/s</dd></div>
            <div><dt>Waypoints</dt><dd>{waypoints.length}</dd></div>
          </dl>
          <div className="drone-command-row">
            <button className="control-button" type="button" disabled={commandPending} onClick={addWaypoint}>Add waypoint</button>
            <button className="control-button" type="button" disabled={commandPending} onClick={dragRoute}>Drag route</button>
            <button className="control-button" type="button" disabled={commandPending} onClick={liftDown}>Lift down</button>
            <button className="control-button" type="button" disabled={commandPending} onClick={uploadPatrolMission}>Upload mission</button>
            <button
              className="control-button"
              type="button"
              disabled={commandPending}
              onClick={() => sendCommand.mutate({ drone_id: selectedDroneId, action: "follow_path", path: waypoints, requested_by: "dashboard" })}
            >
              Start patrol
            </button>
          </div>
        </section>

        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Camera Feed Panel</h4>
            <span className="muted">{cameraFeed?.camera_id ?? "no-feed"}</span>
          </div>
          <div className="drone-video-preview">
            <div className="drone-video-scanline" />
            <div className="drone-video-overlay">
              <span>Live simulation feed</span>
              <strong>{cameraFeed?.preview_url ?? cameraFeed?.stream_url ?? "Camera feed unavailable"}</strong>
            </div>
          </div>
          <div className="drone-chip-row">
            {(cameraFeed?.ai_detections ?? []).map((detection) => (
              <span key={detection.label} className="drone-chip">{detection.label} {Math.round(detection.confidence * 100)}%</span>
            ))}
          </div>
          <div className="drone-command-row">
            <button className="control-button" type="button" disabled={commandPending || !cameraFeed} onClick={() => sendCommand.mutate({ drone_id: selectedDroneId, action: "start_camera_stream", camera_id: cameraFeed?.camera_id ?? null, requested_by: "dashboard" })}>Start stream</button>
            <button className="control-button" type="button" disabled={commandPending || !cameraFeed} onClick={() => sendCommand.mutate({ drone_id: selectedDroneId, action: "camera_zoom", camera_id: cameraFeed?.camera_id ?? null, zoom_level: (cameraFeed?.gimbal.zoom_level ?? 0) + 1, requested_by: "dashboard" })}>Zoom</button>
            <button className="control-button" type="button" disabled={commandPending || !cameraFeed} onClick={() => sendCommand.mutate({ drone_id: selectedDroneId, action: "gimbal_move", camera_id: cameraFeed?.camera_id ?? null, gimbal_pitch_deg: (cameraFeed?.gimbal.pitch_deg ?? 0) - 2, gimbal_yaw_deg: cameraFeed?.gimbal.yaw_deg ?? 0, requested_by: "dashboard" })}>Gimbal</button>
          </div>
        </section>

        <section className="drone-gateway-card">
          <div className="drone-gateway-card-header">
            <h4>Alerts & Threat Detection Panel</h4>
            <span className={`status-pill ${statusClass(alerts[0]?.threat_level)}`}>{alerts.length}</span>
          </div>
          <div className="drone-alert-list">
            {alerts.map((alert) => (
              <div key={alert.alert_id} className="drone-alert-row">
                <strong>{alert.title}</strong>
                <span className={`status-pill ${statusClass(alert.threat_level)}`}>{alert.threat_level}</span>
                <p className="muted">{alert.source_ids.join(" / ")} | {Math.round(alert.confidence * 100)}%</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </article>
  );
}
