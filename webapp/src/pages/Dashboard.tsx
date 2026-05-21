/**
 * ============================================================================
 * File: frontend/src/pages/Dashboard.tsx
 * Purpose:
 *   Operator dashboard. Composes domain panels (recent readings, traffic
 *   summary) into a responsive grid. Each panel manages its own data
 *   fetching via React Query hooks.
 * ============================================================================
 */

import RecentReadingsPanel from "@/components/RecentReadingsPanel";
import TrafficSummaryPanel from "@/components/TrafficSummaryPanel";

export default function Dashboard() {
  return (
    <section className="dashboard">
      <h2>Operations Dashboard</h2>
      <p className="muted">
        Live view of the SmartCito backbone. Data refreshes automatically.
      </p>

      <div className="dashboard-grid">
        <TrafficSummaryPanel />
        <RecentReadingsPanel />
      </div>
    </section>
  );
}
