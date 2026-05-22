import { useServiceHealth } from "@/api/services";
import { useCountries } from "@/api/location";

export default function BackendConnectionPanel() {
  const services = useServiceHealth();
  const countries = useCountries();

  return (
    <section className="panel panel-wide backend-connection-panel">
      <div className="panel-header">
        <div>
          <h3>Backend Connections</h3>
          <p className="muted">
            Frontend is connected through Vite proxies to FastAPI, Location/Map,
            and GPS services.
          </p>
        </div>
        <span className="status-pill live">API Bridge</span>
      </div>

      <div className="connection-grid">
        {(services.data ?? []).map((service) => (
          <div className="connection-card" key={service.name}>
            <strong>{service.name}</strong>
            <span className={`status-pill ${service.status}`}>
              {service.status}
            </span>
            <small>{service.detail}</small>
          </div>
        ))}

        <div className="connection-card">
          <strong>Map Dataset</strong>
          <span className={`status-pill ${countries.isSuccess ? "live" : "connecting"}`}>
            {countries.isSuccess ? "live" : "connecting"}
          </span>
          <small>
            {countries.data?.length
              ? `${countries.data.length} countries loaded`
              : "waiting for Location API"}
          </small>
        </div>
      </div>
    </section>
  );
}
