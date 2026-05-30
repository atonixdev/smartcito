const test = require('node:test');
const assert = require('node:assert');
const {
  getCountries,
  getRegions,
  resolveAreaCode,
} = require('../src/datasets');

test('Loads ISO-3166 countries', () => {
  const list = getCountries();
  assert.ok(list.length > 0);
  assert.ok(list.find((c) => c.iso2 === 'KE'));
});

test('Loads regions for a country', () => {
  const regions = getRegions('KE');
  assert.ok(regions.find((r) => r.code === 'NBO'));
});

test('Resolves area code to coordinates', () => {
  const r = resolveAreaCode('US', '415');
  assert.strictEqual(r.city, 'San Francisco');
  assert.ok(typeof r.latitude === 'number');
});
