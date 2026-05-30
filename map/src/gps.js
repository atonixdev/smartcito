function validateGPS(gps) {
  if (!gps || typeof gps !== 'object') return null;
  const { latitude, longitude, accuracy, timestamp } = gps;

  if (typeof latitude !== 'number' || typeof longitude !== 'number')
    return null;
  if (latitude < -90 || latitude > 90) return null;
  if (longitude < -180 || longitude > 180) return null;

  return {
    latitude,
    longitude,
    accuracy: typeof accuracy === 'number' ? accuracy : null,
    timestamp: timestamp || new Date().toISOString(),
  };
}

module.exports = { validateGPS };
