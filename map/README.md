# Orca Location Intelligence

Sovereign location intelligence for Orca: country selection, region/area-code mapping, IP geolocation, GPS validation, and multi-source fusion with confidence scoring.

## Container Image

- Build file: `map/Dockerfile`
- What the image does: runs the Node.js location intelligence API on port `4010` with `node src/server.js`.
- What ships in the image: the `map/` application source, installed production dependencies, and this README at `/app/README.md`.

## Features

- ISO-3166 country dataset
- Region/state/province lookup
- Area code → city → coordinates mapping
- IPv4 + IPv6 geolocation with ASN/ISP
- GPS reader with accuracy validation
- Location Fusion Engine with confidence scoring
- ATP ledger logging with HMAC signature

## API

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/api/location/countries` | List countries |
| GET | `/api/location/regions/:iso2` | Regions for a country |
| GET | `/api/location/area-codes/:iso2` | Area codes for a country |
| GET | `/api/location/ip/:ip` | IP geolocation |
| POST | `/api/location/fuse` | Fuse multiple location sources |
| POST | `/api/location/log` | Log location event to ATP ledger |

## Source Priority

1. GPS (highest)
2. IP geolocation
3. Area-code resolution
4. User-selected country/region (lowest)

## Run

```bash
npm install
npm start
npm test
```
