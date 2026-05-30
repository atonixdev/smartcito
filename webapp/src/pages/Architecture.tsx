/**
 * ============================================================================
 * File: webapp/src/pages/Architecture.tsx
 * Purpose: Frontend architecture overview page for Orca.
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
    body: "AES-GCM, audit events, firmware integrity, policy controls, and quantum-ready envelopes protect local and backend workflows.",
  },
  {
    title: "Local Tooling Layer",
    body: "CLI, terminal dashboard, SDK, and local agent surfaces operate against device UUIDs and optional OpenStack-backed services.",
  },
];

const assetBasePath = `${import.meta.env.BASE_URL}assets/`;

export default function Architecture() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Architecture overview</span>
      <h2>Layered from device firmware to local operator tooling.</h2>
      <p className="lead-text">
        Orca is built as a layered architecture so protocol adapters, storage,
        security, firmware distribution, local tooling, and optional backend
        services can evolve independently while still operating as one backbone.
      </p>

      <img
        className="wide-visual"
        src={`${assetBasePath}platform-overview.svg`}
        alt="Orca platform architecture"
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
        <img
          src={`${assetBasePath}ingestion-protocols.svg`}
          alt="Ingestion protocol adapters"
        />
        <img
          src={`${assetBasePath}storage-backbone.svg`}
          alt="Storage and event backbone"
        />
        <img
          src={`${assetBasePath}security-quantum.svg`}
          alt="Security and quantum-safe controls"
        />
      </div>
    </section>
  );
}
