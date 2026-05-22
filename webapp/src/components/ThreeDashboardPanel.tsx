/**
 * ============================================================================
 * File: webapp/src/components/ThreeDashboardPanel.tsx
 * Purpose:
 *   Dependency-free 3D-style dashboard scene for SmartCito IoT, GPS, cameras,
 *   Raspberry Pi edge nodes, and AI threat waves.
 * ============================================================================
 */

import { useMemo, useState } from "react";

import type { SceneDevice, SceneOverview } from "@/api/scene";

const layerLabels = [
  ["iot-devices", "IoT"],
  ["gps-paths", "GPS paths"],
  ["camera-overlays", "Cameras"],
  ["threat-waves", "Threat zones"],
] as const;

function projectDevice(device: SceneDevice) {
  return {
    left: `${50 + device.x * 4}%`,
    top: `${50 + device.z * 4}%`,
  };
}

export default function ThreeDashboardPanel({ scene }: { scene: SceneOverview }) {
  const [enabledLayers, setEnabledLayers] = useState(() => new Set(scene.layers));
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  const visibleDevices = useMemo(
    () => scene.devices.filter((device) => device.trust_score > 80),
    [scene.devices],
  );

  const selectedDevice = visibleDevices.find((device) => device.id === selectedDeviceId);

  function toggleLayer(layer: string) {
    setEnabledLayers((currentLayers) => {
      const nextLayers = new Set(currentLayers);
      if (nextLayers.has(layer)) {
        nextLayers.delete(layer);
      } else {
        nextLayers.add(layer);
      }
      return nextLayers;
    });
  }

  return (
    <section className="three-dashboard-stage" aria-label="SmartCito 3D control plane">
      <div className="three-stage-copy">
        <h3>SmartCito 3D Operations Scene</h3>
        <p>
          Verified IoT, GPS, camera, and edge devices rendered with GPS paths,
          camera overlays, and risk zones for operational context.
        </p>
      </div>

      <div className="three-stage-layout">
        <div className="three-stage-canvas css-three-scene" data-testid="three-dashboard-canvas">
          <div className="css-three-grid" />
          <div className="css-three-core">SmartEdge</div>

          {enabledLayers.has("gps-paths") && (
            <svg className="css-three-paths" viewBox="0 0 100 100" preserveAspectRatio="none">
              {visibleDevices.map((device) => {
                if (device.gps_path_3d.length < 2) return null;

                const points = device.gps_path_3d
                  .map(([x, , z]) => `${50 + x * 4},${50 + z * 4}`)
                  .join(" ");

                return (
                  <polyline
                    key={`${device.id}-path`}
                    points={points}
                    fill="none"
                    stroke="#57c7d4"
                    strokeWidth="0.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.85"
                  />
                );
              })}
            </svg>
          )}

          {visibleDevices.map((device) => {
            const isCamera = device.device_type === "camera";
            if (isCamera && !enabledLayers.has("camera-overlays")) return null;

            return (
              <button
                key={device.id}
                className={`css-three-device ${device.device_type}`}
                style={projectDevice(device)}
                onClick={() => setSelectedDeviceId(device.id)}
                title={`${device.name} · trust ${device.trust_score}`}
              >
                <span style={{ backgroundColor: device.status_color }} />
                <b>{device.device_type.toUpperCase()}</b>
              </button>
            );
          })}

          {enabledLayers.has("threat-waves") &&
            scene.threats.map((threat) => (
              <span
                key={threat.id}
                className={`css-three-threat ${threat.severity}`}
                style={{ left: `${50 + threat.x * 4}%`, top: `${50 + threat.z * 4}%` }}
                title={threat.label}
              />
            ))}
        </div>

        <aside className="three-stage-controls">
          <div className="three-layer-controls">
            {layerLabels.map(([layer, label]) => (
              <label key={layer}>
                <input
                  type="checkbox"
                  checked={enabledLayers.has(layer)}
                  onChange={() => toggleLayer(layer)}
                />
                {label}
              </label>
            ))}
          </div>

          <div className="three-selected-device">
            <strong>{selectedDevice?.name ?? "No device selected"}</strong>
            {selectedDevice && (
              <>
                <span>{selectedDevice.device_type} · trust {selectedDevice.trust_score}</span>
                <span>{selectedDevice.latitude.toFixed(4)}, {selectedDevice.longitude.toFixed(4)}</span>
              </>
            )}
          </div>

          <div className="three-scene-list">
            {visibleDevices.map((device) => (
              <button key={device.id} onClick={() => setSelectedDeviceId(device.id)}>
                {device.name}
              </button>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}