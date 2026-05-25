/**
 * ============================================================================
 * File: webapp/src/pages/Visualization.tsx
 * Purpose:
 *   Unified visualization and observability surface for Dash, Grafana, and
 *   Kibana. Uses relative URLs so the page works behind either the local
 *   compose gateway or the Kubernetes visualization gateway.
 * ============================================================================
 */

const observabilitySurfaces = [
  {
    title: "Plotly Dash",
    eyebrow: "Operations analytics",
    description:
      "Live sensor and telemetry visualizations rendered by the backend Dash side-app.",
    href: "/dash/",
    embedSrc: "/dash/",
  },
  {
    title: "Grafana",
    eyebrow: "Metrics and alerts",
    description:
      "Prometheus-backed operational dashboards for cache, PostgreSQL, Kafka, and node health.",
    href: "/grafana/d/smartcito-overview/smartcito-overview?kiosk",
    embedSrc: "/grafana/d/smartcito-overview/smartcito-overview?kiosk",
  },
  {
    title: "Kibana",
    eyebrow: "Platform logs",
    description:
      "Centralized application and container log exploration flowing through Fluent Bit into Elasticsearch.",
    href: "/kibana/app/home#/",
    embedSrc: "/kibana/app/home#/?embed=true",
  },
] as const;

export default function Visualization() {
  return (
    <section className="visualization-page">
      <div className="visualization-hero">
        <div>
          <span className="eyebrow">Visualization gateway</span>
          <h2>Dash, metrics, and logs from one routed surface.</h2>
          <p className="lead-text">
            This page assumes the app is served behind the SmartCito gateway and
            keeps every observability surface on the same origin. In local
            compose, use the gateway on port 8088 for the closest parity with
            the Kubernetes deployment model.
          </p>
        </div>

        <div className="visualization-meta">
          <div>
            <strong>Local gateway</strong>
            <span>http://localhost:8088</span>
          </div>
          <div>
            <strong>Shared paths</strong>
            <span>/dash · /grafana · /kibana</span>
          </div>
        </div>
      </div>

      <div className="visualization-grid">
        {observabilitySurfaces.map((surface) => (
          <article className="visualization-card" key={surface.title}>
            <header className="visualization-card-header">
              <div>
                <span className="eyebrow">{surface.eyebrow}</span>
                <h3>{surface.title}</h3>
              </div>
              <a href={surface.href} target="_blank" rel="noreferrer">
                Open full surface
              </a>
            </header>

            <p>{surface.description}</p>

            <div className="visualization-frame-shell">
              <iframe
                className="visualization-frame"
                loading="lazy"
                src={surface.embedSrc}
                title={`${surface.title} embed`}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}