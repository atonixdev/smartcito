/**
 * ============================================================================
 * File: frontend/src/pages/Home.tsx
 * Purpose:
 *   Landing page describing what SmartCito is and pointing visitors at the
 *   dashboard, docs, and GitHub.
 * ============================================================================
 */

import { Link } from "react-router-dom";

export default function Home() {
  return (
    <section className="hero">
      <h2>Urban Data Backbone for Smart Cities</h2>
      <p>
        SmartCito unifies IoT sensors, traffic systems, utilities, and citizen
        services into one secure, open hub. Real-time visualization, predictive
        analytics, and privacy-by-design — out of the box.
      </p>

      <ul className="hero-features">
        <li>🛰️ Unified ingestion (MQTT, Kafka, HTTP)</li>
        <li>🔐 Built-in RBAC, JWT, TLS, audit logs</li>
        <li>📊 Live dashboards for traffic, air quality, energy</li>
        <li>🌍 Apache 2.0 — open governance, open contributions</li>
      </ul>

      <div className="hero-actions">
        <Link className="btn primary" to="/dashboard">
          Open dashboard →
        </Link>
        <a
          className="btn"
          href="https://github.com/atonixdev/smartcito"
          target="_blank"
          rel="noreferrer"
        >
          Contribute on GitHub
        </a>
      </div>
    </section>
  );
}
