import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { smartCitoDevices3D, smartCitoThreats3D } from '../data/smartcito3dDevices';
import './SmartCito3DDashboard.css';

const typeColors = {
  edge: 0x06d6a0,
  camera: 0xef476f,
  gps: 0xffd166,
  iot: 0x4cc9f0
};

const trustColors = {
  verified: '#06d6a0',
  unverified: '#ffd166',
  blocked: '#ef476f'
};

export default function SmartCito3DDashboard() {
  const mountRef = useRef(null);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [layers, setLayers] = useState({
    iot: true,
    gps: true,
    camera: true,
    edge: true,
    threats: true
  });

  const visibleDevices = useMemo(
    () => smartCitoDevices3D.filter((device) => layers[device.type]),
    [layers]
  );

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const width = mount.clientWidth;
    const height = mount.clientHeight || 620;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x08111f);
    scene.fog = new THREE.Fog(0x08111f, 80, 220);

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(0, 80, 120);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0x91a7d8, 0.55));

    const sun = new THREE.DirectionalLight(0xffffff, 0.9);
    sun.position.set(60, 100, 60);
    scene.add(sun);

    const cityGroup = new THREE.Group();
    scene.add(cityGroup);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(180, 180),
      new THREE.MeshStandardMaterial({
        color: 0x111b2e,
        roughness: 0.9,
        metalness: 0.1
      })
    );
    ground.rotation.x = -Math.PI / 2;
    cityGroup.add(ground);

    const grid = new THREE.GridHelper(180, 36, 0x4cc9f0, 0x263956);
    grid.position.y = 0.05;
    cityGroup.add(grid);

    for (let i = 0; i < 42; i += 1) {
      const building = new THREE.Mesh(
        new THREE.BoxGeometry(4 + Math.random() * 7, 6 + Math.random() * 34, 4 + Math.random() * 7),
        new THREE.MeshStandardMaterial({
          color: 0x1c2740,
          emissive: 0x07101f,
          roughness: 0.7
        })
      );

      building.position.set(
        -75 + Math.random() * 150,
        building.geometry.parameters.height / 2,
        -75 + Math.random() * 150
      );

      cityGroup.add(building);
    }

    const clickable = [];
    const animated = [];

    visibleDevices.forEach((device) => {
      if (device.status === 'blocked') return;

      const color = typeColors[device.type] || 0xffffff;

      const pinGroup = new THREE.Group();
      pinGroup.position.set(device.x, 0, device.z);
      pinGroup.userData = { device };

      const base = new THREE.Mesh(
        new THREE.CylinderGeometry(1.4, 1.4, 1, 24),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.2 })
      );
      base.position.y = 0.5;
      pinGroup.add(base);

      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(2.2, 24, 24),
        new THREE.MeshStandardMaterial({
          color,
          emissive: color,
          emissiveIntensity: 0.65
        })
      );
      marker.position.y = 7;
      pinGroup.add(marker);

      const beam = new THREE.Mesh(
        new THREE.CylinderGeometry(0.25, 0.25, 12, 16),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.35
        })
      );
      beam.position.y = 6;
      pinGroup.add(beam);

      const ring = new THREE.Mesh(
        new THREE.RingGeometry(4, 5.2, 48),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.45,
          side: THREE.DoubleSide
        })
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.y = 0.15;
      pinGroup.add(ring);

      scene.add(pinGroup);
      clickable.push(marker);
      animated.push({ ring, marker, phase: Math.random() * Math.PI * 2 });

      const pathCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(device.x, 1, device.z),
        new THREE.Vector3(device.x * 0.5, 18, device.z * 0.5),
        new THREE.Vector3(0, 12, 0)
      ]);

      const path = new THREE.Mesh(
        new THREE.TubeGeometry(pathCurve, 36, 0.12, 8, false),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.35
        })
      );
      scene.add(path);
    });

    if (layers.threats) {
      smartCitoThreats3D.forEach((threat) => {
        const threatColor = threat.severity === 'high' ? 0xef476f : 0xffd166;

        const wave = new THREE.Mesh(
          new THREE.RingGeometry(3, 3.4, 64),
          new THREE.MeshBasicMaterial({
            color: threatColor,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
          })
        );
        wave.rotation.x = -Math.PI / 2;
        wave.position.set(threat.x, 0.25, threat.z);
        scene.add(wave);
        animated.push({ wave, phase: 0 });
      });
    }

    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(4, 4, 10, 32),
      new THREE.MeshStandardMaterial({
        color: 0x06d6a0,
        emissive: 0x06d6a0,
        emissiveIntensity: 0.45
      })
    );
    hub.position.y = 5;
    scene.add(hub);

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    const onPointerDown = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(clickable, false);

      if (hits.length > 0) {
        setSelectedDevice(hits[0].object.parent.userData.device);
      }
    };

    renderer.domElement.addEventListener('pointerdown', onPointerDown);

    let frameId;
    const clock = new THREE.Clock();

    const animate = () => {
      const elapsed = clock.getElapsedTime();

      hub.rotation.y += 0.01;

      animated.forEach((item) => {
        if (item.marker) {
          item.marker.position.y = 7 + Math.sin(elapsed * 2 + item.phase) * 0.5;
        }

        if (item.ring) {
          const scale = 1 + Math.sin(elapsed * 2 + item.phase) * 0.12;
          item.ring.scale.set(scale, scale, scale);
        }

        if (item.wave) {
          const scale = 1 + ((elapsed + item.phase) % 2.4);
          item.wave.scale.set(scale, scale, scale);
          item.wave.material.opacity = Math.max(0, 0.8 - scale * 0.25);
        }
      });

      camera.position.x = Math.sin(elapsed * 0.08) * 120;
      camera.position.z = Math.cos(elapsed * 0.08) * 120;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };

    animate();

    const onResize = () => {
      const nextWidth = mount.clientWidth;
      const nextHeight = mount.clientHeight || 620;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    };

    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', onResize);
      renderer.domElement.removeEventListener('pointerdown', onPointerDown);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [visibleDevices, layers.threats]);

  const toggleLayer = (key) => {
    setLayers((current) => ({ ...current, [key]: !current[key] }));
  };

  return (
    <section className="smartcito-3d-dashboard">
      <aside className="smartcito-3d-panel">
        <p className="smartcito-eyebrow">SmartCito 3D Control Plane</p>
        <h1>IoT, GPS, Camera, Map, Threats, and Raspberry Pi Edge Nodes</h1>
        <p>
          Devices are displayed only after authorization and ATP trust validation.
          GPS/IP/area-code fused locations are rendered as 3D pins on the city map.
        </p>

        <div className="smartcito-layer-controls">
          {Object.keys(layers).map((key) => (
            <button
              key={key}
              className={layers[key] ? 'active' : ''}
              onClick={() => toggleLayer(key)}
            >
              {key}
            </button>
          ))}
        </div>

        <div className="smartcito-device-list">
          {smartCitoDevices3D.map((device) => (
            <button
              key={device.id}
              className="smartcito-device-card"
              onClick={() => setSelectedDevice(device)}
            >
              <span style={{ background: trustColors[device.status] }} />
              <strong>{device.id}</strong>
              <small>{device.type} · trust {device.trustScore}%</small>
            </button>
          ))}
        </div>
      </aside>

      <div className="smartcito-3d-map-wrap">
        <div ref={mountRef} className="smartcito-3d-map" />

        {selectedDevice && (
          <div className="smartcito-device-popup">
            <button onClick={() => setSelectedDevice(null)}>×</button>
            <h2>{selectedDevice.name}</h2>
            <p><strong>ID:</strong> {selectedDevice.id}</p>
            <p><strong>Type:</strong> {selectedDevice.type}</p>
            <p><strong>Status:</strong> {selectedDevice.status}</p>
            <p><strong>Trust:</strong> {selectedDevice.trustScore}%</p>
            <p><strong>GPS:</strong> {selectedDevice.latitude}, {selectedDevice.longitude}</p>
            <p><strong>Telemetry:</strong> {selectedDevice.telemetry}</p>

            {selectedDevice.type === 'camera' && (
              <div className="smartcito-video-preview">
                <span>LIVE CAMERA OVERLAY</span>
                <small>{selectedDevice.streamUrl}</small>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
