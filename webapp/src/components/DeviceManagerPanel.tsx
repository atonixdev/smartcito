/**
 * ============================================================================
 * File: webapp/src/components/DeviceManagerPanel.tsx
 * Purpose:
 *   Device manager panel showing USB, camera, GPS, and IoT device trust and
 *   driver mapping state.
 * ============================================================================
 */

import type { ManagedDevice } from "@/api/controlPlane";

function formatTrust(trust: ManagedDevice["trust_level"]) {
  return trust.replace("_", " ");
}

export default function DeviceManagerPanel({ devices }: { devices: ManagedDevice[] }) {
  return (
    <article className="panel panel-wide">
      <header className="panel-header">
        <h3>Device Manager</h3>
      </header>

      <table className="data-table">
        <thead>
          <tr>
            <th>Device</th>
            <th>Type</th>
            <th>Trust</th>
            <th>Driver</th>
            <th>Endpoint</th>
            <th>Firmware</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>
                <div className="stack-cell">
                  <strong>{device.name}</strong>
                  <span className="muted">
                    {device.authenticated ? "authenticated" : "pending trust"}
                  </span>
                </div>
              </td>
              <td>{device.category}</td>
              <td>
                <span className={`status-pill ${device.trust_level === "verified" ? "live" : device.trust_level === "blocked" ? "degraded" : "connecting"}`}>
                  {formatTrust(device.trust_level)}
                </span>
              </td>
              <td>{device.driver_container}</td>
              <td>{device.endpoint}</td>
              <td>{device.firmware_version}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}