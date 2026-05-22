/**
 * ============================================================================
 * File: webapp/src/pages/Roadmap.tsx
 * Purpose: Product roadmap page for SmartCito.
 * ============================================================================
 */

const roadmap = [
  {
    horizon: "Short term",
    title: "Containerization, CI/CD, hardware validation",
    body: "Keep the Docker, GitFlow, security scanning, hardware simulation, and dashboard validation path reliable.",
  },
  {
    horizon: "Mid term",
    title: "AI model registry, blockchain audit trail, IoT expansion",
    body: "Add richer analytics, durable audit proofs, broader field-device coverage, and stronger operator workflows.",
  },
  {
    horizon: "Long term",
    title: "Quantum computing, satellite feeds, digital twin simulation",
    body: "Explore next-generation cryptography, external data feeds, city-scale simulation, and advanced decision support.",
  },
];

import { PageTitle } from "@/components/ui";

export default function Roadmap() {
  return (
    <section className="page-shell narrative-page">
      <PageTitle
        breadcrumb="Home / Roadmap"
        eyebrow="Roadmap"
        title="From practical foundation to advanced smart city platform."
        subtitle="The roadmap keeps near-term engineering grounded while leaving room for a transparent, visual, collaborative platform for secure smart city infrastructure."
      />

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