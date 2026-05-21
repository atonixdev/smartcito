/**
 * ============================================================================
 * File: frontend/src/components/RecentReadingsPanel.tsx
 * Purpose:
 *   Display the most recent sensor readings as a compact table. Uses the
 *   `useRecentSensors` hook so polling and caching are handled centrally.
 * ============================================================================
 */

import { useRecentSensors } from "@/api/sensors";

export default function RecentReadingsPanel() {
  const { data, isLoading, isError, error } = useRecentSensors(20);

  return (
    <article className="panel">
      <header className="panel-header">
        <h3>Recent Sensor Readings</h3>
        <span className="muted">auto-refresh · 5s</span>
      </header>

      {isLoading && <p>Loading readings…</p>}
      {isError && (
        <p className="error">
          Could not load readings: {(error as { message?: string }).message}
        </p>
      )}

      {data && data.length === 0 && (
        <p className="muted">
          No readings yet. POST one to <code>/api/v1/sensors</code> to see it
          appear here.
        </p>
      )}

      {data && data.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Sensor</th>
              <th>Kind</th>
              <th>Value</th>
              <th>Observed</th>
            </tr>
          </thead>
          <tbody>
            {[...data].reverse().map((r) => (
              <tr key={r.id}>
                <td>{r.sensor_id}</td>
                <td>{r.kind}</td>
                <td>
                  {r.value} <span className="muted">{r.unit}</span>
                </td>
                <td>{new Date(r.observed_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}
