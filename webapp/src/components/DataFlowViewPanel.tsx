/**
 * ============================================================================
 * File: webapp/src/components/DataFlowViewPanel.tsx
 * Purpose:
 *   Pipeline view showing how device and protocol flows move through the
 *   SmartCito event backbone.
 * ============================================================================
 */

import type { DataFlowStage } from "@/api/controlPlane";

export default function DataFlowViewPanel({ stages }: { stages: DataFlowStage[] }) {
  return (
    <article className="panel panel-wide">
      <header className="panel-header">
        <h3>Data Flow View</h3>
      </header>

      <div className="pipeline-grid">
        {stages.map((stage) => (
          <div key={stage.id} className="pipeline-card">
            <span className={`status-pill ${stage.state === "healthy" ? "live" : stage.state === "blocked" ? "degraded" : "connecting"}`}>
              {stage.state}
            </span>
            <h4>{stage.name}</h4>
            <p>{stage.throughput_hint}</p>
          </div>
        ))}
      </div>
    </article>
  );
}