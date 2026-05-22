/**
 * ============================================================================
 * File: webapp/src/pages/Home.tsx
 * Purpose:
 *   Landing page describing what SmartCito is and verifying frontend-to-backend
 *   API communication.
 * ============================================================================
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type ApiStatus = "checking" | "online" | "offline";

export default function Home() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/v1/health/live", { signal: controller.signal })
      .then((response) => {
        setApiStatus(response.ok ? "online" : "offline");
      })
      .catch(() => {
        setApiStatus("offline");
      });

    return () => controller.abort();
  }, []);

  return (
    <section className="hero">
      <h2>Urban Data Backbone for Smart Cities</h2>
      <p>
        SmartCito unifies IoT sensors, traffic systems, utilities, and citizen
        services into one secure, open hub. Real-time visualization, predictive
        analytics, and privacy-by-design — out of the box.
      </p>

      <div className={`api-status ${apiStatus}`}>
        <strong>Backend API:</strong>{" "}
        {apiStatus === "checking" && "Checking connection…"}
        {apiStatus === "online" && "Connected"}
        {apiStatus === "offline" && "Offline — start citosmart backend"}
      </div>

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
