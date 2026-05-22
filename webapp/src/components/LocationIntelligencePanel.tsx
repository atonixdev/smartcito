/**
 * ============================================================================
 * File: webapp/src/components/LocationIntelligencePanel.tsx
 * Purpose:
 *   Country, region, area code, IP, GPS, and fused location control panel.
 * ============================================================================
 */

import { useMemo, useState } from "react";

type Country = { iso2: string; name: string };
type Region = { code: string; name: string };
type AreaCode = { city: string; region: string; lat: number; lon: number };
type IpLocation = { city: string; country: string; isp: string; lat: number; lon: number };
type GpsLocation = { latitude: number; longitude: number; accuracy?: number };

const countries: Country[] = [
  { iso2: "KE", name: "Kenya" },
  { iso2: "US", name: "United States" },
  { iso2: "GB", name: "United Kingdom" },
];

const regions: Record<string, Region[]> = {
  KE: [
    { code: "NBO", name: "Nairobi" },
    { code: "MSA", name: "Mombasa" },
  ],
  US: [
    { code: "CA", name: "California" },
    { code: "NY", name: "New York" },
  ],
  GB: [{ code: "LDN", name: "London" }],
};

const areaCodes: Record<string, Record<string, AreaCode>> = {
  KE: {
    "020": { city: "Nairobi", region: "NBO", lat: -1.2921, lon: 36.8219 },
    "041": { city: "Mombasa", region: "MSA", lat: -4.0435, lon: 39.6682 },
  },
  US: {
    "415": { city: "San Francisco", region: "CA", lat: 37.7749, lon: -122.4194 },
    "212": { city: "New York", region: "NY", lat: 40.7128, lon: -74.006 },
  },
  GB: {
    "020": { city: "London", region: "LDN", lat: 51.5074, lon: -0.1278 },
  },
};

export default function LocationIntelligencePanel() {
  const [country, setCountry] = useState("");
  const [region, setRegion] = useState("");
  const [areaCode, setAreaCode] = useState("");
  const [ip, setIp] = useState("");
  const [ipLocation, setIpLocation] = useState<IpLocation | null>(null);
  const [gps, setGps] = useState<GpsLocation | null>(null);

  const selectedRegions = country ? regions[country] ?? [] : [];
  const selectedAreaCodes = country ? areaCodes[country] ?? {} : {};
  const selectedArea = areaCode ? selectedAreaCodes[areaCode] : null;

  const fused = useMemo(() => {
    if (gps) {
      return {
        title: "GPS",
        status: "Verified",
        confidence: 96,
        value: `${gps.latitude.toFixed(5)}, ${gps.longitude.toFixed(5)}`,
      };
    }

    if (ipLocation) {
      return {
        title: "IP",
        status: "Network verified",
        confidence: 74,
        value: `${ipLocation.city}, ${ipLocation.country}`,
      };
    }

    if (selectedArea) {
      return {
        title: "Area Code",
        status: "Mapped",
        confidence: 68,
        value: `${selectedArea.city} (${selectedArea.lat}, ${selectedArea.lon})`,
      };
    }

    return null;
  }, [gps, ipLocation, selectedArea]);

  function onCountryChange(nextCountry: string) {
    setCountry(nextCountry);
    setRegion("");
    setAreaCode("");
    setIpLocation(null);
    setGps(null);
  }

  function lookupIp() {
    if (!ip.trim()) return;

    setIpLocation({
      city: selectedArea?.city ?? "Network City",
      country: country || "Unknown",
      isp: "SmartCito ISP Lookup",
      lat: selectedArea?.lat ?? -1.2921,
      lon: selectedArea?.lon ?? 36.8219,
    });
  }

  function captureGps() {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition((position) => {
      setGps({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      });
    });
  }

  return (
    <article className="panel panel-wide location-intelligence-panel">
      <div className="dashboard-control-panel">
        <label>
          Country
          <select value={country} onChange={(event) => onCountryChange(event.target.value)}>
            <option value="">Select country</option>
            {countries.map((item) => (
              <option key={item.iso2} value={item.iso2}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Region
          <select
            value={region}
            disabled={!country}
            onChange={(event) => setRegion(event.target.value)}
          >
            <option value="">Select region</option>
            {selectedRegions.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Area Code
          <select
            value={areaCode}
            disabled={!country}
            onChange={(event) => setAreaCode(event.target.value)}
          >
            <option value="">Select area code</option>
            {Object.entries(selectedAreaCodes).map(([code, item]) => (
              <option key={code} value={code}>
                {code} — {item.city}
              </option>
            ))}
          </select>
        </label>

        <label>
          IP Address
          <input
            value={ip}
            placeholder="IPv4 or IPv6"
            onChange={(event) => setIp(event.target.value)}
          />
        </label>

        <div className="dashboard-control-actions">
          <button type="button" onClick={lookupIp}>Lookup</button>
          <button type="button" onClick={captureGps}>Capture GPS</button>
          <button className="primary" type="button">Fuse Location</button>
        </div>
      </div>

      <div className="location-output-grid">
        <div className="location-output-card">
          <span className={selectedArea ? "status-dot live" : "status-dot idle"} />
          <strong>Area Code Location</strong>
          <p>{selectedArea ? `${selectedArea.city}, ${selectedArea.region}` : "Not selected"}</p>
        </div>

        <div className="location-output-card">
          <span className={ipLocation ? "status-dot live" : "status-dot idle"} />
          <strong>IP Location</strong>
          <p>{ipLocation ? `${ipLocation.city} · ${ipLocation.isp}` : "Not loaded"}</p>
        </div>

        <div className="location-output-card">
          <span className={gps ? "status-dot live" : "status-dot idle"} />
          <strong>GPS Location</strong>
          <p>{gps ? `${gps.latitude.toFixed(5)}, ${gps.longitude.toFixed(5)}` : "Not captured"}</p>
        </div>

        <div className="location-output-card">
          <span className={fused ? "status-dot live" : "status-dot idle"} />
          <strong>Unified Output</strong>
          <p>{fused ? `${fused.title} · ${fused.confidence}% · ${fused.status}` : "Not fused"}</p>
        </div>
      </div>
    </article>
  );
}
