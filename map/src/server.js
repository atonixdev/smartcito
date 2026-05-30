const express = require('express');
const {
  getCountries,
  getRegions,
  getAreaCodes,
  lookupIP,
  fuseLocation,
  logLocationEvent,
} = require('./index');

const app = express();
app.use(express.json());

app.get('/api/location/countries', (req, res) => {
  res.json(getCountries());
});

app.get('/api/location/regions/:iso2', (req, res) => {
  res.json(getRegions(req.params.iso2.toUpperCase()));
});

app.get('/api/location/area-codes/:iso2', (req, res) => {
  res.json(getAreaCodes(req.params.iso2.toUpperCase()));
});

app.get('/api/location/ip/:ip', async (req, res) => {
  try {
    const result = await lookupIP(req.params.ip);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.post('/api/location/fuse', (req, res) => {
  const result = fuseLocation(req.body || {});
  res.json(result);
});

app.post('/api/location/log', (req, res) => {
  try {
    const event = logLocationEvent(req.body || {});
    res.json({ ok: true, event });
  } catch (err) {
    res.status(400).json({ ok: false, error: err.message });
  }
});

const port = process.env.PORT || 4010;
if (require.main === module) {
  app.listen(port, () => {
    console.log(`Orca Location Intelligence API on :${port}`);
  });
}

module.exports = app;
