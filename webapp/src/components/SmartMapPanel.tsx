/**
 * ============================================================================
 * File: webapp/src/components/SmartMapPanel.tsx
 * Purpose:
 *   Real WebGL world map using Mapbox GL JS for country zoom, 2D/3D mode,
 *   GPS trails, devices, camera overlays, address labels, terrain, satellite
 *   imagery, and 3D buildings.
 * ============================================================================
 */

import { useEffect, useMemo, useRef, useState } from "react";

import type { SmartMapDevice } from "@/api/map";

const MAPBOX_JS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.8.0/mapbox-gl.js";
const MAPBOX_CSS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.8.0/mapbox-gl.css";

type MapMode = "2d" | "3d";
type FeatureProperties = Record<string, string | number | boolean | null>;

interface FeatureCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: FeatureProperties;
    geometry:
      | { type: "Point"; coordinates: [number, number] }
      | { type: "LineString"; coordinates: Array<[number, number]> }
      | { type: "Polygon"; coordinates: Array<Array<[number, number]>> };
  }>;
}

interface MapboxMouseEvent {
  lngLat: { lng: number; lat: number };
  point: unknown;
}

interface MapboxSource {
  setData?: (data: FeatureCollection) => void;
}

interface MapboxRenderedFeature {
  properties?: Record<string, unknown>;
  geometry?: { type: string; coordinates?: unknown };
}

interface MapboxPopup {
  setLngLat(coordinates: [number, number]): MapboxPopup;
  setHTML(html: string): MapboxPopup;
  addTo(map: MapboxMap): MapboxPopup;
}

interface MapboxMap {
  on(event: string, handler: (event: MapboxMouseEvent) => void): void;
  once(event: string, handler: () => void): void;
  addSource(id: string, source: Record<string, unknown>): void;
  getSource(id: string): MapboxSource | undefined;
  addLayer(layer: Record<string, unknown>, beforeId?: string): void;
  getLayer(id: string): unknown;
  getStyle(): { layers?: Array<{ id: string; type?: string; layout?: Record<string, unknown> }> };
  queryRenderedFeatures(point: unknown, options?: { layers?: string[] }): MapboxRenderedFeature[];
  flyTo(options: Record<string, unknown>): void;
  fitBounds(bounds: [[number, number], [number, number]], options?: Record<string, unknown>): void;
  easeTo(options: Record<string, unknown>): void;
  setLayoutProperty(layerId: string, name: string, value: string): void;
  setTerrain?(terrain?: Record<string, unknown>): void;
  remove(): void;
}

interface MapboxNamespace {
  accessToken: string;
  Map: new (options: Record<string, unknown>) => MapboxMap;
  Popup: new (options?: Record<string, unknown>) => MapboxPopup;
}

declare global {
  interface Window {
    mapboxgl?: MapboxNamespace;
  }
}

function loadMapbox(): Promise<MapboxNamespace> {
  if (window.mapboxgl) return Promise.resolve(window.mapboxgl);

  return new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${MAPBOX_CSS_URL}"]`)) {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = MAPBOX_CSS_URL;
      document.head.appendChild(css);
    }

    const script = document.createElement("script");
    script.src = MAPBOX_JS_URL;
    script.async = true;
    script.onload = () => window.mapboxgl ? resolve(window.mapboxgl) : reject(new Error("Mapbox GL failed to load"));
    script.onerror = () => reject(new Error("Mapbox GL failed to load"));
    document.body.appendChild(script);
  });
}

function escapeHtml(value: unknown) {
  return String(value ?? "Unknown").replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[char] ?? char
  ));
}

function deviceFeatures(devices: SmartMapDevice[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: devices.map((device) => ({
      type: "Feature",
      properties: {
        id: device.id,
        name: device.name,
        type: device.device_type,
        country: device.country ?? null,
        region: device.region ?? null,
        city: device.city ?? null,
        street: device.street ?? null,
        label: device.address_label ?? device.name,
        trust: device.trust_score,
        hasCamera: Boolean(device.camera_feed_url),
        sensor: device.sensor_value ?? 0.4,
      },
      geometry: { type: "Point", coordinates: [device.longitude, device.latitude] },
    })),
  };
}

function trailFeatures(devices: SmartMapDevice[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: devices
      .filter((device) => device.gps_path.length > 1)
      .map((device) => ({
        type: "Feature",
        properties: { id: device.id, name: device.name },
        geometry: {
          type: "LineString",
          coordinates: device.gps_path.map(([lat, lon]) => [lon, lat]),
        },
      })),
  };
}

function zoneFeatures(devices: SmartMapDevice[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: devices
      .filter((device) => (device.sensor_value ?? 0) >= 0.7 || device.device_type === "camera")
      .map((device) => ({
        type: "Feature",
        properties: {
          id: `${device.id}-zone`,
          name: `${device.name} risk zone`,
          severity: (device.sensor_value ?? 0) >= 0.8 ? "high" : "medium",
        },
        geometry: { type: "Point", coordinates: [device.longitude, device.latitude] },
      })),
  };
}

function bboxPolygon(bbox: [number, number, number, number]): FeatureCollection {
  const [minLon, minLat, maxLon, maxLat] = bbox;
  return {
    type: "FeatureCollection",
    features: [{
      type: "Feature",
      properties: {},
      geometry: {
        type: "Polygon",
        coordinates: [[[minLon, minLat], [maxLon, minLat], [maxLon, maxLat], [minLon, maxLat], [minLon, minLat]]],
      },
    }],
  };
}

export default function SmartMapPanel({ devices }: { devices: SmartMapDevice[] }) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapboxMap | null>(null);
  const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

  const [mode, setMode] = useState<MapMode>("3d");
  const [countryLabel, setCountryLabel] = useState("World view");
  const [mapError, setMapError] = useState<string | null>(null);
  const [enabledLayers, setEnabledLayers] = useState(
    () => new Set(["devices", "cameras", "paths", "heatmap", "traffic", "weather", "threats"]),
  );

  const verifiedDevices = useMemo(
    () => devices.filter((device) => device.trust_score > 80),
    [devices],
  );

  useEffect(() => {
    if (!token || !mapContainerRef.current || mapRef.current) return;

    let cancelled = false;

    loadMapbox()
      .then((mapboxgl) => {
        if (cancelled || !mapContainerRef.current) return;

        mapboxgl.accessToken = token;
        const map = new mapboxgl.Map({
          container: mapContainerRef.current,
          style: "mapbox://styles/mapbox/dark-v11",
          center: [18.9, 12.5],
          zoom: 1.35,
          pitch: 60,
          bearing: -18,
          projection: "globe",
          antialias: true,
        });

        mapRef.current = map;

        map.once("load", () => {
          map.addSource("mapbox-dem", {
            type: "raster-dem",
            url: "mapbox://mapbox.mapbox-terrain-dem-v1",
            tileSize: 512,
            maxzoom: 14,
          });
          map.setTerrain?.({ source: "mapbox-dem", exaggeration: 1.25 });

          map.addSource("satellite-overlay", {
            type: "raster",
            url: "mapbox://mapbox.satellite",
            tileSize: 256,
          });
          map.addLayer({
            id: "satellite-overlay",
            type: "raster",
            source: "satellite-overlay",
            paint: { "raster-opacity": 0.18 },
          });

          map.addSource("devices", { type: "geojson", data: deviceFeatures(verifiedDevices) });
          map.addSource("gps-trails", { type: "geojson", data: trailFeatures(verifiedDevices) });
          map.addSource("risk-zones", { type: "geojson", data: zoneFeatures(verifiedDevices) });
          map.addSource("country-highlight", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

          map.addLayer({
            id: "gps-trails",
            type: "line",
            source: "gps-trails",
            paint: { "line-color": "#57c7d4", "line-width": 3, "line-opacity": 0.9 },
          });

          map.addLayer({
            id: "sensor-heatmap",
            type: "heatmap",
            source: "devices",
            paint: {
              "heatmap-weight": ["coalesce", ["get", "sensor"], 0.4],
              "heatmap-intensity": 1.3,
              "heatmap-radius": 38,
              "heatmap-opacity": 0.45,
            },
          });

          map.addLayer({
            id: "risk-zones",
            type: "circle",
            source: "risk-zones",
            paint: {
              "circle-radius": 28,
              "circle-color": ["case", ["==", ["get", "severity"], "high"], "#f87171", "#f1c96b"],
              "circle-opacity": 0.22,
              "circle-stroke-color": "#f87171",
              "circle-stroke-width": 2,
            },
          });

          map.addLayer({
            id: "device-circles",
            type: "circle",
            source: "devices",
            paint: {
              "circle-radius": 8,
              "circle-color": ["case", ["==", ["get", "type"], "camera"], "#f1c96b", "#67d5a5"],
              "circle-stroke-color": "#0b1220",
              "circle-stroke-width": 2,
            },
          });

          map.addLayer({
            id: "camera-badges",
            type: "symbol",
            source: "devices",
            filter: ["==", ["get", "hasCamera"], true],
            layout: {
              "text-field": "CAM",
              "text-size": 11,
              "text-offset": [0, 1.4],
              "text-allow-overlap": true,
            },
            paint: { "text-color": "#f1c96b", "text-halo-color": "#0b1220", "text-halo-width": 1 },
          });

          map.addLayer({
            id: "device-labels",
            type: "symbol",
            source: "devices",
            layout: {
              "text-field": ["get", "label"],
              "text-size": 12,
              "text-offset": [0, -1.4],
              "text-anchor": "bottom",
              "text-allow-overlap": false,
            },
            paint: { "text-color": "#f8fafc", "text-halo-color": "#0b1220", "text-halo-width": 1.2 },
          });

          map.addLayer({
            id: "country-highlight-fill",
            type: "fill",
            source: "country-highlight",
            paint: { "fill-color": "#57c7d4", "fill-opacity": 0.12 },
          });
          map.addLayer({
            id: "country-highlight-line",
            type: "line",
            source: "country-highlight",
            paint: { "line-color": "#57c7d4", "line-width": 2.5 },
          });

          const labelLayer = map.getStyle().layers?.find(
            (layer) => layer.type === "symbol" && layer.layout?.["text-field"],
          )?.id;

          map.addLayer({
            id: "3d-buildings",
            source: "composite",
            "source-layer": "building",
            filter: ["==", "extrude", "true"],
            type: "fill-extrusion",
            minzoom: 14,
            paint: {
              "fill-extrusion-color": "#3c566b",
              "fill-extrusion-height": ["get", "height"],
              "fill-extrusion-base": ["get", "min_height"],
              "fill-extrusion-opacity": 0.72,
            },
          }, labelLayer);
        });

        map.on("click", async (event) => {
          const hit = map.queryRenderedFeatures(event.point, {
            layers: ["device-circles", "device-labels", "camera-badges", "risk-zones"],
          })[0];

          const details = await reverseGeocode(event.lngLat.lng, event.lngLat.lat, token);
          setCountryLabel(details.country ?? "Selected location");

          if (!hit && details.bbox) {
            map.getSource("country-highlight")?.setData?.(bboxPolygon(details.bbox));
            map.fitBounds(
              [[details.bbox[0], details.bbox[1]], [details.bbox[2], details.bbox[3]]],
              { padding: 80, duration: 1600, maxZoom: 7 },
            );
          }

          new mapboxgl.Popup({ closeButton: true })
            .setLngLat([event.lngLat.lng, event.lngLat.lat])
            .setHTML(`
              <strong>${escapeHtml(hit?.properties?.name ?? details.country)}</strong><br />
              Country: ${escapeHtml(details.country ?? hit?.properties?.country)}<br />
              Region: ${escapeHtml(details.region ?? hit?.properties?.region)}<br />
              City: ${escapeHtml(details.city ?? hit?.properties?.city)}<br />
              Street: ${escapeHtml(details.street ?? hit?.properties?.street)}<br />
              Lat/Lon: ${event.lngLat.lat.toFixed(5)}, ${event.lngLat.lng.toFixed(5)}<br />
              ${hit?.properties?.type ? `Device/Risk: ${escapeHtml(hit.properties.type ?? hit.properties.severity)}<br />` : ""}
            `)
            .addTo(map);
        });
      })
      .catch((error: Error) => setMapError(error.message));

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [token, verifiedDevices]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.getSource("devices")?.setData?.(deviceFeatures(verifiedDevices));
    map.getSource("gps-trails")?.setData?.(trailFeatures(verifiedDevices));
    map.getSource("risk-zones")?.setData?.(zoneFeatures(verifiedDevices));
  }, [verifiedDevices]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    [
      ["devices", ["device-circles", "device-labels"]],
      ["cameras", ["camera-badges"]],
      ["paths", ["gps-trails"]],
      ["heatmap", ["sensor-heatmap"]],
      ["threats", ["risk-zones"]],
    ].forEach(([toggle, layers]) => {
      (layers as string[]).forEach((layerId) => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", enabledLayers.has(toggle as string) ? "visible" : "none");
        }
      });
    });
  }, [enabledLayers]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    map.easeTo({
      pitch: mode === "3d" ? 60 : 0,
      bearing: mode === "3d" ? -18 : 0,
      duration: 900,
    });
    map.setTerrain?.(mode === "3d" ? { source: "mapbox-dem", exaggeration: 1.25 } : undefined);

    if (map.getLayer("3d-buildings")) {
      map.setLayoutProperty("3d-buildings", "visibility", mode === "3d" ? "visible" : "none");
    }
  }, [mode]);

  async function reverseGeocode(longitude: number, latitude: number, accessToken: string) {
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json?types=country,region,place,locality,neighborhood,address&access_token=${accessToken}`,
    );
    const payload = await response.json() as {
      features?: Array<{
        place_type?: string[];
        text?: string;
        place_name?: string;
        bbox?: [number, number, number, number];
        context?: Array<{ id: string; text: string }>;
      }>;
    };

    const features = payload.features ?? [];
    const country = features.find((feature) => feature.place_type?.includes("country"));
    const address = features[0];

    return {
      country: country?.text ?? address?.context?.find((item) => item.id.startsWith("country"))?.text,
      region: address?.context?.find((item) => item.id.startsWith("region"))?.text,
      city: address?.context?.find((item) => item.id.startsWith("place"))?.text ?? address?.text,
      street: address?.place_name,
      bbox: country?.bbox,
    };
  }

  function toggleLayer(layer: string) {
    setEnabledLayers((current) => {
      const next = new Set(current);
      next.has(layer) ? next.delete(layer) : next.add(layer);
      return next;
    });
  }

  return (
    <article className="panel panel-wide smart-map-panel">
      <header className="panel-header map-panel-header">
        <div>
          <h3>SmartCito 3D World Map</h3>
          <p className="muted">
            {token
              ? `${countryLabel} · real Mapbox GL map · country zoom · 3D buildings`
              : "Mapbox token required: set VITE_MAPBOX_TOKEN to render the real map"}
          </p>
        </div>
        <button className="btn small" type="button" disabled={!token} onClick={() => setMode(mode === "3d" ? "2d" : "3d")}>
          {mode === "3d" ? "Switch to 2D" : "Switch to 3D"}
        </button>
      </header>

      <div className="map-layout">
        <div ref={mapContainerRef} className="smart-map css-smart-map" aria-label="SmartCito real 3D world map">
          {!token && (
            <div className="empty-state">
              Set <code>VITE_MAPBOX_TOKEN</code> and restart Vite to load the real WebGL world map.
            </div>
          )}
          {mapError && <div className="empty-state">{mapError}</div>}
        </div>

        <aside className="map-sidebar">
          <div className="map-layer-controls" aria-label="Map layer controls">
            {[
              ["devices", "Device markers"],
              ["cameras", "Camera overlays"],
              ["paths", "GPS trails"],
              ["heatmap", "Sensor heatmap"],
              ["threats", "Risk zones"],
              ["weather", "Weather layers"],
              ["traffic", "Traffic layers"],
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

          <div className="map-device-list">
            {verifiedDevices.map((device) => (
              <button
                className="map-device-card"
                key={device.id}
                type="button"
                onClick={() => mapRef.current?.flyTo({
                  center: [device.longitude, device.latitude],
                  zoom: 17,
                  pitch: mode === "3d" ? 65 : 0,
                  duration: 1200,
                })}
              >
                <strong>{device.name}</strong>
                <span>{device.city ?? "Unknown city"} · {device.street ?? "address pending"}</span>
                <span>{device.latitude.toFixed(4)}, {device.longitude.toFixed(4)}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </article>
  );
}