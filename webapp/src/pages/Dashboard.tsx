/**
 * ============================================================================
 * File: webapp/src/pages/Dashboard.tsx
 * Purpose:
 *   SmartCito Operations Dashboard. Single unified dashboard for location
 *   intelligence, 2D/3D visualization, and operational logs.
 * ============================================================================
 */

import LocationIntelligencePanel from "@/components/LocationIntelligencePanel";
import OperationsVisualizationPanel from "@/components/OperationsVisualizationPanel";
import RecentReadingsPanel from "@/components/RecentReadingsPanel";

export default function Dashboard() {
  return (
    <section className="dashboard">
      <h2>SmartCito Operations Dashboard</h2>
      <p className="muted">
        Unified operations view for sovereign location intelligence, GPS, map,
        weather, devices, threat visualization, and live operational logs.
      </p>

      <div className="dashboard-grid">
        <LocationIntelligencePanel />
        <OperationsVisualizationPanel />
        <RecentReadingsPanel />
      </div>
    </section>
  );
}
