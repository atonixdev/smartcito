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

const coreFeatures = [
  {
    title: "Local CLI",
    body: "Primary local control surface for UUID device discovery, connection management, firmware checks, and operational workflows.",
  },
  {
    title: "Terminal Dashboard",
    body: "A local TUI focused on device state, firmware, telemetry, and diagnostics without depending on a cloud-hosted browser dashboard.",
  },
  {
    title: "UUID Device Identity",
    body: "Each drone or robot is identified by firmware-burned UUIDs instead of user accounts, passwords, or browser sessions.",
  },
  {
    title: "OpenStack-aligned Backend",
    body: "OpenStack services remain available for device registry, firmware delivery, optional telemetry storage, and optional map data synchronization.",
  },
  {
    title: "Developer SDK",
    body: "Python SDK and local agent surfaces give developers consistent device operations without routing everything through a browser UI.",
  },
];

const proofPoints = [
  { value: "5", label: "architecture layers" },
  { value: "UUID", label: "device identity root" },
  { value: "TUI", label: "local operator surface" },
  { value: "CI", label: "hardware-aware validation" },
];

const governanceSignals = [
  "Apache 2.0 open-source licensing",
  "GitFlow branch governance and CI checks",
  "Security posture documented with audit trails",
  "Hardware, CLI, SDK, and local agent modules validated together",
];

const architectureLayers = [
  "Device UUID and firmware identity",
  "Local CLI, TUI, and local agent",
  "Ingestion and protocol adapters",
  "Optional OpenStack services",
  "Documentation and developer guides",
];

const platformOverviewAsset = `${import.meta.env.BASE_URL}assets/platform-overview.svg`;

export default function Home() {
  return (
    <div className="home-page">
      <section className="landing-hero">
        <div className="hero-copy">
          <div className="hero-brand-row">
            <OrcaLogo className="hero-mark" title="ORCA platform mark" />
            <span className="eyebrow">Open smart city infrastructure</span>
          </div>
          <h2>Orca</h2>
          <p>
            Orca is a local-first robotics and device operations platform. It
            centers on CLI, TUI, SDK, and local-agent workflows, uses
            firmware-burned UUIDs instead of user accounts, and keeps backend
            services focused on registry, firmware, telemetry, and optional map
            data.
          </p>

          <div className="foundation-strip" aria-label="Project positioning">
            <span>Local-first operations</span>
            <span>OpenStack-grade visual language</span>
            <span>Kubernetes and OLM inspired platform posture</span>
          </div>

          <div className="hero-actions">
            <Link className="btn primary" to="/downloads">
              Get Orca tools
            </Link>
            <Link className="btn" to="/docs">
              Read docs
            </Link>
          </div>
        </div>

        <div className="city-scene" aria-hidden="true">
          <div className="scene-grid" />
          <div className="scene-node node-camera">CLI</div>
          <div className="scene-node node-gps">TUI</div>
          <div className="scene-node node-iot">SDK</div>
          <div className="scene-core">UUID</div>
          <div className="scene-line line-a" />
          <div className="scene-line line-b" />
          <div className="scene-line line-c" />
        </div>
      </section>

      <section className="proof-band" aria-label="Orca proof points">
        {proofPoints.map((item) => (
          <div className="proof-item" key={item.label}>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </section>

      <section className="content-section intro-section">
        <div>
          <span className="eyebrow">Mission</span>
          <h3>Open, collaborative, and future-proof by design.</h3>
          <p className="section-copy">
            ORCA now follows a local-first operations model: public
            architecture, installable tools, UUID-based devices, validated
            runtime paths, and optional backend services rather than browser
            dashboards.
          </p>
        </div>
        <div className="statement-list">
          <p>
            Run ORCA locally with a CLI, terminal dashboard, SDK, and local
            agent.
          </p>
          <p>
            Use firmware-burned UUIDs instead of user accounts, passwords, or
            browser sessions.
          </p>
          <p>
            Keep backend services focused on registry, updates, telemetry, and
            optional map data.
          </p>
        </div>
      </section>

      <section className="content-section foundation-section">
        <div className="section-heading">
          <span className="eyebrow">Foundation-grade posture</span>
          <h3>Built to look and operate like serious open infrastructure.</h3>
        </div>
        <div className="governance-grid">
          <article className="governance-panel primary-panel">
            <h4>Open governance baseline</h4>
            <p>
              ORCA is positioned as open infrastructure with a serious
              operator-facing look and feel inspired by OpenStack, Kubernetes,
              and Operator Lifecycle Manager, but centered on local tools
              instead of cloud dashboards.
            </p>
          </article>
          <div className="governance-list">
            {governanceSignals.map((signal) => (
              <div className="governance-item" key={signal}>
                <span />
                <strong>{signal}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading">
          <span className="eyebrow">Core features</span>
          <h3>What the platform is centered on now.</h3>
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
          <h3>A layered backbone for local-first device operations.</h3>
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
          src={platformOverviewAsset}
          alt="Orca platform overview"
        />
      </section>

      <section className="content-section split-section">
        <div>
          <span className="eyebrow">Community</span>
          <h3>Built so every discipline has a real place to contribute.</h3>
          <p>
            Developers can contribute CLI commands, SDKs, local agents, hardware
            services, firmware flows, and documentation. Designers can improve
            downloads, docs, diagrams, and infrastructure-style presentation
            without maintaining browser dashboards.
          </p>
        </div>
        <div className="outcome-panel">
          <h4>Outcome</h4>
          <p>
            ORCA reads as a local-first infrastructure platform: transparent,
            installable, operationally serious, and ready to evolve around CLI,
            TUI, SDK, firmware, and device registry flows.
          </p>
          <Link className="text-link" to="/community">
            View contribution paths
          </Link>
        </div>
      </section>
    </div>
  );
}
