/**
 * ============================================================================
 * File: webapp/src/components/SecurityMonitorPanel.tsx
 * Purpose:
 *   Security monitor panel displaying encryption, IAM, audit, and intrusion
 *   status for the SmartCito control plane.
 * ============================================================================
 */

import type { SecurityMonitorStatus } from "@/api/controlPlane";

export default function SecurityMonitorPanel({ security }: { security: SecurityMonitorStatus }) {
  return (
    <article className="panel">
      <header className="panel-header">
        <h3>Security Monitor</h3>
      </header>

      <ul className="metric-list">
        <li><span className="metric-key">Encryption</span><strong>{security.encryption_status}</strong></li>
        <li><span className="metric-key">IAM</span><strong>{security.iam_status}</strong></li>
        <li><span className="metric-key">Audit</span><strong>{security.audit_pipeline_status}</strong></li>
        <li><span className="metric-key">Quantum-safe</span><strong>{security.quantum_safe_status}</strong></li>
      </ul>

      <div className="alert-list">
        {security.intrusion_alerts.map((alert) => (
          <div key={alert.id} className="alert-card">
            <strong>{alert.title}</strong>
            <span className="muted">{alert.severity} · {alert.status}</span>
          </div>
        ))}
      </div>
    </article>
  );
}