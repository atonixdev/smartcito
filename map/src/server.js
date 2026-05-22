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
