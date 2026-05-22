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
      <div className="dashboard-grid">
        <LocationIntelligencePanel />
        <OperationsVisualizationPanel />
        <RecentReadingsPanel />
      </div>
    </section>
  );
}
