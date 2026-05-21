/**
 * ============================================================================
 * File: webapp/src/pages/Dashboard.tsx
 * Purpose:
 *   Operator dashboard. Composes domain panels (recent readings, traffic
 *   summary) into a responsive grid. Each panel manages its own data
 *   fetching via React Query hooks.
 * ============================================================================
 */

import RecentReadingsPanel from "@/components/RecentReadingsPanel";
import DataFlowViewPanel from "@/components/DataFlowViewPanel";
import DeviceManagerPanel from "@/components/DeviceManagerPanel";
import OperatorControlsPanel from "@/components/OperatorControlsPanel";
import RegisteredCamerasPanel from "@/components/RegisteredCamerasPanel";
import SecurityMonitorPanel from "@/components/SecurityMonitorPanel";
import SmartMapPanel from "@/components/SmartMapPanel";
import TrafficSummaryPanel from "@/components/TrafficSummaryPanel";
import { useControlPlaneOverview, useUpdateOperatorControl } from "@/api/controlPlane";
import { useSmartMapOverview } from "@/api/map";

export default function Dashboard() {
  const { data } = useControlPlaneOverview();
  const { data: mapData } = useSmartMapOverview();
  const updateControl = useUpdateOperatorControl();

  return (
    <section className="dashboard">
      <h2>Operations Dashboard</h2>
      <p className="muted">
        Live view of the SmartCito backbone. Data refreshes automatically.
      </p>

      <div className="dashboard-grid">
        <SmartMapPanel devices={mapData?.devices ?? []} />
        <DeviceManagerPanel devices={data?.devices ?? []} />
        <RegisteredCamerasPanel />
        <SecurityMonitorPanel
          security={
            data?.security ?? {
              encryption_status: "loading",
              iam_status: "loading",
              audit_pipeline_status: "loading",
              quantum_safe_status: "loading",
              intrusion_alerts: [],
            }
          }
        />
        <TrafficSummaryPanel />
        <OperatorControlsPanel
          controls={data?.controls ?? []}
          isPending={updateControl.isPending}
          onToggle={(controlId, desiredState) =>
            updateControl.mutate({ controlId, desiredState })
          }
        />
        <DataFlowViewPanel stages={data?.data_flow ?? []} />
        <RecentReadingsPanel />
      </div>
    </section>
  );
}
