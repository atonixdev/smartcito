const test = require('node:test');
const assert = require('node:assert');
const { fuseLocation } = require('../src/fusion-engine');

test('GPS overrides IP when both present', () => {
  const { fused } = fuseLocation({
    gps: { latitude: -1.29, longitude: 36.82, accuracy: 5 },
    ip: {
      country: 'US',
      city: 'San Francisco',
      latitude: 37.77,
      longitude: -122.41,
    },
  });
  assert.strictEqual(fused.source, 'gps');
  assert.strictEqual(fused.latitude, -1.29);
});

test('Falls back to IP when no GPS', () => {
  const { fused } = fuseLocation({
    ip: { country: 'US', city: 'New York', latitude: 40.71, longitude: -74.0 },
  });
  assert.strictEqual(fused.source, 'ip');
});

test('Resolves area code when user-selected', () => {
  const { fused } = fuseLocation({
    userSelected: { country: 'KE', areaCode: '020' },
  });
  assert.ok(fused);
  assert.strictEqual(fused.city, 'Nairobi');
});

test('Returns null when no sources', () => {
  const { fused } = fuseLocation({});
  assert.strictEqual(fused, null);
});
