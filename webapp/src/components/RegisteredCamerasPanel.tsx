/**
 * ============================================================================
 * File: webapp/src/components/RegisteredCamerasPanel.tsx
 * Purpose:
 *   Fleet panel showing registered cameras, stream state, GPS telemetry, and
 *   mount/tamper indicators.
 * ============================================================================
 */

import { demoCameraFleet, useCameras } from "@/api/cameras";

function formatLocation(lat?: number, lon?: number) {
  if (lat == null || lon == null) {
    return "No fix";
  }
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}

export default function RegisteredCamerasPanel() {
  const { data, isLoading, isError, error } = useCameras();
  const cameras = data && data.length > 0 ? data : demoCameraFleet;

  return (
    <article className="panel panel-wide">
      <header className="panel-header">
        <h3>Registered Cameras</h3>
      </header>

      {isLoading && <p>Loading camera fleet…</p>}
      {isError && (
        <p className="muted">
          Camera API unavailable: {(error as { message?: string }).message}. Showing demo fleet.
        </p>
      )}

      {!isLoading && cameras.length === 0 && (
        <p className="muted">No cameras available yet.</p>
      )}

      {cameras.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Device</th>
              <th>Type</th>
              <th>Stream</th>
              <th>GPS</th>
              <th>Mount</th>
              <th>Battery</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((camera) => (
              <tr key={camera.id}>
                <td>
                  <div className="stack-cell">
                    <strong>{camera.device_id}</strong>
                    <span className="muted">fw {camera.firmware_version}</span>
                  </div>
                </td>
                <td>{camera.device_type.replace("_", " ")}</td>
                <td>
                  <span className={`status-pill ${camera.stream_status}`}>
                    {camera.stream_status}
                  </span>
                </td>
                <td>
                  {formatLocation(camera.location?.lat, camera.location?.lon)}
                </td>
                <td>{camera.mounted == null ? "unknown" : camera.mounted ? "mounted" : "removed"}</td>
                <td>{camera.battery_level == null ? "-" : `${camera.battery_level}%`}</td>
                <td>
                  {camera.tamper_detected ? (
                    <span className="status-pill degraded">tamper</span>
                  ) : (
                    <span className="muted">normal</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}
