/**
 * ============================================================================
 * File: webapp/src/components/SmartMapPanel.tsx
 * Purpose:
 *   Leaflet-powered dashboard map for IoT -> GPS -> Map -> Camera flow.
 * ============================================================================
 */

import { useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { SmartMapDevice } from "@/api/map";

const mapCenter: [number, number] = [-25.7479, 28.2293];
const canInitializeLeaflet = import.meta.env.MODE !== "test";

function layerAllows(layer: string, enabledLayers: Set<string>) {
  return enabledLayers.has(layer);
}

export default function SmartMapPanel({ devices }: { devices: SmartMapDevice[] }) {
  const mapRef = useRef<L.Map | null>(null);
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const [enabledLayers, setEnabledLayers] = useState(
    () => new Set(["devices", "cameras", "paths", "heatmap"]),
  );

  const verifiedDevices = useMemo(
    () => devices.filter((device) => device.trust_score > 80),
    [devices],
  );

  useEffect(() => {
    if (!canInitializeLeaflet) {
      return;
    }

    if (!mapElementRef.current || mapRef.current) {
      return;
    }

    mapRef.current = L.map(mapElementRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView(mapCenter, 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(mapRef.current);

    layerGroupRef.current = L.layerGroup().addTo(mapRef.current);
  }, []);

  useEffect(() => {
    if (!canInitializeLeaflet) {
      return;
    }

    const group = layerGroupRef.current;
    if (!group) {
      return;
    }

    group.clearLayers();

    verifiedDevices.forEach((device) => {
      if (layerAllows("paths", enabledLayers) && device.gps_path.length > 1) {
        L.polyline(device.gps_path, {
          color: "#57c7d4",
          weight: 3,
          opacity: 0.75,
        }).addTo(group);
      }

      if (layerAllows("heatmap", enabledLayers)) {
        L.circle([device.latitude, device.longitude], {
          radius: 420 + (device.sensor_value ?? 0.5) * 460,
          color: "#f1c96b",
          fillColor: "#f1c96b",
          fillOpacity: 0.14,
          weight: 1,
        }).addTo(group);
      }

      if (!layerAllows("devices", enabledLayers)) {
        return;
      }

      const hasCamera = Boolean(device.camera_feed_url);
      if (device.device_type === "camera" && !layerAllows("cameras", enabledLayers)) {
        return;
      }

      const icon = L.divIcon({
        className: "smart-map-pin",
        html: `<span>${device.device_type.toUpperCase()}</span>`,
        iconSize: [44, 44],
        iconAnchor: [22, 22],
      });

      const cameraMarkup = hasCamera
        ? `<a href="${device.camera_feed_url}" target="_blank" rel="noreferrer">Open camera feed</a>`
        : "<span>No camera feed linked</span>";

      L.marker([device.latitude, device.longitude], { icon })
        .bindPopup(
          `<strong>${device.name}</strong><br/>` +
            `Trust score: ${device.trust_score}<br/>` +
            `Sensor: ${device.sensor_type}<br/>` +
            cameraMarkup,
        )
        .addTo(group);
    });

    if (verifiedDevices.length > 0 && mapRef.current) {
      const bounds = L.latLngBounds(
        verifiedDevices.map((device) => [device.latitude, device.longitude]),
      );
      mapRef.current.fitBounds(bounds.pad(0.25), { maxZoom: 13 });
    }
  }, [enabledLayers, verifiedDevices]);

  function toggleLayer(layer: string) {
    setEnabledLayers((current) => {
      const next = new Set(current);
      if (next.has(layer)) {
        next.delete(layer);
      } else {
        next.add(layer);
      }
      return next;
    });
  }

  return (
    <article className="panel panel-wide smart-map-panel">
      <header className="panel-header map-panel-header">
        <h3>SmartCito Map</h3>
      </header>

      <div className="map-layout">
        <div ref={mapElementRef} className="smart-map" aria-label="SmartCito verified device map" />
        <aside className="map-sidebar">
          <div className="map-layer-controls" aria-label="Map layer controls">
            {[
              ["devices", "Device pins"],
              ["cameras", "Camera overlays"],
              ["paths", "GPS paths"],
              ["heatmap", "Sensor heatmap"],
            ].map(([layer, label]) => (
              <label key={layer}>
                <input
                  type="checkbox"
                  checked={enabledLayers.has(layer)}
                  onChange={() => toggleLayer(layer)}
                />
                {label}
              </label>
            ))}
          </div>
        </aside>
      </div>
    </article>
  );
}