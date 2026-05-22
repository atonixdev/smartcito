/**
 * ============================================================================
 * File: webapp/src/pages/Mission.tsx
 * Purpose: Mission and project-positioning page for SmartCito.
 * ============================================================================
 */

import { Link } from "react-router-dom";
import { Card, Grid, IconWrapper, PageTitle, SectionContainer } from "@/components/ui";

const principles = [
  {
    title: "Open collaboration",
    body: "Software, infrastructure, hardware, and public-interest technology contributors can work from one shared platform surface.",
  },
  {
    title: "Security-first engineering",
    body: "RBAC, audit logs, encryption, and post-quantum readiness are treated as product foundations, not add-ons.",
  },
  {
    title: "Operational transparency",
    body: "Dashboards, APIs, Wiki pages, and validation workflows keep city infrastructure understandable and inspectable.",
  },
];

export default function Mission() {
  return (
    <section className="page-shell narrative-page">
      <PageTitle
        breadcrumb="Home / Mission"
        eyebrow="Mission"
        title="Mission"
        subtitle="Build a future-proof foundation for secure smart cities that communities can understand, inspect, deploy, and improve."
      />

      <SectionContainer
        title="What makes it different"
        subtitle="SmartCito connects platform code, operator UX, real maps, device validation, and security into one coherent system."
      >
        <Grid columns={3}>
          {principles.map((principle) => (
            <Card key={principle.title} title={principle.title}>
              <p>{principle.body}</p>
            </Card>
          ))}
        </Grid>
      </SectionContainer>

      <SectionContainer className="security-first-section" title="Security first">
        <div className="icon-copy-row">
          <IconWrapper>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3 5 6v5c0 4.5 2.9 8.7 7 10 4.1-1.3 7-5.5 7-10V6l-7-3Z" />
              <path d="m9 12 2 2 4-5" />
            </svg>
          </IconWrapper>
          <div>
            <h3>Protected city operations by design.</h3>
            <p>
              SmartCito combines FastAPI services, React operator views, 2D/3D
              world maps, camera and GPS modules, USB device detection,
              quantum-safe APIs, infrastructure-as-code, hardware tests, and
              Wiki-ready documentation.
            </p>
          </div>
        </div>
      </SectionContainer>

      <div className="outcome-panel">
        <h4>Foundation-ready posture</h4>
        <p>
          The current shape positions SmartCito as a serious open initiative
          that can later grow into a formal SmartCito Foundation without losing
          its personal-project roots.
        </p>
        <Link className="text-link" to="/roadmap">See the roadmap</Link>
      </div>
    </section>
  );
}