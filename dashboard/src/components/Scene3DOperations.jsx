import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * 3D operational scene:
 * - Ground plane = the city
 * - Glowing pins = devices (IoT/Camera/GPS)
 * - Animated arcs = data flowing to the dashboard hub
 */
export default function Scene3DOperations({ devices = [], threats = [] }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = mount.clientHeight || 480;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1220);

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(0, 60, 90);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mount.appendChild(renderer.domElement);

    // Lights
    scene.add(new THREE.AmbientLight(0x506080, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(50, 80, 50);
    scene.add(dir);

    // Ground (city plane)
    const grid = new THREE.GridHelper(200, 40, 0x4cc9f0, 0x1c2740);
    scene.add(grid);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(200, 200),
      new THREE.MeshStandardMaterial({ color: 0x111b2e, roughness: 0.9 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.05;
    scene.add(ground);

    // Central dashboard hub
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(4, 4, 6, 24),
      new THREE.MeshStandardMaterial({ color: 0x06d6a0, emissive: 0x06d6a0, emissiveIntensity: 0.4 })
    );
    hub.position.y = 3;
    scene.add(hub);

    // Default demo devices if none provided
    const points = devices.length > 0 ? devices : [
      { id: 'iot-1', type: 'iot', status: 'verified', x: -40, z: -20 },
      { id: 'cam-1', type: 'camera', status: 'verified', x: 30, z: -35 },
      { id: 'gps-1', type: 'gps', status: 'unverified', x: 50, z: 20 },
      { id: 'pi-1', type: 'edge', status: 'verified', x: -30, z: 40 },
      { id: 'blocked-1', type: 'iot', status: 'blocked', x: 10, z: 55 }
    ];

    const trustOverrides = {
      verified: null,
      unverified: 0xffd166,
      blocked: 0xef476f
    };

    const colors = {
      iot: 0x4cc9f0,
      camera: 0xef476f,
      gps: 0xffd166,
      edge: 0x90e0ef
    };

    const arcs = [];

    points.forEach((p) => {
      const color = trustOverrides[p.status] || colors[p.type] || 0xffffff;

      const pin = new THREE.Mesh(
        new THREE.SphereGeometry(1.6, 16, 16),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.6 })
      );
      pin.position.set(p.x, 2, p.z);
      scene.add(pin);

      const halo = new THREE.Mesh(
        new THREE.RingGeometry(2.4, 3.2, 32),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6, side: THREE.DoubleSide })
      );
      halo.rotation.x = -Math.PI / 2;
      halo.position.set(p.x, 0.1, p.z);
      scene.add(halo);

      // Arc from device to hub
      const start = new THREE.Vector3(p.x, 2, p.z);
      const end = new THREE.Vector3(0, 5, 0);
      const mid = start.clone().add(end).multiplyScalar(0.5);
      mid.y += 20;

      const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
      const geo = new THREE.TubeGeometry(curve, 40, 0.15, 8, false);
      const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.5 });
      const arc = new THREE.Mesh(geo, mat);
      scene.add(arc);

      // Packet traveling along the arc
      const packet = new THREE.Mesh(
        new THREE.SphereGeometry(0.5, 8, 8),
        new THREE.MeshBasicMaterial({ color })
      );
      scene.add(packet);

      arcs.push({ curve, packet, t: Math.random() });
    });

    threatPoints.forEach((t) => {
      const color = t.severity === 'high' ? 0xef476f : 0xffd166;
      const wave = new THREE.Mesh(
        new THREE.RingGeometry(3, 3.5, 64),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.8, side: THREE.DoubleSide })
      );
      wave.rotation.x = -Math.PI / 2;
      wave.position.set(t.x, 0.2, t.z);
      scene.add(wave);
      arcs.push({ wave, t: Math.random() });
    });

    let frame;
    const clock = new THREE.Clock();

    const animate = () => {
      const dt = clock.getDelta();

      hub.rotation.y += dt * 0.5;

      arcs.forEach((a) => {
        if (a.wave) {
          a.t += dt * 0.6;
          if (a.t > 1) a.t = 0;
          const scale = 1 + a.t * 3;
          a.wave.scale.set(scale, scale, scale);
          a.wave.material.opacity = 0.8 * (1 - a.t);
        }
      });

      // Orbit camera slowly
      const time = clock.elapsedTime;
      camera.position.x = Math.sin(time * 0.15) * 110;
      camera.position.z = Math.cos(time * 0.15) * 110;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      const w = mount.clientWidth;
      const h = mount.clientHeight || 480;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [devices, threats]);

  return (
    <div
      ref={mountRef}
      style={{ width: '100%', height: '480px', borderRadius: 12, overflow: 'hidden' }}
    />
  );
}
