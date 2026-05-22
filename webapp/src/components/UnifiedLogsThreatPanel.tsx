/**
 * ============================================================================
 * File: webapp/src/components/UnifiedLogsThreatPanel.tsx
 * Purpose:
 *   Unified logs and AI threat analysis panel for SmartCito operations.
 * ============================================================================
 */

import { useEffect, useMemo, useState } from "react";

type LogSeverity = "info" | "warning" | "critical";
type LogType = "device" | "network" | "security" | "sensor" | "operations" | "threat";

interface UnifiedLogEvent {
  id: string;
  timestamp: string;
  type: LogType;
  severity: LogSeverity;
  device_id: string;
  country: string;
  region: string;
  area_code: string;
  ip: string;
  gps?: { latitude: number; longitude: number } | null;
  message: string;
  incident_id?: string | null;
}

interface AiThreatCase {
  id: string;
  label: string;
  threat_score: number;
  severity: LogSeverity;
  devices: string[];
  country: string;
  region: string;
  area_code: string;
  ip: string;
  gps?: { latitude: number; longitude: number } | null;
  time_window: string;
  key_log_ids: string[];
  explanation: string;
  suggested_action: string;
}

const fallbackLogs: UnifiedLogEvent[] = [
  {
    id: "demo-log-001",
    timestamp: new Date().toISOString(),
    type: "device",
    severity: "info",
    device_id: "PI-NBO-01",
    country: "KE",
    region: "NBO",
    area_code: "020",
    ip: "10.10.20.12",
    gps: { latitude: -1.2921, longitude: 36.8219 },
    message: "Edge node heartbeat normal",
    incident_id: null,
  },
  {
    id: "demo-log-002",
    timestamp: new Date().toISOString(),
    type: "security",
    severity: "critical",
    device_id: "CAM-12",
    country: "KE",
    region: "NBO",
    area_code: "020",
    ip: "41.90.12.44",
    gps: { latitude: -1.2864, longitude: 36.8172 },
    message: "Suspicious stream token failures detected",
    incident_id: "INC-DEMO-001",
  },
];

const fallbackThreats: AiThreatCase[] = [
  {
    id: "INC-DEMO-001",
    label: "Camera Stream Token Abuse",
    threat_score: 91,
    severity: "critical",
    devices: ["CAM-12"],
    country: "KE",
    region: "NBO",
    area_code: "020",
    ip: "41.90.12.44",
    gps: { latitude: -1.2864, longitude: 36.8172 },
    time_window: "last 10 minutes",
    key_log_ids: ["demo-log-002"],
    explanation: "Repeated token failures and stream access bursts are correlated against one camera endpoint.",
    suggested_action: "Block IP and rotate camera stream token",
  },
];

export default function UnifiedLogsThreatPanel({
  onThreatSelect,
}: {
  onThreatSelect?: (threat: AiThreatCase) => void;
}) {
  const [logs, setLogs] = useState<UnifiedLogEvent[]>(fallbackLogs);
  const [threats, setThreats] = useState<AiThreatCase[]>(fallbackThreats);
  const [selectedIncident, setSelectedIncident] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let active = true;

    async function loadLogs() {
      try {
        const response = await fetch("/api/location/dashboard/logs");
        if (!response.ok) throw new Error("Log API unavailable");

        const payload = await response.json();
        if (!active) return;

        setLogs(payload.logs ?? fallbackLogs);
        setThreats(payload.threats ?? fallbackThreats);
      } catch {
        if (!active) return;
        setLogs((current) => [...current]);
        setThreats(fallbackThreats);
      }
    }

    loadLogs();
    const timer = window.setInterval(loadLogs, 5_000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const regions = useMemo(
    () => Array.from(new Set(logs.map((log) => log.region))).filter(Boolean),
    [logs],
  );

  const filteredLogs = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return logs.filter((log) => {
      const matchesIncident = selectedIncident ? log.incident_id === selectedIncident : true;
      const matchesType = typeFilter === "all" || log.type === typeFilter;
      const matchesSeverity = severityFilter === "all" || log.severity === severityFilter;
      const matchesRegion = regionFilter === "all" || log.region === regionFilter;
      const matchesSearch =
        !normalizedSearch ||
        [
          log.id,
          log.device_id,
          log.ip,
          log.area_code,
          log.message,
          log.country,
          log.region,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);

      return matchesIncident && matchesType && matchesSeverity && matchesRegion && matchesSearch;
    });
  }, [logs, regionFilter, search, selectedIncident, severityFilter, typeFilter]);

  function selectThreat(threat: AiThreatCase) {
    setSelectedIncident(threat.id);
    setTypeFilter("all");
    setSeverityFilter("all");
    setSearch("");
    onThreatSelect?.(threat);
  }

  return (
    <article className="panel panel-wide unified-threat-panel">
      <header className="unified-threat-header">
        <div>
          <h3>Unified Logs & AI Threat Analysis</h3>
          <p className="muted">
            Device, network, security, sensor, and operations events in one SOC pipeline.
          </p>
        </div>
        <span className="status-pill live">live</span>
      </header>

      <div className="log-filter-bar">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search ID, IP, area code, message"
        />

        <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
          <option value="all">All types</option>
          <option value="device">Device</option>
          <option value="network">Network</option>
          <option value="security">Security</option>
          <option value="sensor">Sensor</option>
          <option value="operations">Operations</option>
          <option value="threat">Threat</option>
        </select>

        <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
          <option value="all">All severity</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </select>

        <select value={regionFilter} onChange={(event) => setRegionFilter(event.target.value)}>
          <option value="all">All regions</option>
          {regions.map((region) => (
            <option key={region} value={region}>{region}</option>
          ))}
        </select>

        {selectedIncident && (
          <button type="button" onClick={() => setSelectedIncident("")}>
            Clear incident
          </button>
        )}
      </div>

      <div className="threat-intel-layout">
        <section className="ai-threat-cases" aria-label="AI threat cases">
          {threats.map((threat) => (
            <button
              key={threat.id}
              type="button"
              className={`ai-threat-card ${selectedIncident === threat.id ? "active" : ""} ${threat.severity}`}
              onClick={() => selectThreat(threat)}
            >
              <span className="threat-score">{threat.threat_score}</span>
              <strong>{threat.label}</strong>
              <small>{threat.devices.join(", ")} · {threat.region} · {threat.time_window}</small>
              <p>{threat.explanation}</p>
              <em>{threat.suggested_action}</em>
            </button>
          ))}
        </section>

        <section className="live-log-stream" aria-label="Live log stream">
          {filteredLogs.map((log) => (
            <article className={`log-event-card ${log.severity}`} key={log.id}>
              <div className="log-event-meta">
                <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                <strong>{log.type}</strong>
                <b>{log.severity}</b>
              </div>
              <p>{log.message}</p>
              <small>
                {log.device_id} · {log.country}/{log.region} · area {log.area_code} · {log.ip}
              </small>
            </article>
          ))}
        </section>
      </div>
    </article>
  );
}
