export const smartCitoDevices3D = [
  {
    id: 'PI-NBO-01',
    name: 'Raspberry Pi Edge Node',
    type: 'edge',
    status: 'verified',
    trustScore: 96,
    latitude: -1.2921,
    longitude: 36.8219,
    x: -28,
    z: 12,
    telemetry: 'CPU 42% · Temp 51°C · MQTT online'
  },
  {
    id: 'CAM-12',
    name: 'Street Camera',
    type: 'camera',
    status: 'verified',
    trustScore: 94,
    latitude: -1.2864,
    longitude: 36.8172,
    x: 18,
    z: -20,
    streamUrl: 'rtsp://camera.local/cam-12',
    telemetry: 'Live feed · encrypted'
  },
  {
    id: 'GPS-07',
    name: 'GPS Tracker',
    type: 'gps',
    status: 'unverified',
    trustScore: 72,
    latitude: -1.2655,
    longitude: 36.8054,
    x: 42,
    z: 24,
    telemetry: 'Accuracy ±12m'
  },
  {
    id: 'IOT-44',
    name: 'IoT Air Sensor',
    type: 'iot',
    status: 'verified',
    trustScore: 88,
    latitude: -1.3102,
    longitude: 36.8388,
    x: -44,
    z: -32,
    telemetry: 'PM2.5 normal · humidity 62%'
  },
  {
    id: 'SEC-BLOCK-03',
    name: 'Blocked Unknown Node',
    type: 'iot',
    status: 'blocked',
    trustScore: 21,
    latitude: -1.3001,
    longitude: 36.8299,
    x: 5,
    z: 40,
    telemetry: 'Blocked by ATP trust policy'
  }
];

export const smartCitoThreats3D = [
  {
    id: 'THREAT-001',
    label: 'AI motion anomaly',
    severity: 'high',
    x: 18,
    z: -20
  },
  {
    id: 'THREAT-002',
    label: 'GPS path deviation',
    severity: 'medium',
    x: 42,
    z: 24
  }
];
