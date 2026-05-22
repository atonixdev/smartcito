/**
 * ============================================================================
 * File: webapp/src/components/ThreeDashboardPanel.tsx
 * Purpose:
 *   Three.js 3D dashboard scene for SmartCito IoT, GPS, cameras, Raspberry Pi
 *   edge nodes, and AI threat waves.
 * ============================================================================
 */

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import type { SceneOverview } from "@/api/scene";

const canInitializeThree = import.meta.env.MODE !== "test";

const layerLabels = [
  ["iot-devices", "IoT"],
  ["gps-paths", "GPS paths"],
  ["camera-overlays", "Cameras"],
  ["threat-waves", "Threat waves"],
] as const;

export default function ThreeDashboardPanel({ scene }: { scene: SceneOverview }) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [enabledLayers, setEnabledLayers] = useState(() => new Set(scene.layers));

  const visibleDevices = useMemo(
    () => scene.devices.filter((device) => device.trust_score > 80),
    [scene.devices],
  );

  useEffect(() => {
    setEnabledLayers(new Set(scene.layers));
  }, [scene]);

  useEffect(() => {
    if (!canInitializeThree || !mountRef.current) {
      return;
    }

    const mountElement = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(mountElement.clientWidth, mountElement.clientHeight);
    mountElement.appendChild(renderer.domElement);

    const threeScene = new THREE.Scene();
    threeScene.background = new THREE.Color("#07111b");
    threeScene.fog = new THREE.Fog("#07111b", 16, 42);

    const camera = new THREE.PerspectiveCamera(48, mountElement.clientWidth / mountElement.clientHeight, 0.1, 100);
    camera.position.set(7, 8, 12);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0);

    threeScene.add(new THREE.HemisphereLight("#edf6f8", "#08141f", 2.6));
    const keyLight = new THREE.DirectionalLight("#ffffff", 2.1);
    keyLight.position.set(8, 10, 6);
    threeScene.add(keyLight);

    const baseGroup = new THREE.Group();
    const deviceGroup = new THREE.Group();
    const pathGroup = new THREE.Group();
    const threatGroup = new THREE.Group();
    threeScene.add(baseGroup, deviceGroup, pathGroup, threatGroup);

    const grid = new THREE.GridHelper(24, 24, "#57c7d4", "#1b4050");
    grid.position.y = 0;
    baseGroup.add(grid);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(24, 24),
      new THREE.MeshStandardMaterial({ color: "#0c2431", roughness: 0.9, metalness: 0.05 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    baseGroup.add(ground);

    for (let buildingIndex = 0; buildingIndex < 18; buildingIndex += 1) {
      const height = 0.35 + ((buildingIndex % 5) * 0.22);
      const building = new THREE.Mesh(
        new THREE.BoxGeometry(0.8, height, 0.8),
        new THREE.MeshStandardMaterial({ color: "#14384a", roughness: 0.82 }),
      );
      building.position.set((buildingIndex % 6) * 3.2 - 8, height / 2, Math.floor(buildingIndex / 6) * 3.4 - 4.5);
      baseGroup.add(building);
    }

    visibleDevices.forEach((device) => {
      const markerGeometry = device.device_type === "camera" ? new THREE.ConeGeometry(0.34, 0.9, 4) : new THREE.SphereGeometry(0.36, 24, 16);
      const marker = new THREE.Mesh(
        markerGeometry,
        new THREE.MeshStandardMaterial({ color: device.status_color, emissive: device.status_color, emissiveIntensity: 0.24 }),
      );
      marker.position.set(device.x, device.y, device.z);
      deviceGroup.add(marker);

      if (enabledLayers.has("gps-paths") && device.gps_path_3d.length > 1) {
        const points = device.gps_path_3d.map(([xPosition, yPosition, zPosition]) => new THREE.Vector3(xPosition, yPosition + 0.04, zPosition));
        pathGroup.add(
          new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(points),
            new THREE.LineBasicMaterial({ color: "#57c7d4" }),
          ),
        );
      }
    });

    scene.threats.forEach((threat) => {
      if (!enabledLayers.has("threat-waves")) {
        return;
      }
      const wave = new THREE.Mesh(
        new THREE.TorusGeometry(threat.radius, 0.025, 12, 96),
        new THREE.MeshBasicMaterial({ color: threat.severity === "high" ? "#f87171" : "#f1c96b", transparent: true, opacity: 0.68 }),
      );
      wave.rotation.x = Math.PI / 2;
      wave.position.set(threat.x, threat.y, threat.z);
      threatGroup.add(wave);
    });

    function handleResize() {
      if (!mountRef.current) {
        return;
      }
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    }
    window.addEventListener("resize", handleResize);

    let animationFrame = 0;
    function animate() {
      animationFrame = requestAnimationFrame(animate);
      const elapsed = performance.now() * 0.001;
      deviceGroup.children.forEach((object, objectIndex) => {
        object.position.y = 0.4 + Math.sin(elapsed * 1.7 + objectIndex) * 0.08;
      });
      threatGroup.children.forEach((object, objectIndex) => {
        const pulse = 1 + Math.sin(elapsed * 2.2 + objectIndex) * 0.08;
        object.scale.setScalar(pulse);
      });
      controls.update();
      renderer.render(threeScene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", handleResize);
      controls.dispose();
      renderer.dispose();
      mountElement.removeChild(renderer.domElement);
    };
  }, [enabledLayers, scene, visibleDevices]);

  function toggleLayer(layer: string) {
    setEnabledLayers((currentLayers) => {
      const nextLayers = new Set(currentLayers);
      if (nextLayers.has(layer)) {
        nextLayers.delete(layer);
      } else {
        nextLayers.add(layer);
      }
      return nextLayers;
    });
  }

  return (
    <section className="three-dashboard-stage" aria-label="SmartCito 3D control plane">
      <div className="three-stage-copy">
        <h3>SmartCito 3D Dashboard</h3>
      </div>

      <div className="three-stage-layout">
        <div ref={mountRef} className="three-stage-canvas" data-testid="three-dashboard-canvas" />
        <aside className="three-stage-controls">
          <div className="three-layer-controls">
            {layerLabels.map(([layer, label]) => (
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
    </section>
  );
}