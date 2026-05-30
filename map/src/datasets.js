const fs = require('fs');
const path = require('path');

const dataDir = path.join(__dirname, '..', 'data');

const countries = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'countries.json'), 'utf8'),
);
const regions = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'regions.json'), 'utf8'),
);
const areaCodes = JSON.parse(
  fs.readFileSync(path.join(dataDir, 'area-codes.json'), 'utf8'),
);

function getCountries() {
  return countries;
}

function getRegions(iso2) {
  return regions[iso2] || [];
}

function getAreaCodes(iso2) {
  return areaCodes[iso2] || {};
}

function resolveAreaCode(iso2, code) {
  const map = areaCodes[iso2] || {};
  const entry = map[code];
  if (!entry) return null;
  return {
    country: iso2,
    region: entry.region,
    city: entry.city,
    latitude: entry.lat,
    longitude: entry.lon,
  };
}

module.exports = {
  getCountries,
  getRegions,
  getAreaCodes,
  resolveAreaCode,
};
