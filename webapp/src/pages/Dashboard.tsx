/**
 * ============================================================================
 * File: webapp/src/pages/Dashboard.tsx
 * Purpose:
 *   SmartCito Operations Dashboard. Single unified dashboard for location
 *   intelligence and 2D/3D operational visualization.
 * ============================================================================
 */

import LocationIntelligencePanel from "@/components/LocationIntelligencePanel";
import OperationsVisualizationPanel from "@/components/OperationsVisualizationPanel";

export default function Dashboard() {
  return (
    <section className="dashboard">
      <h2>SmartCito Operations Dashboard</h2>
      <p className="muted">
        Unified operations view for sovereign location intelligence, GPS, map,
        weather, devices, and threat visualization.
      </p>

      <div className="dashboard-grid">
        <LocationIntelligencePanel />
        <OperationsVisualizationPanel />
      </div>
    </section>
  );
}
