/**
 * ============================================================================
 * File: webapp/src/components/OperatorControlsPanel.tsx
 * Purpose:
 *   Operator controls for starting and stopping services or policy sets from
 *   the dashboard control plane.
 * ============================================================================
 */

import type { OperatorControl, OperatorControlState } from "@/api/controlPlane";

export default function OperatorControlsPanel({
  controls,
  isPending,
  onToggle,
}: {
  controls: OperatorControl[];
  isPending: boolean;
  onToggle: (controlId: string, desiredState: OperatorControlState) => void;
}) {
  return (
    <article className="panel">
      <header className="panel-header">
        <h3>Operator Controls</h3>
      </header>

      <div className="control-list">
        {controls.map((control) => {
          const desiredState: OperatorControlState = control.state === "running" ? "stopped" : "running";

          return (
            <div key={control.id} className="control-card">
              <div>
                <strong>{control.name}</strong>
                <p className="muted">{control.description}</p>
              </div>
              <div className="control-actions">
                <span className={`status-pill ${control.state === "running" ? "live" : control.state === "degraded" ? "degraded" : "connecting"}`}>
                  {control.state}
                </span>
                <button
                  className="control-button"
                  type="button"
                  disabled={isPending}
                  onClick={() => onToggle(control.id, desiredState)}
                >
                  {control.action_label}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}