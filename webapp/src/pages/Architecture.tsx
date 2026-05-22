/**
 * ============================================================================
 * File: webapp/src/pages/Architecture.tsx
 * Purpose: Frontend architecture overview page for SmartCito.
 * ============================================================================
 */

const layers = [
  {
    title: "City Devices and Systems",
    body: "Cameras, GPS receivers, USB bridges, IoT sensors, racks, and field hardware become registered, monitored assets.",
  },
  {
    title: "Ingestion and Protocol Adapters",
    body: "RTSP, ONVIF, MQTT, NMEA, HTTP, and device drivers normalize raw signals into service-ready data.",
  },
  {
    title: "Storage and Event Backbone",
    body: "PostgreSQL, Kafka, Redis, and storage-aligned modules provide persistence, event movement, and replayable context.",
  },
  {
    title: "Security and Audit Controls",
    body: "JWT, RBAC, AES-GCM, audit events, security policies, and quantum-ready envelopes protect control-plane operations.",
  },
  {
    title: "SmartEdge Dashboard",
    body: "React pages expose the device manager, security monitor, data-flow view, traffic summaries, and operator controls.",
  },
];

export default function Architecture() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Architecture overview</span>
      <h2>Layered from field devices to operator decisions.</h2>
      <p className="lead-text">
        SmartCito is built as a layered architecture so protocol adapters,
        storage, security, cloud orchestration, and dashboards can evolve
        independently while still operating as one backbone.
      </p>

      <img
        className="wide-visual"
        src="/assets/platform-overview.svg"
        alt="SmartCito platform architecture"
      />

      <div className="architecture-list">
        {layers.map((layer, index) => (
          <article className="architecture-item" key={layer.title}>
            <span>{index + 1}</span>
            <div>
              <h3>{layer.title}</h3>
              <p>{layer.body}</p>
            </div>
          </article>
        ))}
      </div>

      <div className="visual-grid">
        <img src="/assets/ingestion-protocols.svg" alt="Ingestion protocol adapters" />
        <img src="/assets/storage-backbone.svg" alt="Storage and event backbone" />
        <img src="/assets/security-quantum.svg" alt="Security and quantum-safe controls" />
        <img src="/assets/dashboard-views.svg" alt="Dashboard and operator views" />
      </div>
    </section>
  );
}