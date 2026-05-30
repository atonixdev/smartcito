/**
 * ============================================================================
 * File: webapp/src/pages/Docs.tsx
 * Purpose: Documentation landing page for ORCA platform operations.
 * ============================================================================
 */

const docSections = [
  {
    title: "Platform Overview",
    body: "Understand the ORCA platform architecture, including CLI, TUI, SDK, local agent, UUID identity, and optional OpenStack integration.",
  },
  {
    title: "Developer Guides",
    body: "Build local workflows, install package extras, integrate the SDK, and extend device operations without relying on browser dashboards.",
  },
  {
    title: "Firmware Updates",
    body: "Track update channels, signed release artifacts, and firmware rollout strategy tied to device UUID registry entries.",
  },
  {
    title: "Backend Services",
    body: "Use OpenStack-backed registry, optional telemetry persistence, and optional map data services only where they add value to local operations.",
  },
];

export default function Docs() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Documentation</span>
      <h2>Pages and guides instead of cloud dashboards.</h2>
      <p className="lead-text">
        The website is now a product explanation and documentation surface with
        an infrastructure-console visual language inspired by OpenStack,
        Kubernetes, and Operator Lifecycle Manager.
      </p>

      <div className="feature-grid">
        {docSections.map((item) => (
          <article className="feature-card" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
