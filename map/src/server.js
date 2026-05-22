const express = require('express');
const {
  getCountries,
  getRegions,
  getAreaCodes,
  lookupIP,
  fuseLocation,
  logLocationEvent
} = require('./index');

const app = express();
app.use(express.json());

function requireDashboardAuth(req, res, next) {
  if (process.env.REQUIRE_DASHBOARD_AUTH === 'true' && !req.headers.authorization) {
    return res.status(401).json({ error: 'Missing Authorization header' });
  }
  return next();
}

const dashboard3dPayload = {
  generated_at: new Date().toISOString(),
  map: {
    name: 'SmartCito Nairobi Edge Map',
    mode: '3d',
    center: { latitude: -1.2921, longitude: 36.8219 },
    bounds: {
      north: -1.24,
      south: -1.34,
      east: 36.88,
      west: 36.76
    }
  },
  devices: [
    {
      id: 'PI-NBO-01',
      name: 'Raspberry Pi Edge Node',
      type: 'edge',
      status: 'verified',
      trust_score: 96,
      latitude: -1.2921,
      longitude: 36.8219,
      x: -35,
      z: 12,
      telemetry: 'CPU 42% · MQTT online · GPS fused',
      camera_stream: null
    },
    {
      id: 'CAM-12',
      name: 'Street Camera',
      type: 'camera',
      status: 'verified',
      trust_score: 94,
      latitude: -1.2864,
      longitude: 36.8172,
      x: 22,
      z: -24,
      telemetry: 'Encrypted live stream · object detection enabled',
      camera_stream: 'rtsp://camera.local/cam-12'
    },
    {
      id: 'GPS-07',
      name: 'GPS Tracker',
      type: 'gps',
      status: 'unverified',
      trust_score: 72,
      latitude: -1.2655,
      longitude: 36.8054,
      x: 48,
      z: 28,
      telemetry: 'Accuracy ±12m · path deviation watch',
      camera_stream: null
    },
    {
      id: 'IOT-44',
      name: 'IoT Air Sensor',
      type: 'iot',
      status: 'verified',
      trust_score: 88,
      latitude: -1.3102,
      longitude: 36.8388,
      x: -48,
      z: -34,
      telemetry: 'PM2.5 normal · humidity 62%',
      camera_stream: null
    },
    {
      id: 'SEC-BLOCK-03',
      name: 'Blocked Unknown Node',
      type: 'iot',
      status: 'blocked',
      trust_score: 21,
      latitude: -1.3001,
      longitude: 36.8299,
      x: 5,
      z: 42,
      telemetry: 'Blocked by ATP trust policy',
      camera_stream: null
    }
  ],
  threats: [
    {
      id: 'THREAT-001',
      label: 'AI motion anomaly near CAM-12',
      severity: 'high',
      x: 22,
      z: -24
    },
    {
      id: 'THREAT-002',
      label: 'GPS path deviation on GPS-07',
      severity: 'medium',
      x: 48,
      z: 28
    }
  ],
  gps_paths: [
    {
      device_id: 'GPS-07',
      points: [
        { x: 30, z: 10 },
        { x: 38, z: 18 },
        { x: 48, z: 28 }
      ]
    }
  ]
};

const operationsVisualizationPayload = {
  generated_at: new Date().toISOString(),
  map: {
    name: 'SmartCito Nairobi Operations Map',
    center: { latitude: -1.2921, longitude: 36.8219 },
    zones: [
      { id: 'zone-cbd', label: 'CBD', x: 50, y: 46, risk: 'medium' },
      { id: 'zone-westlands', label: 'Westlands', x: 38, y: 34, risk: 'low' },
      { id: 'zone-industrial', label: 'Industrial Area', x: 62, y: 65, risk: 'high' }
    ]
  },
  devices: [
    { id: 'PI-NBO-01', type: 'edge', status: 'verified', trust_score: 96, x: 30, y: 42, label: 'Raspberry Pi Edge' },
    { id: 'CAM-12', type: 'camera', status: 'verified', trust_score: 94, x: 56, y: 36, label: 'Street Camera' },
    { id: 'GPS-07', type: 'gps', status: 'unverified', trust_score: 72, x: 68, y: 58, label: 'GPS Tracker' },
    { id: 'IOT-44', type: 'iot', status: 'verified', trust_score: 88, x: 38, y: 66, label: 'IoT Sensor' }
  ],
  gps_paths: [
    {
      id: 'gps-path-07',
      device_id: 'GPS-07',
      points: [
        { x: 24, y: 68 },
        { x: 36, y: 62 },
        { x: 50, y: 60 },
        { x: 68, y: 58 }
      ]
    }
  ],
  traffic: [
    { id: 'traffic-1', label: 'CBD congestion', level: 'high', x: 52, y: 48, value: 87 },
    { id: 'traffic-2', label: 'Westlands flow', level: 'medium', x: 38, y: 34, value: 54 },
    { id: 'traffic-3', label: 'Industrial queue', level: 'high', x: 64, y: 66, value: 91 }
  ],
  threats: [
    { id: 'threat-1', label: 'AI motion anomaly', severity: 'high', x: 56, y: 36 },
    { id: 'threat-2', label: 'GPS deviation', severity: 'medium', x: 68, y: 58 }
  ],
  weather: [
    { id: 'weather-1', label: 'Rain cell', type: 'rain', intensity: 66, x: 44, y: 30 },
    { id: 'weather-2', label: 'Wind corridor', type: 'wind', intensity: 42, x: 70, y: 42 },
    { id: 'weather-3', label: 'Heat island', type: 'heat', intensity: 78, x: 60, y: 70 }
  ]
};

const unifiedLogEvents = [
  {
    id: 'log-001',
    timestamp: new Date().toISOString(),
    type: 'device',
    severity: 'info',
    device_id: 'PI-NBO-01',
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '10.10.20.12',
    gps: { latitude: -1.2921, longitude: 36.8219 },
    message: 'Raspberry Pi edge node heartbeat normal',
    incident_id: null
  },
  {
    id: 'log-002',
    timestamp: new Date().toISOString(),
    type: 'security',
    severity: 'warning',
    device_id: 'CAM-12',
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '41.90.12.44',
    gps: { latitude: -1.2864, longitude: 36.8172 },
    message: 'Repeated token validation failures from camera network path',
    incident_id: 'INC-001'
  },
  {
    id: 'log-003',
    timestamp: new Date().toISOString(),
    type: 'network',
    severity: 'critical',
    device_id: 'CAM-12',
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '41.90.12.44',
    gps: { latitude: -1.2864, longitude: 36.8172 },
    message: 'Suspicious IP burst detected against stream endpoint',
    incident_id: 'INC-001'
  },
  {
    id: 'log-004',
    timestamp: new Date().toISOString(),
    type: 'sensor',
    severity: 'warning',
    device_id: 'GPS-07',
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '10.10.31.7',
    gps: { latitude: -1.2655, longitude: 36.8054 },
    message: 'GPS path deviation exceeded expected corridor',
    incident_id: 'INC-002'
  },
  {
    id: 'log-005',
    timestamp: new Date().toISOString(),
    type: 'operations',
    severity: 'info',
    device_id: 'IOT-44',
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '10.10.44.9',
    gps: { latitude: -1.3102, longitude: 36.8388 },
    message: 'Air quality value within normal operating range',
    incident_id: null
  }
];

const aiThreatCases = [
  {
    id: 'INC-001',
    label: 'Camera Stream Token Abuse',
    threat_score: 91,
    severity: 'critical',
    devices: ['CAM-12'],
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '41.90.12.44',
    gps: { latitude: -1.2864, longitude: 36.8172 },
    time_window: 'last 10 minutes',
    key_log_ids: ['log-002', 'log-003'],
    explanation: 'Token failures and network bursts are correlated against the same camera stream endpoint.',
    suggested_action: 'Block IP and rotate camera stream token'
  },
  {
    id: 'INC-002',
    label: 'GPS Path Deviation',
    threat_score: 67,
    severity: 'warning',
    devices: ['GPS-07'],
    country: 'KE',
    region: 'NBO',
    area_code: '020',
    ip: '10.10.31.7',
    gps: { latitude: -1.2655, longitude: 36.8054 },
    time_window: 'last 15 minutes',
    key_log_ids: ['log-004'],
    explanation: 'GPS movement diverged from the expected corridor while device trust is not fully verified.',
    suggested_action: 'Monitor only and request fresh GPS attestation'
  }
];

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'location-api' });
});

app.get('/api/location/health', (req, res) => {
  res.json({ status: 'ok', service: 'location-api' });
});

app.get('/api/location/dashboard/3d', requireDashboardAuth, (req, res) => {
  res.json({
    ...dashboard3dPayload,
    generated_at: new Date().toISOString()
  });
});

app.post('/api/location/dashboard/audit', requireDashboardAuth, (req, res) => {
  res.json({
    ok: true,
    event: {
      type: 'visualization.audit',
      payload: req.body || {},
      timestamp: new Date().toISOString()
    }
  });
});

app.get('/api/location/dashboard/visualization', (req, res) => {
  res.json({
    ...operationsVisualizationPayload,
    generated_at: new Date().toISOString()
  });
});

app.get('/api/location/dashboard/logs', requireDashboardAuth, (req, res) => {
  res.json({
    generated_at: new Date().toISOString(),
    logs: unifiedLogEvents.map((event) => ({
      ...event,
      timestamp: new Date().toISOString()
    })),
    threats: aiThreatCases
  });
});

app.get('/api/v1/sensors/recent', (req, res) => {
  const limit = Number(req.query.limit || 20);

  const readings = [
    {
      id: 'reading-001',
      sensor_id: 'IOT-44',
      kind: 'air_quality',
      value: 42,
      unit: 'AQI',
      latitude: -1.3102,
      longitude: 36.8388,
      observed_at: new Date().toISOString(),
      received_at: new Date().toISOString(),
      metadata: { source: 'map-api-fallback', area: 'Industrial Area' }
    },
    {
      id: 'reading-002',
      sensor_id: 'GPS-07',
      kind: 'traffic',
      value: 87,
      unit: 'vehicles/min',
      latitude: -1.2655,
      longitude: 36.8054,
      observed_at: new Date().toISOString(),
      received_at: new Date().toISOString(),
      metadata: { source: 'map-api-fallback', area: 'Westlands' }
    },
    {
      id: 'reading-003',
      sensor_id: 'PI-NBO-01',
      kind: 'other',
      value: 51,
      unit: 'celsius',
      latitude: -1.2921,
      longitude: 36.8219,
      observed_at: new Date().toISOString(),
      received_at: new Date().toISOString(),
      metadata: { source: 'raspberry-pi', metric: 'cpu_temp' }
    }
  ];

  res.json(readings.slice(0, limit));
});

app.get('/api/v1/traffic/summary', (req, res) => {
  res.json({
    total_samples: 3,
    sensors: [
      {
        sensor_id: 'traffic-cbd-001',
        samples: 48,
        average_value: 87,
        unit: 'vehicles/min'
      },
      {
        sensor_id: 'traffic-westlands-002',
        samples: 32,
        average_value: 54,
        unit: 'vehicles/min'
      },
      {
        sensor_id: 'traffic-industrial-003',
        samples: 41,
        average_value: 91,
        unit: 'vehicles/min'
      }
    ]
  });
});

app.get('/api/v1/cameras', (req, res) => {
  res.json([
    {
      id: 'CAM-12',
      name: 'Street Camera',
      status: 'live',
      location: 'Nairobi CBD',
      latitude: -1.2864,
      longitude: 36.8172,
      stream_url: 'rtsp://camera.local/cam-12',
      trust_score: 94
    },
    {
      id: 'CAM-18',
      name: 'Industrial Gate Camera',
      status: 'live',
      location: 'Industrial Area',
      latitude: -1.3102,
      longitude: 36.8388,
      stream_url: 'rtsp://camera.local/cam-18',
      trust_score: 91
    }
  ]);
});

const router = express.Router();

router.get('/countries', (req, res) => {
  res.json(getCountries());
});

router.get('/regions/:iso2', (req, res) => {
  res.json(getRegions(req.params.iso2.toUpperCase()));
});

router.get('/area-codes/:iso2', (req, res) => {
  res.json(getAreaCodes(req.params.iso2.toUpperCase()));
});

router.get('/ip/:ip', async (req, res) => {
  try {
    const result = await lookupIP(req.params.ip);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

router.post('/fuse', (req, res) => {
  const result = fuseLocation(req.body || {});
  res.json(result);
});

router.post('/log', (req, res) => {
  try {
    const event = logLocationEvent(req.body || {});
    res.json({ ok: true, event });
  } catch (err) {
    res.status(400).json({ ok: false, error: err.message });
  }
});

app.use('/api/location', router);
app.use('/api/v1/location', router);

const port = process.env.PORT || 4010;
if (require.main === module) {
  app.listen(port, () => {
    console.log(`SmartCito Location Intelligence API on :${port}`);
  });
}

module.exports = app;
