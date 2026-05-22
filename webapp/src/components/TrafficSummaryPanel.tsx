/**
 * ============================================================================
 * File: webapp/src/components/TrafficSummaryPanel.tsx
 * Purpose: Aggregated traffic-sensor summary card.
 * ============================================================================
 */

import { useTrafficSummary } from "@/api/sensors";

export default function TrafficSummaryPanel() {
  const { data, isLoading, isError, error } = useTrafficSummary();

  return (
    <article className="panel">
      <header className="panel-header">
        <h3>Traffic Summary</h3>
      </header>

      {isLoading && <p>Computing summary…</p>}
      {isError && (
        <p className="error">
          Could not load summary: {(error as { message?: string }).message}
        </p>
      )}

      {data && (
        <>
          <p>
            <strong>{data.total_samples}</strong> samples across{" "}
            <strong>{data.sensors.length}</strong> traffic sensors.
          </p>

          {data.sensors.length === 0 ? (
            <p className="muted">No traffic data available yet.</p>
          ) : (
            <ul className="metric-list">
              {data.sensors.map((s) => (
                <li key={s.sensor_id}>
                  <span className="metric-key">{s.sensor_id}</span>
                  <span className="metric-value">
                    {s.average_value.toFixed(2)} {s.unit}{" "}
                    <span className="muted">(n={s.samples})</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </article>
  );
}
