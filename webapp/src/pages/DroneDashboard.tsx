import { useMemo } from "react";

import OperationsSwitcher from "@/components/OperationsSwitcher";
import DroneOperationsPanel from "@/components/DroneOperationsPanel";
import { useDroneFleet, useDroneGatewayReady, useThreatAlerts } from "@/api/droneGateway";

function summarizeStatus(ready: boolean, alerts: number) {
  if (!ready) {
    return "Partial visibility";
  }
  if (alerts > 0) {
    return "Alert watch";
  }
  return "Nominal";
}

export default function DroneDashboard() {
  const gatewayReady = useDroneGatewayReady();
  const fleetQuery = useDroneFleet();
  const alertsQuery = useThreatAlerts();

  const telemetry = fleetQuery.data?.drones?.[0];
  const registry = fleetQuery.data?.registry?.[0];
  const alerts = alertsQuery.data ?? [];
  const linkQualityPercent = Math.round((telemetry?.link_quality ?? 0) * 100);
  const altitudeMeters = Math.round(telemetry?.position.altitude_m ?? 0);

  const statusCards = useMemo(
    () => [
      { label: "Gateway", value: gatewayReady.data?.registry ?? "offline" },
      { label: "Active drone", value: registry?.model ?? "--" },
      { label: "Battery", value: telemetry ? `${Math.round(telemetry.battery_percent)}%` : "--" },
      { label: "Flight mode", value: telemetry?.flight_mode ?? "--" },
      { label: "Link", value: `${linkQualityPercent}%` },
      { label: "Threats", value: `${alerts.length}` },
    ],
    [alerts.length, gatewayReady.data?.registry, linkQualityPercent, registry?.model, telemetry?.battery_percent, telemetry?.flight_mode],
  );

  return (
    <section className="command-center operations-page" aria-label="Drone operations dashboard">
      <header className="command-topbar operations-topbar">
        <div className="command-topbar-block">
          <span className="command-kicker">Drone dashboard</span>
          <h2>Flight Operations Console</h2>
          <p>Live simulation cockpit for telemetry, mission control, camera feed, and threat response.</p>
        </div>

        <div className="command-topbar-meta">
          <div>
            <span>System status</span>
            <strong>{summarizeStatus(Boolean(gatewayReady.data), alerts.length)}</strong>
          </div>
          <div>
            <span>Primary aircraft</span>
            <strong>{registry?.drone_id ?? "--"}</strong>
          </div>
          <div>
            <span>Altitude</span>
            <strong>{altitudeMeters} m</strong>
          </div>
        </div>
      </header>

      <OperationsSwitcher />

      <section className="operations-status-grid" aria-label="Drone overview metrics">
        {statusCards.map((card) => (
          <article key={card.label} className="operations-status-card">
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <DroneOperationsPanel />
    </section>
  );
}