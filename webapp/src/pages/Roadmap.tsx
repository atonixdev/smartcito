/**
 * ============================================================================
 * File: webapp/src/pages/Roadmap.tsx
 * Purpose: Product roadmap page for Orca.
 * ============================================================================
 */

const roadmap = [
  {
    horizon: "Short term",
    title: "CLI, TUI, local agent, firmware delivery",
    body: "Keep the local tooling stack, UUID device flows, firmware packaging, and hardware validation path reliable.",
  },
  {
    horizon: "Mid term",
    title: "Device registry, telemetry storage, map synchronization",
    body: "Expand OpenStack-backed registry, optional telemetry persistence, map data services, and offline-first workflows.",
  },
  {
    horizon: "Long term",
    title: "Quantum-safe operations, satellite feeds, digital twin simulation",
    body: "Explore next-generation cryptography, external data feeds, city-scale simulation, and advanced device-side decision support.",
  },
];

export default function Roadmap() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Roadmap</span>
      <h2>
        From secure device operations to advanced infrastructure platform.
      </h2>
      <p className="lead-text">
        The roadmap keeps near-term engineering grounded while leaving room for
        the larger vision: a transparent, installable, collaborative platform
        for secure smart city and robotics infrastructure.
      </p>

      <div className="roadmap-track">
        {roadmap.map((item) => (
          <article className="roadmap-item" key={item.horizon}>
            <span className="eyebrow">{item.horizon}</span>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
