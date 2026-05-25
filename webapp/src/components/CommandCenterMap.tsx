import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import * as THREE from "three";
import "leaflet/dist/leaflet.css";

import type { SceneOverview } from "@/api/scene";

type AssetKind = "drone" | "robot" | "camera" | "sensor" | "deterrent";
type MapMode = "2d" | "3d" | "street";

interface AssetItem {
  id: string;
  kind: AssetKind;
  label: string;
  status: string;
  subtitle: string;
  latitude: number;
  longitude: number;
}

interface ThreatAlert {
  alert_id: string;
  title: string;
  threat_level: string;
  source_ids: string[];
}

interface ZoneOverlay {
  id: string;
  label: string;
  kind: "critical" | "restricted" | "geofence";
  top: number;
  left: number;
  width: number;
  height: number;
}

interface MapPoint {
  latitude: number;
  longitude: number;
}

export interface CameraCorridor {
  id: string;
  label: string;
  polygon: Array<[number, number]>;
}

const tileProviders: Record<Exclude<MapMode, "3d">, { url: string; attribution: string }> = {
  "2d": {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  street: {
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
};

function assetColor(kind: AssetKind) {
  if (kind === "drone") {
    return "#8fe5db";
  }
  if (kind === "robot") {
    return "#8fb6ff";
  }
  if (kind === "camera") {
    return "#ffd776";
  }
  if (kind === "deterrent") {
    return "#ffaf8d";
  }
  return "#a7b9ff";
}

export default function CommandCenterMap({
  assets,
  threatAlerts,
  zones,
  selectedAssetId,
  drawPoints,
  onMapClick,
  onSelectAsset,
  mode = "2d",
  sceneOverview,
  cameraCorridors = [],
}: {
  assets: AssetItem[];
  threatAlerts: ThreatAlert[];
  zones: ZoneOverlay[];
  selectedAssetId: string | null;
  drawPoints: MapPoint[];
  onMapClick: (point: MapPoint) => void;
  onSelectAsset: (kind: AssetKind, id: string) => void;
  mode?: MapMode;
  sceneOverview?: SceneOverview | null;
  cameraCorridors?: CameraCorridor[];
}) {
  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const sceneElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const overlaysRef = useRef<L.LayerGroup | null>(null);

  const bounds = useMemo(() => assets.filter((asset) => Number.isFinite(asset.latitude) && Number.isFinite(asset.longitude)), [assets]);

  function toLatLng(topPercent: number, leftPercent: number) {
    const north = -25.742;
    const south = -25.7525;
    const west = 28.226;
    const east = 28.2485;

    return {
      latitude: north - (topPercent / 100) * (north - south),
      longitude: west + (leftPercent / 100) * (east - west),
    };
  }

  useEffect(() => {
    if (mode === "3d" || import.meta.env.MODE === "test" || !mapElementRef.current) {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        tileLayerRef.current = null;
        layerGroupRef.current = null;
        overlaysRef.current = null;
      }
      return;
    }

    if (!mapRef.current) {
      mapRef.current = L.map(mapElementRef.current, {
        zoomControl: true,
        attributionControl: true,
      }).setView([-25.7479, 28.2293], 13);

      layerGroupRef.current = L.layerGroup().addTo(mapRef.current);
      overlaysRef.current = L.layerGroup().addTo(mapRef.current);
      mapRef.current.on("click", (event: L.LeafletMouseEvent) => {
        onMapClick({ latitude: event.latlng.lat, longitude: event.latlng.lng });
      });
    }

    tileLayerRef.current?.remove();
    const provider = tileProviders[mode];
    tileLayerRef.current = L.tileLayer(provider.url, {
      maxZoom: 19,
      attribution: provider.attribution,
    }).addTo(mapRef.current);
  }, [mode, onMapClick]);

  useEffect(() => {
    if (mode === "3d" || !layerGroupRef.current || !mapRef.current || !overlaysRef.current) {
      return;
    }

    const group = layerGroupRef.current;
    const overlays = overlaysRef.current;
    group.clearLayers();
    overlays.clearLayers();

    zones.forEach((zone) => {
      const topLeft = toLatLng(zone.top, zone.left);
      const bottomRight = toLatLng(zone.top + zone.height, zone.left + zone.width);
      L.rectangle(
        [
          [topLeft.latitude, topLeft.longitude],
          [bottomRight.latitude, bottomRight.longitude],
        ],
        {
          color: zone.kind === "critical" ? "#f87171" : zone.kind === "restricted" ? "#f1c96b" : "#57c7d4",
          weight: 1,
          fillOpacity: 0.08,
        },
      )
        .bindTooltip(zone.label)
        .addTo(overlays);
    });

    cameraCorridors.forEach((corridor) => {
      L.polygon(corridor.polygon, {
        color: mode === "street" ? "#f1c96b" : "#ffd776",
        weight: mode === "street" ? 2 : 1,
        fillOpacity: mode === "street" ? 0.22 : 0.14,
      })
        .bindTooltip(corridor.label)
        .addTo(overlays);
    });

    assets.forEach((asset) => {
      const marker = L.circleMarker([asset.latitude, asset.longitude], {
        radius: selectedAssetId === asset.id ? 12 : 9,
        color: selectedAssetId === asset.id ? "#ffe08b" : "#041219",
        weight: 2,
        fillColor: assetColor(asset.kind),
        fillOpacity: 0.95,
      });

      marker.bindPopup(`<strong>${asset.label}</strong><br/>${asset.subtitle}<br/>Status: ${asset.status}`);
      marker.on("click", () => onSelectAsset(asset.kind, asset.id));
      marker.addTo(group);
    });

    threatAlerts.forEach((alert) => {
      const source = assets.find((asset) => alert.source_ids.includes(asset.id));
      if (!source) {
        return;
      }

      L.circle([source.latitude, source.longitude], {
        radius: alert.threat_level === "critical" ? 340 : 240,
        color: alert.threat_level === "critical" ? "#f87171" : "#f1c96b",
        weight: 2,
        fillOpacity: 0.12,
      }).addTo(group);
    });

    if (drawPoints.length > 1) {
      L.polyline(drawPoints.map((point) => [point.latitude, point.longitude]), {
        color: "#f1c96b",
        weight: 3,
        dashArray: "8 6",
      }).addTo(group);
    }

    if (bounds.length > 0) {
      mapRef.current.fitBounds(L.latLngBounds(bounds.map((asset) => [asset.latitude, asset.longitude])), {
        maxZoom: 15,
        padding: [36, 36],
      });
    }
  }, [assets, bounds, cameraCorridors, drawPoints, mode, onSelectAsset, selectedAssetId, threatAlerts, zones]);

  useEffect(() => {
    if (mode !== "3d" || import.meta.env.MODE === "test" || !sceneElementRef.current) {
      return;
    }

    const mount = sceneElementRef.current;
    const width = mount.clientWidth || 960;
    const height = mount.clientHeight || 560;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x071520);

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(0, 56, 90);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0x608090, 0.8));
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.1);
    directionalLight.position.set(40, 80, 40);
    scene.add(directionalLight);
    scene.add(new THREE.GridHelper(180, 24, 0x29445a, 0x142534));

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(180, 180),
      new THREE.MeshStandardMaterial({ color: 0x0b1d2b, roughness: 0.9 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    scene.add(ground);

    const devices = sceneOverview?.devices ?? [];
    devices.forEach((device) => {
      const marker = new THREE.Mesh(
        new THREE.BoxGeometry(device.device_type === "camera" ? 2.2 : 1.8, device.device_type === "camera" ? 4.4 : 3.2, 1.8),
        new THREE.MeshStandardMaterial({ color: new THREE.Color(device.status_color) }),
      );
      marker.position.set(device.x, device.y + 1.2, device.z);
      scene.add(marker);

      const pathPoints = device.gps_path_3d.map(([xPosition, yPosition, zPosition]) => new THREE.Vector3(xPosition, yPosition + 0.08, zPosition));
      if (pathPoints.length > 1) {
        const pathGeometry = new THREE.BufferGeometry().setFromPoints(pathPoints);
        const pathMaterial = new THREE.LineBasicMaterial({ color: device.device_type === "camera" ? 0xffd776 : 0x57c7d4 });
        scene.add(new THREE.Line(pathGeometry, pathMaterial));
      }

      if (device.device_type === "camera") {
        const cone = new THREE.Mesh(
          new THREE.ConeGeometry(4.2, 9.5, 16, 1, true),
          new THREE.MeshBasicMaterial({ color: 0xffd776, transparent: true, opacity: 0.18, side: THREE.DoubleSide }),
        );
        cone.position.set(device.x + 2.6, 4.6, device.z - 1.6);
        cone.rotation.z = Math.PI / 2;
        scene.add(cone);
      }
    });

    (sceneOverview?.threats ?? []).forEach((threat) => {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(Math.max(threat.radius * 0.8, 1.4), Math.max(threat.radius, 2.2), 32),
        new THREE.MeshBasicMaterial({
          color: threat.severity === "high" ? 0xf1c96b : 0xf87171,
          transparent: true,
          opacity: 0.24,
          side: THREE.DoubleSide,
        }),
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(threat.x, 0.08, threat.z);
      scene.add(ring);
    });

    let frame = 0;
    const clock = new THREE.Clock();

    function animate() {
      const elapsed = clock.getElapsedTime();
      camera.position.x = Math.sin(elapsed * 0.18) * 88;
      camera.position.z = Math.cos(elapsed * 0.18) * 88;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    }

    animate();

    function handleResize() {
      const nextWidth = mount.clientWidth || 960;
      const nextHeight = mount.clientHeight || 560;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    }

    window.addEventListener("resize", handleResize);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [mode, sceneOverview]);

  if (mode === "3d") {
    return <div ref={sceneElementRef} className="command-three-map" aria-label="SmartCito city command map" />;
  }

  return <div ref={mapElementRef} className="command-leaflet-map" aria-label="SmartCito city command map" />;
}