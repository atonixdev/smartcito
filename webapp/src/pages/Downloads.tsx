/**
 * ============================================================================
 * File: webapp/src/pages/Downloads.tsx
 * Purpose: Download and install page for local-first ORCA tooling.
 * ============================================================================
 */

const downloads = [
  {
    title: "ORCA CLI",
    body: "Primary local control surface for UUID device discovery, connection management, firmware checks, and operational workflows.",
    install: "python3 -m pip install .",
  },
  {
    title: "ORCA SDK",
    body: "Local developer surface for integrating device operations, firmware flows, telemetry upload, and backend synchronization when needed.",
    install: "python3 -m pip install .",
  },
  {
    title: "ORCA Service Extras",
    body: "Optional FastAPI and service runtime dependencies for local agents, firmware services, and backend adapters.",
    install: "python3 -m pip install .[services]",
  },
  {
    title: "ORCA Template Bundle",
    body: "Bootstrap local payloads and operator examples with bundled JSON templates written from the installed CLI.",
    install: "orca workspace template-write-all --output-dir ./orca-templates",
  },
];

export default function Downloads() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Downloads</span>
      <h2>CLI, SDK, TUI, and local agent deliverables.</h2>
      <p className="lead-text">
        ORCA ships as installable local tooling. Browser dashboards and account
        flows are gone; the focus is local operation, firmware-aware devices,
        and optional backend services.
      </p>

      <div className="feature-grid">
        {downloads.map((item) => (
          <article className="feature-card" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
            <p>
              <strong>{item.install}</strong>
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
