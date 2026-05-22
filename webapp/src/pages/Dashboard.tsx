/**
 * ============================================================================
 * File: webapp/src/pages/Dashboard.tsx
 * Purpose:
 *   Operator dashboard. Composes domain panels (recent readings, traffic
 *   summary) into a responsive grid. Each panel manages its own data
 *   fetching via React Query hooks.
 * ============================================================================
 */

import { lazy, Suspense } from "react";

import RecentReadingsPanel from "@/components/RecentReadingsPanel";
import DataFlowViewPanel from "@/components/DataFlowViewPanel";
import DeviceManagerPanel from "@/components/DeviceManagerPanel";
import OperatorControlsPanel from "@/components/OperatorControlsPanel";
import RegisteredCamerasPanel from "@/components/RegisteredCamerasPanel";
import SecurityMonitorPanel from "@/components/SecurityMonitorPanel";
import SmartMapPanel from "@/components/SmartMapPanel";
import TrafficSummaryPanel from "@/components/TrafficSummaryPanel";
import { useControlPlaneOverview, useUpdateOperatorControl } from "@/api/controlPlane";
import { demoSmartMapDevices, useSmartMapOverview } from "@/api/map";
import { demoSceneOverview, useSceneOverview } from "@/api/scene";

const ThreeDashboardPanel = lazy(() => import("@/components/ThreeDashboardPanel"));

function hasVisibleMapDevices(devices: typeof demoSmartMapDevices | undefined) {
  return Boolean(devices?.some((device) => device.trust_score > 80));
}

function hasVisibleSceneDevices(sceneData: typeof demoSceneOverview | undefined) {
  return Boolean(sceneData?.devices.some((device) => device.trust_score > 80));
}

export default function Dashboard() {
  const { data } = useControlPlaneOverview();
  const { data: mapData } = useSmartMapOverview();
  const { data: sceneData } = useSceneOverview();
  const updateControl = useUpdateOperatorControl();
  const mapDevices = hasVisibleMapDevices(mapData?.devices) ? mapData!.devices : demoSmartMapDevices;
  const scene = hasVisibleSceneDevices(sceneData)
    ? {
        ...sceneData!,
        threats: sceneData!.threats.length > 0 ? sceneData!.threats : demoSceneOverview.threats,
        layers: sceneData!.layers.length > 0 ? sceneData!.layers : demoSceneOverview.layers,
      }
    : demoSceneOverview;

  return (
    <section className="dashboard">
      <h2>Operations Dashboard</h2>

      <Suspense fallback={<div className="three-stage-loading">Loading 3D control plane...</div>}>
        <ThreeDashboardPanel scene={scene} />
      </Suspense>

      <div className="dashboard-grid">
        <SmartMapPanel devices={mapDevices} />
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
