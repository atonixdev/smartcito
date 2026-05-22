import { useEffect, useMemo, useState } from "react";
import {
  fuseLocation,
  getAreaCodes,
  getCountries,
  getRegions,
  lookupIp,
  logLocationEvent,
  Country,
  FusedLocation,
  IpLocation,
  Region,
} from "@/api/locationIntelligence";
import "./LocationIntelligencePanel.css";

export default function LocationIntelligencePanel() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [areaCodes, setAreaCodes] = useState<Record<string, { city: string; region: string; lat: number; lon: number }>>({});
  const [country, setCountry] = useState("");
  const [region, setRegion] = useState("");
  const [areaCode, setAreaCode] = useState("");
  const [ip, setIp] = useState("");
  const [ipLocation, setIpLocation] = useState<IpLocation | null>(null);
  const [gps, setGps] = useState<{ latitude: number; longitude: number; accuracy?: number; timestamp?: string } | null>(null);
  const [fused, setFused] = useState<FusedLocation | null>(null);
  const [sources, setSources] = useState<Array<{ source: string; confidence: number }>>([]);
  const [status, setStatus] = useState("Ready");

  useEffect(() => {
    getCountries().then(setCountries).catch(() => setStatus("Location API unavailable"));
  }, []);

  useEffect(() => {
    if (!country) return;
    setRegion("");
    setAreaCode("");
    getRegions(country).then(setRegions);
    getAreaCodes(country).then(setAreaCodes);
  }, [country]);

  const selectedArea = useMemo(() => areaCodes[areaCode] ?? null, [areaCodes, areaCode]);

  async function captureGps() {
    if (!navigator.geolocation) {
      setStatus("Browser GPS unavailable");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGps({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: new Date(pos.timestamp).toISOString(),
        });
        setStatus("GPS captured");
      },
      () => setStatus("GPS permission denied"),
    );
  }

  async function runIpLookup() {
    if (!ip) return;
    const result = await lookupIp(ip);
    setIpLocation(result);
    setStatus("IP geolocation loaded");
  }

  async function runFusion() {
    const result = await fuseLocation({
      gps,
      ip: ipLocation,
      userSelected: { country, region, areaCode },
    });

    setFused(result.fused);
    setSources(result.sources.map((s) => ({ source: s.source, confidence: s.confidence })));

    if (result.fused) {
      await logLocationEvent({
        deviceId: "dashboard-operator",
        authenticated: true,
        fused: result.fused,
        sources: result.sources,
      }).catch(() => undefined);
    }

    setStatus("Unified location fused and ATP logged");
  }

  return (
    <article className="panel panel-wide location-intelligence-panel">
      <div className="location-form-grid">
        <label>
          Country
          <select value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">Select country</option>
            {countries.map((c) => (
              <option key={c.iso2} value={c.iso2}>
                {c.name} ({c.iso2})
              </option>
            ))}
          </select>
        </label>

        <label>
          Region
          <select value={region} onChange={(e) => setRegion(e.target.value)} disabled={!country}>
            <option value="">Select region</option>
            {regions.map((r) => (
              <option key={r.code} value={r.code}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Area Code
          <select value={areaCode} onChange={(e) => setAreaCode(e.target.value)} disabled={!country}>
            <option value="">Select area code</option>
            {Object.entries(areaCodes).map(([code, value]) => (
              <option key={code} value={code}>
                {code} — {value.city}
              </option>
            ))}
          </select>
        </label>

        <label>
          IP Address
          <div className="location-inline">
            <input value={ip} onChange={(e) => setIp(e.target.value)} placeholder="IPv4 or IPv6" />
            <button onClick={runIpLookup}>Lookup</button>
          </div>
        </label>
      </div>

      <div className="location-actions">
        <button onClick={captureGps}>Capture GPS</button>
        <button className="primary" onClick={runFusion}>Fuse Location</button>
      </div>

      <div className="location-results">
        <div>
          <strong>Area Code Location</strong>
          <p>{selectedArea ? `${selectedArea.city}, ${selectedArea.region} (${selectedArea.lat}, ${selectedArea.lon})` : "Not selected"}</p>
        </div>
        <div>
          <strong>IP Location</strong>
          <p>{ipLocation ? `${ipLocation.city}, ${ipLocation.country} · ${ipLocation.isp ?? "ISP unknown"}` : "Not loaded"}</p>
        </div>
        <div>
          <strong>GPS Location</strong>
          <p>{gps ? `${gps.latitude}, ${gps.longitude} ±${gps.accuracy ?? "?"}m` : "Not captured"}</p>
        </div>
        <div>
          <strong>Unified Output</strong>
          <p>{fused ? `${fused.source.toUpperCase()} · ${(fused.confidence * 100).toFixed(0)}% · ${fused.latitude}, ${fused.longitude}` : "Not fused"}</p>
        </div>
      </div>

      <div className="confidence-list">
        {sources.map((source) => (
          <span key={source.source}>
            {source.source}: {(source.confidence * 100).toFixed(0)}%
          </span>
        ))}
      </div>
    </article>
  );
}
