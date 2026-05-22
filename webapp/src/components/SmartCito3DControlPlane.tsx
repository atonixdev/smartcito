import { useEffect, useMemo, useState } from "react";
import {
  audit3DVisualizationEvent,
  fetchSmartCito3DDashboard,
  SmartCito3DDashboardPayload,
  SmartCito3DDevice,
  SmartCito3DDeviceType,
} from "@/api/dashboard3d";
import "./SmartCito3DControlPlane.css";

const layers: Array<{ key: SmartCito3DDeviceType | "threats" | "paths"; label: string }> = [
  { key: "edge", label: "Raspberry Pi" },
  { key: "iot", label: "IoT" },
  { key: "gps", label: "GPS" },
  { key: "camera", label: "Camera" },
  { key: "threats", label: "Threats" },
  { key: "paths", label: "GPS Paths" },
];

function toX(x: number) {
  return `${50 + x / 1.5}%`;
}

function toY(z: number) {
  return `${50 + z / 1.5}%`;
}

export default function SmartCito3DControlPlane() {
  const [payload, setPayload] = useState<SmartCito3DDashboardPayload | null>(null);
  const [selected, setSelected] = useState<SmartCito3DDevice | null>(null);
  const [enabledLayers, setEnabledLayers] = useState<Record<string, boolean>>({
    edge: true,
    iot: true,
    gps: true,
    camera: true,
    threats: true,
    paths: true,
  });

  useEffect(() => {
    let active = true;

    fetchSmartCito3DDashboard().then((data) => {
      if (active) setPayload(data);
    });

    const timer = window.setInterval(() => {
      fetchSmartCito3DDashboard().then((data) => {
        if (active) setPayload(data);
      });
    }, 10_000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const devices = useMemo(
    () => (payload?.devices ?? []).filter((device) => enabledLayers[device.type]),
    [payload, enabledLayers],
  );

  function toggleLayer(key: string) {
    setEnabledLayers((current) => ({ ...current, [key]: !current[key] }));
  }

  function selectDevice(device: SmartCito3DDevice) {
    setSelected(device);
    audit3DVisualizationEvent({
      action: "3d.device.selected",
      device_id: device.id,
      type: device.type,
      status: device.status,
      trust_score: device.trust_score,
    });
  }

  return (
    <section className="panel panel-wide smartcito-3d-control">
      <div className="smartcito-3d-header">
        <div>
          <p className="smartcito-3d-eyebrow">3D Control Plane</p>
          <h3>IoT, GPS, Map, Camera, Threats, and Raspberry Pi Edge Nodes</h3>
          <p className="muted">
            Devices are rendered from backend 3D-ready data with trust scoring,
            camera overlays, GPS paths, and ATP visualization audit events.
          </p>
        </div>
        <span className="status-pill live">3D Map Online</span>
      </div>

      <div className="smartcito-3d-layout">
        <aside className="smartcito-3d-sidebar">
          <strong>Operator Layers</strong>
          <div className="smartcito-3d-layer-list">
            {layers.map((layer) => (
              <button
                key={layer.key}
                className={enabledLayers[layer.key] ? "active" : ""}
                onClick={() => toggleLayer(layer.key)}
              >
                {layer.label}
              </button>
            ))}
          </div>

          <strong>Authorized Objects</strong>
          <div className="smartcito-3d-device-list">
            {payload?.devices.map((device) => (
              <button
                key={device.id}
                className="smartcito-3d-device-card"
                onClick={() => selectDevice(device)}
              >
                <span className={`trust-dot ${device.status}`} />
                <b>{device.id}</b>
                <small>
                  {device.type} · trust {device.trust_score}%
                </small>
              </button>
            ))}
          </div>
        </aside>

        <div className="smartcito-3d-map-shell">
          <div className="smartcito-3d-map">
            <div className="city-grid" />
            <div className="city-road road-one" />
            <div className="city-road road-two" />
            <div className="city-hub">ATP</div>

            {enabledLayers.paths &&
              payload?.gps_paths.map((path) =>
                path.points.map((point, index) => (
                  <span
                    key={`${path.device_id}-${index}`}
                    className="gps-path-point"
                    style={{ left: toX(point.x), top: toY(point.z) }}
                  />
                )),
              )}

            {devices.map((device) => (
              <button
                key={device.id}
                className={`smartcito-3d-pin ${device.type} ${device.status}`}
                style={{ left: toX(device.x), top: toY(device.z) }}
                onClick={() => selectDevice(device)}
                title={`${device.id} · ${device.name}`}
              >
                <span />
                <b>{device.type}</b>
              </button>
            ))}

            {enabledLayers.threats &&
              payload?.threats.map((threat) => (
                <div
                  key={threat.id}
                  className={`threat-wave ${threat.severity}`}
                  style={{ left: toX(threat.x), top: toY(threat.z) }}
                  title={threat.label}
                />
              ))}
          </div>

          {selected && (
            <article className="smartcito-3d-popup">
              <button className="popup-close" onClick={() => setSelected(null)}>
                ×
              </button>
              <h3>{selected.name}</h3>
              <p>
                <strong>ID:</strong> {selected.id}
              </p>
              <p>
                <strong>Type:</strong> {selected.type}
              </p>
              <p>
                <strong>Status:</strong> {selected.status}
              </p>
              <p>
                <strong>Trust:</strong> {selected.trust_score}%
              </p>
              <p>
                <strong>GPS:</strong> {selected.latitude}, {selected.longitude}
              </p>
              <p>
                <strong>Telemetry:</strong> {selected.telemetry}
              </p>

              {selected.type === "camera" && (
                <div className="camera-overlay">
                  <strong>LIVE CAMERA OVERLAY</strong>
                  <small>{selected.camera_stream ?? "stream pending"}</small>
                </div>
              )}
            </article>
          )}
        </div>
      </div>
    </section>
  );
}
