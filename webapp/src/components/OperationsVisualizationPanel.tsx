/**
 * ============================================================================
 * File: webapp/src/components/OperationsVisualizationPanel.tsx
 * Purpose:
 *   Dependency-free Map/GPS/Traffic/Threat/Weather/Device visualization.
 * ============================================================================
 */

import { useEffect, useState } from "react";

export type OperationsTopic = "map" | "gps" | "traffic" | "threat" | "weather" | "device";
type ViewMode = "2d" | "3d";

const topics: Record<OperationsTopic, { title: string; description: string }> = {
  map: { title: "Map Visualization", description: "City zones, roads, regions, and risk areas." },
  gps: { title: "GPS Visualization", description: "Verified coordinates, paths, and movement trails." },
  traffic: { title: "Traffic Visualization", description: "Congestion, road flow, and traffic intensity." },
  threat: { title: "Threat Visualization", description: "AI alerts, suspicious motion, and risk waves." },
  weather: { title: "Weather Visualization", description: "Rain, wind, heat, and environmental overlays." },
  device: { title: "Device Visualization", description: "IoT, camera, GPS, and Raspberry Pi edge nodes." },
};

const zones = [
  { id: "cbd", label: "CBD", x: 50, y: 45, level: "medium" },
  { id: "westlands", label: "Westlands", x: 32, y: 35, level: "low" },
  { id: "industrial", label: "Industrial", x: 65, y: 66, level: "high" },
];

const gpsPath = [
  { x: 24, y: 70 },
  { x: 36, y: 63 },
  { x: 50, y: 59 },
  { x: 68, y: 55 },
];

const traffic = [
  { id: "t1", label: "87", x: 52, y: 48, level: "high" },
  { id: "t2", label: "54", x: 38, y: 34, level: "medium" },
  { id: "t3", label: "91", x: 64, y: 66, level: "high" },
];

const weather = [
  { id: "rain", label: "Rain", x: 40, y: 30, type: "rain" },
  { id: "wind", label: "Wind", x: 70, y: 42, type: "wind" },
  { id: "heat", label: "Heat", x: 60, y: 72, type: "heat" },
];

const devices = [
  { id: "PI-NBO-01", x: 30, y: 42, type: "edge", trust: 96 },
  { id: "CAM-12", x: 56, y: 36, type: "camera", trust: 94 },
  { id: "GPS-07", x: 68, y: 55, type: "gps", trust: 89 },
  { id: "IOT-44", x: 38, y: 66, type: "iot", trust: 88 },
];

const threats = [
  { id: "threat-cam", x: 56, y: 36, severity: "high" },
  { id: "threat-gps", x: 68, y: 55, severity: "medium" },
];

export default function OperationsVisualizationPanel({
  activeTopic,
  onTopicChange,
}: {
  activeTopic: OperationsTopic;
  onTopicChange: (topic: OperationsTopic) => void;
}) {
  const [mode, setMode] = useState<ViewMode>("2d");
  const [pulse, setPulse] = useState(0);
  const active = topics[activeTopic];

  useEffect(() => {
    const timer = window.setInterval(() => setPulse((value) => value + 1), 5_000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <article className="panel panel-wide operations-viz-panel">
      <header className="operations-viz-header">
        <div>
          <h3>SmartCito Operations Visualization</h3>
          <p className="muted">{active.title} — {active.description}</p>
        </div>

        <div className="viz-mode-toggle">
          <button className={mode === "2d" ? "active" : ""} onClick={() => setMode("2d")}>2D</button>
          <button className={mode === "3d" ? "active" : ""} onClick={() => setMode("3d")}>3D</button>
        </div>
      </header>

      <div className="viz-topic-tabs">
        {Object.entries(topics).map(([key, item]) => (
          <button
            key={key}
            className={activeTopic === key ? "active" : ""}
            onClick={() => onTopicChange(key as OperationsTopic)}
          >
            {item.title.replace(" Visualization", "")}
          </button>
        ))}
      </div>

      <div className={`operations-viz-map mode-${mode} topic-${activeTopic}`} data-pulse={pulse}>
        <div className="operations-grid" />
        <span className="operations-road road-primary" />
        <span className="operations-road road-secondary" />
        <span className="operations-road road-tertiary" />

        {activeTopic === "map" && zones.map((zone) => (
          <button key={zone.id} className={`viz-zone ${zone.level}`} style={{ left: `${zone.x}%`, top: `${zone.y}%` }}>
            {zone.label}
          </button>
        ))}

        {activeTopic === "gps" && (
          <>
            <svg className="viz-path-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
              <polyline points={gpsPath.map((p) => `${p.x},${p.y}`).join(" ")} fill="none" stroke="#f1c96b" strokeWidth="0.8" />
            </svg>
            {gpsPath.map((point) => (
              <span key={`${point.x}-${point.y}`} className="viz-gps-dot" style={{ left: `${point.x}%`, top: `${point.y}%` }} />
            ))}
          </>
        )}

        {activeTopic === "traffic" && traffic.map((item) => (
          <button key={item.id} className={`viz-traffic ${item.level}`} style={{ left: `${item.x}%`, top: `${item.y}%` }}>
            {item.label}
          </button>
        ))}

        {activeTopic === "weather" && weather.map((item) => (
          <button key={item.id} className={`viz-weather ${item.type}`} style={{ left: `${item.x}%`, top: `${item.y}%` }}>
            {item.label}
          </button>
        ))}

        {activeTopic === "device" && devices.map((device) => (
          <button key={device.id} className={`viz-device ${device.type}`} style={{ left: `${device.x}%`, top: `${device.y}%` }}>
            <span />
            <small>{device.type}</small>
          </button>
        ))}

        {activeTopic === "threat" && threats.map((threat) => (
          <button key={threat.id} className={`viz-threat ${threat.severity}`} style={{ left: `${threat.x}%`, top: `${threat.y}%` }} />
        ))}
      </div>
    </article>
  );
}
