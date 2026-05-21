/**
 * ============================================================================
 * File: webapp/src/pages/Mission.tsx
 * Purpose: Mission and project-positioning page for SmartCito.
 * ============================================================================
 */

import { Link } from "react-router-dom";

const principles = [
  "Open collaboration across software, infrastructure, hardware, and public-interest technology.",
  "Security-first engineering with RBAC, audit logs, encryption, and post-quantum readiness.",
  "Operational transparency through dashboards, APIs, Wiki pages, and validation workflows.",
];

export default function Mission() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Mission statement</span>
      <h2>Build a future-proof foundation for secure smart cities.</h2>
      <p className="lead-text">
        SmartCito exists to connect cameras, GPS, IoT devices, cloud systems,
        and hardware validation into one open backbone that communities can
        understand, inspect, deploy, and improve.
      </p>

      <div className="feature-grid compact-grid">
        {principles.map((principle) => (
          <article className="feature-card" key={principle}>
            <p>{principle}</p>
          </article>
        ))}
      </div>

      <div className="split-section content-section inset-section">
        <div>
          <h3>What makes it different</h3>
          <p>
            The project is not only a dashboard. It combines FastAPI services,
            React operator views, camera and GPS modules, USB device detection,
            quantum-safe APIs, infrastructure-as-code, hardware tests, and
            Wiki-ready documentation.
          </p>
        </div>
        <div className="outcome-panel">
          <h4>Foundation-ready posture</h4>
          <p>
            The current shape positions SmartCito as a serious open initiative
            that can later grow into a formal SmartCito Foundation without
            losing its personal-project roots.
          </p>
          <Link className="text-link" to="/roadmap">See the roadmap</Link>
        </div>
      </div>
    </section>
  );
}