const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const LEDGER_DIR =
  process.env.ATP_LEDGER_DIR || path.join(__dirname, '..', 'ledger');
const ATP_SECRET = process.env.ATP_SECRET || 'orca-dev-secret';

function ensureLedger() {
  if (!fs.existsSync(LEDGER_DIR)) {
    fs.mkdirSync(LEDGER_DIR, { recursive: true });
  }
}

function signEvent(payload) {
  return crypto
    .createHmac('sha256', ATP_SECRET)
    .update(JSON.stringify(payload))
    .digest('hex');
}

function logLocationEvent({ deviceId, authenticated, fused, sources }) {
  if (!deviceId) throw new Error('deviceId is required');
  if (!authenticated)
    throw new Error('Device must be authenticated before logging');
  if (!fused) throw new Error('No fused location available');

  ensureLedger();

  const event = {
    deviceId,
    fused,
    sources,
    timestamp: new Date().toISOString(),
  };

  event.signature = signEvent(event);

  const file = path.join(LEDGER_DIR, `${deviceId}.log`);
  fs.appendFileSync(file, JSON.stringify(event) + '\n');

  return event;
}

module.exports = { logLocationEvent, signEvent };
