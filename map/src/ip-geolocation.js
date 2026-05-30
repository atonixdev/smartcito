const fetch = (...args) =>
  import('node-fetch').then(({ default: f }) => f(...args));

const PROVIDER_URL = process.env.IP_GEO_URL || 'https://ipapi.co';

function isValidIP(ip) {
  const v4 = /^(\d{1,3}\.){3}\d{1,3}$/;
  const v6 = /^[0-9a-fA-F:]+$/;
  return v4.test(ip) || v6.test(ip);
}

async function lookupIP(ip) {
  if (!isValidIP(ip)) {
    throw new Error(`Invalid IP address: ${ip}`);
  }

  const res = await fetch(`${PROVIDER_URL}/${ip}/json/`);
  if (!res.ok) {
    throw new Error(`IP geolocation failed: ${res.status}`);
  }

  const data = await res.json();
  return {
    ip,
    country: data.country_code || null,
    region: data.region || null,
    city: data.city || null,
    latitude: data.latitude ?? null,
    longitude: data.longitude ?? null,
    asn: data.asn || null,
    isp: data.org || null,
  };
}

module.exports = { lookupIP, isValidIP };
