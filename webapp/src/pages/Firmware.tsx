/**
 * ============================================================================
 * File: webapp/src/pages/Firmware.tsx
 * Purpose: Firmware and device update page for the local-first Orca platform.
 * ============================================================================
 */

const channels = [
  {
    title: "Stable",
    body: "Signed firmware and runtime artifacts intended for field deployment and long-lived device fleets.",
  },
  {
    title: "Candidate",
    body: "Pre-release update builds used for hardware validation, integration checks, and operator rehearsals.",
  },
  {
    title: "Developer",
    body: "Fast-moving local builds for CLI, SDK, local agent, and firmware development with UUID-targeted test devices.",
  },
];

export default function Firmware() {
  return (
    <section className="page-shell narrative-page">
      <span className="eyebrow">Firmware updates</span>
      <h2>Signed update channels tied to device UUIDs.</h2>
      <p className="lead-text">
        ORCA firmware distribution is one of the few backend-dependent workflows
        that remains central to the platform. Devices are tracked by UUID,
        updates are delivered locally, and optional backend sync records the
        rollout state.
      </p>

      <div className="roadmap-track">
        {channels.map((channel) => (
          <article className="roadmap-item" key={channel.title}>
            <span className="eyebrow">Channel</span>
            <h3>{channel.title}</h3>
            <p>{channel.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
