const { resolveAreaCode } = require('./datasets');
const { validateGPS } = require('./gps');

const SOURCE_WEIGHTS = {
  gps: 1.0,
  ip: 0.6,
  areaCode: 0.4,
  userSelected: 0.3,
};

function gpsConfidence(gps) {
  if (!gps) return 0;
  if (gps.accuracy == null) return 0.8;
  if (gps.accuracy <= 10) return 1.0;
  if (gps.accuracy <= 50) return 0.9;
  if (gps.accuracy <= 250) return 0.75;
  return 0.5;
}

function ipConfidence(ip) {
  if (!ip || ip.latitude == null || ip.longitude == null) return 0;
  return ip.city ? 0.7 : 0.5;
}

function areaCodeConfidence(area) {
  return area ? 0.65 : 0;
}

function userSelectedConfidence(sel) {
  if (!sel) return 0;
  if (sel.country && sel.region) return 0.55;
  if (sel.country) return 0.35;
  return 0;
}

function fuseLocation(input) {
  const sources = [];

  const gps = validateGPS(input.gps);
  if (gps) {
    sources.push({
      source: 'gps',
      confidence: gpsConfidence(gps) * SOURCE_WEIGHTS.gps,
      data: gps,
    });
  }

  if (input.ip) {
    sources.push({
      source: 'ip',
      confidence: ipConfidence(input.ip) * SOURCE_WEIGHTS.ip,
      data: input.ip,
    });
  }

  let areaResolved = null;
  if (
    input.userSelected &&
    input.userSelected.country &&
    input.userSelected.areaCode
  ) {
    areaResolved = resolveAreaCode(
      input.userSelected.country,
      input.userSelected.areaCode,
    );
    if (areaResolved) {
      sources.push({
        source: 'areaCode',
        confidence: areaCodeConfidence(areaResolved) * SOURCE_WEIGHTS.areaCode,
        data: areaResolved,
      });
    }
  }

  if (input.userSelected) {
    sources.push({
      source: 'userSelected',
      confidence:
        userSelectedConfidence(input.userSelected) *
        SOURCE_WEIGHTS.userSelected,
      data: input.userSelected,
    });
  }

  if (sources.length === 0) {
    return { fused: null, sources: [] };
  }

  sources.sort((a, b) => b.confidence - a.confidence);
  const best = sources[0];

  const fused = {
    source: best.source,
    confidence: Number(best.confidence.toFixed(3)),
    country:
      best.data.country ||
      (input.userSelected && input.userSelected.country) ||
      null,
    region:
      best.data.region ||
      (input.userSelected && input.userSelected.region) ||
      null,
    city: best.data.city || null,
    latitude: best.data.latitude ?? null,
    longitude: best.data.longitude ?? null,
    timestamp: new Date().toISOString(),
  };

  return { fused, sources };
}

module.exports = { fuseLocation };
