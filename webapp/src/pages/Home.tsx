/**
 * ============================================================================
 * File: webapp/src/pages/Home.tsx
 * Purpose:
 *   Landing page describing what SmartCito is and pointing visitors at the
 *   dashboard, docs, and GitHub.
 * ============================================================================
 */

import { Link } from "react-router-dom";

const coreFeatures = [
  {
    title: "Camera Integration",
    body: "Secure ingestion for RTSP and ONVIF streams, camera registration, stream telemetry, and tamper-aware field devices.",
  },
  {
    title: "GPS and IoT Modules",
    body: "USB, GPS, NMEA, MQTT, and sensor adapters normalize city device events into one operational backbone.",
  },
  {
    title: "Cloud Orchestration",
    body: "Kubernetes, Terraform, Docker Compose, and hardware-aware CI/CD support repeatable deployments from lab to cloud.",
  },
  {
    title: "Quantum-Safe Security",
    body: "RBAC, JWT, AES-GCM, audit trails, and post-quantum envelope services prepare the platform for future cryptography needs.",
  },
  {
    title: "Operator Dashboard",
    body: "The React control plane brings devices, security posture, data flow, and operator actions into one live interface.",
  },
];

const architectureLayers = [
  "City devices and systems",
  "Ingestion and protocol adapters",
  "Storage and event backbone",
  "Security and audit controls",
  "SmartEdge dashboard",
];

export default function Home() {
  return (
    <div className="home-page">
      <section className="landing-hero">
        <div className="hero-copy">
          <span className="eyebrow">Open smart city infrastructure</span>
          <h2>SmartCito</h2>
          <p>
            SmartCito is an open project dedicated to building secure,
            quantum-ready smart city infrastructure. It connects cameras, GPS,
            IoT devices, hardware services, and cloud systems into one unified
            backbone designed for transparency, security, and innovation.
          </p>

          <div className="hero-actions">
            <Link className="btn primary" to="/dashboard">
              Open dashboard
            </Link>
            <Link className="btn" to="/architecture">
              Explore architecture
            </Link>
          </div>
        </div>

        <div className="city-scene" aria-hidden="true">
          <div className="scene-grid" />
          <div className="scene-node node-camera">CAM</div>
          <div className="scene-node node-gps">GPS</div>
          <div className="scene-node node-iot">IOT</div>
          <div className="scene-core">SmartEdge</div>
          <div className="scene-line line-a" />
          <div className="scene-line line-b" />
          <div className="scene-line line-c" />
        </div>
      </section>

      <section className="content-section intro-section">
        <div>
          <span className="eyebrow">Mission</span>
          <h3>Open, collaborative, and future-proof by design.</h3>
        </div>
        <div className="statement-list">
          <p>Create a foundation for smart cities that is open, collaborative, and future-proof.</p>
          <p>Ensure data security with post-quantum cryptography and strong audit controls.</p>
          <p>Empower developers, governments, and communities with open dashboards and APIs.</p>
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading">
          <span className="eyebrow">Core features</span>
          <h3>Everything the platform has grown into.</h3>
        </div>
        <div className="feature-grid">
          {coreFeatures.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <h4>{feature.title}</h4>
              <p>{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section architecture-preview">
        <div className="section-heading">
          <span className="eyebrow">Architecture overview</span>
          <h3>A layered backbone for real city operations.</h3>
        </div>
        <div className="layer-stack">
          {architectureLayers.map((layer, index) => (
            <div className="layer-row" key={layer}>
              <span>{index + 1}</span>
              <strong>{layer}</strong>
            </div>
          ))}
        </div>
        <img
          className="wide-visual"
          src="/assets/platform-overview.svg"
          alt="SmartCito platform overview"
        />
      </section>

      <section className="content-section split-section">
        <div>
          <span className="eyebrow">Community</span>
          <h3>Built so many kinds of contributors can participate.</h3>
          <p>
            Developers can contribute services and containers. Designers can
            improve diagrams and Wiki visuals. Cloud engineers can expand
            infrastructure modules. Security experts can strengthen encryption,
            auditability, and compliance posture.
          </p>
        </div>
        <div className="outcome-panel">
          <h4>Outcome</h4>
          <p>
            SmartCito now reads as a personal open project with foundation-level
            ambition: transparent, visual, collaborative, and ready to evolve
            into a professional smart city infrastructure initiative.
          </p>
          <Link className="text-link" to="/community">View contribution paths</Link>
        </div>
      </section>
    </div>
  );
}
