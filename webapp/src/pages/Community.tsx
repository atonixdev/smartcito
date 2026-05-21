/**
 * ============================================================================
 * File: webapp/src/pages/Community.tsx
 * Purpose: Community and contribution page for SmartCito.
 * ============================================================================
 */

const contributionPaths = [
  {
    title: "Developers",
    body: "Contribute FastAPI endpoints, React panels, service containers, protocol adapters, tests, and SDK clients.",
  },
  {
    title: "Designers",
    body: "Improve dashboard layouts, Wiki visuals, operational diagrams, architecture pages, and contributor onboarding flows.",
  },
  {
    title: "Cloud Engineers",
    body: "Expand Kubernetes, Terraform, Docker, GitFlow, CI/CD, OpenStack, and hardware validation modules.",
  },
  {
    title: "Security Experts",
    body: "Harden IAM, audit controls, post-quantum envelope handling, policy checks, scanning, and compliance evidence.",
  },
];

export default function Community() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Community and contribution</span>
      <h2>Open to everyone who wants cities to be safer and more transparent.</h2>
      <p className="lead-text">
        SmartCito is built for practical contribution. The repo contains active
        backend code, frontend pages, hardware modules, security services,
        infrastructure automation, CI validation, and Wiki-ready documentation.
      </p>

      <div className="feature-grid">
        {contributionPaths.map((path) => (
          <article className="feature-card" key={path.title}>
            <h3>{path.title}</h3>
            <p>{path.body}</p>
          </article>
        ))}
      </div>

      <div className="content-section split-section inset-section">
        <div>
          <h3>How collaboration stays grounded</h3>
          <p>
            Contributions should connect back to a real platform surface:
            a service endpoint, a dashboard module, an infrastructure workflow,
            a hardware validation path, or documentation that helps people run
            and understand the system.
          </p>
        </div>
        <div className="outcome-panel">
          <h4>Repository surfaces</h4>
          <p>
            Backend, webapp, hardware, security, infrastructure, scripts,
            native extensions, and docs all have working entry points for
            focused contributions.
          </p>
          <a
            className="text-link"
            href="https://github.com/atonixdev/smartcito"
            target="_blank"
            rel="noreferrer"
          >
            Open GitHub repository
          </a>
        </div>
      </div>
    </section>
  );
}