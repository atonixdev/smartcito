/**
 * ============================================================================
 * File: webapp/src/pages/Home.tsx
 * Purpose:
 *   Landing page describing what Orca is and pointing visitors at
 *   downloads, docs, and GitHub.
 * ============================================================================
 */

import { Link } from "react-router-dom";

import OrcaLogo from "../components/OrcaLogo";

const platformFeatures = [
  {
    title: "Local-first",
    body: "Operate from trusted local environments instead of depending on cloud-only control flows.",
  },
  {
    title: "Secure",
    body: "Built for controlled deployments, audited workflows, and a serious operator-facing security posture.",
  },
  {
    title: "Robotics + Drone support",
    body: "One platform surface for drone fleets, robotics workloads, sensor systems, and edge operations.",
  },
  {
    title: "OpenStack backend",
    body: "Use OpenStack-aligned backend services for registry, telemetry, and deployment support where needed.",
  },
  {
    title: "CLI + TUI",
    body: "Run ORCA from efficient terminal-first workflows that fit professional operator environments.",
  },
  {
    title: "SDKs",
    body: "Integrate device control, data workflows, and platform automation through developer-ready SDK surfaces.",
  },
];

export default function Home() {
  return (
    <div className="home-page">
      <section className="company-hero">
        <div className="company-hero-copy">
          <div className="hero-brand-row">
            <OrcaLogo className="hero-mark" title="ORCA platform mark" />
            <span className="eyebrow">Local-first robotics foundation</span>
          </div>
          <h2>ORCA is a secure, local-first robotics and drone control platform.</h2>
          <p>
            ORCA delivers a professional control surface for robotics, drones,
            sensors, and edge infrastructure with enterprise-grade operational
            discipline, transparent open-source delivery, and installable local
            tooling.
          </p>

          <div className="hero-actions">
            <Link className="btn primary" to="/downloads">
              Download ORCA
            </Link>
            <Link className="btn" to="/docs">
              View Documentation
            </Link>
          </div>
        </div>

        <div className="hero-presence" aria-hidden="true">
          <div className="presence-orbit orbit-a" />
          <div className="presence-orbit orbit-b" />
          <div className="presence-panel">
            <span>ORCA Platform</span>
            <strong>Robotics. Drones. Security. Control.</strong>
            <p>Trusted local operations with optional backend services.</p>
          </div>
        </div>
      </section>

      <section className="content-section homepage-features">
        <div className="section-heading">
          <span className="eyebrow">Platform capabilities</span>
          <h3>Enterprise-ready capabilities with a clear public surface.</h3>
          <p className="section-copy">
            ORCA keeps the public experience focused on what matters: what the
            platform is, how to get it, and why operators and developers can
            trust it.
          </p>
        </div>
        <div className="feature-grid">
          {platformFeatures.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <h4>{feature.title}</h4>
              <p>{feature.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
