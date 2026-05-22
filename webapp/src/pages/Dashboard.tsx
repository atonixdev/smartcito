/**
 * ============================================================================
 * File: webapp/src/pages/Dashboard.tsx
 * Purpose:
 *   SmartCito Operations Dashboard. Single unified dashboard for location
 *   intelligence, 2D/3D visualization, and operational logs.
 * ============================================================================
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";

import LocationIntelligencePanel from "@/components/LocationIntelligencePanel";
import OperationsVisualizationPanel, {
  type OperationsTopic,
} from "@/components/OperationsVisualizationPanel";
import UnifiedLogsThreatPanel from "@/components/UnifiedLogsThreatPanel";
import RecentReadingsPanel from "@/components/RecentReadingsPanel";

const dashboardTabs: Array<{ key: OperationsTopic; label: string }> = [
  { key: "map", label: "Map" },
  { key: "gps", label: "GPS" },
  { key: "traffic", label: "Traffic" },
  { key: "threat", label: "Security" },
  { key: "weather", label: "Weather" },
  { key: "device", label: "Device" },
];

export default function Dashboard() {
  const [activeTopic, setActiveTopic] = useState<OperationsTopic>("map");
  const navigate = useNavigate();

  return (
    <section className="dashboard operations-dashboard">
      <header className="dashboard-topbar">
        <button
          className="dashboard-brand"
          type="button"
          onClick={() => navigate("/")}
        >
          SmartCito Dashboard
        </button>

        <nav className="dashboard-tabs" aria-label="Dashboard map and data layers">
          {dashboardTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={activeTopic === tab.key ? "active" : ""}
              onClick={() => setActiveTopic(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <div className="dashboard-grid">
        <LocationIntelligencePanel />
        <OperationsVisualizationPanel
          activeTopic={activeTopic}
          onTopicChange={setActiveTopic}
        />
        <UnifiedLogsThreatPanel onThreatSelect={() => setActiveTopic("threat")} />
        <RecentReadingsPanel />
      </div>
    </section>
  );
}
