# SmartCito Location Intelligence

Sovereign location intelligence for SmartCito: country selection, region/area-code mapping, IP geolocation, GPS validation, and multi-source fusion with confidence scoring.

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
| GET | `/api/location/dashboard/logs` | Dashboard operational logs and correlated security cases |

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

## 3D Map Engine Expectations

The frontend map is designed for a WebGL engine such as Mapbox GL JS or
CesiumJS. The current webapp integration uses Mapbox GL JS when
`VITE_MAPBOX_TOKEN` is configured.

The frontend must render a real WebGL map. Configure Mapbox before running the
dashboard:

```bash
cd ../webapp
VITE_MAPBOX_TOKEN=pk_your_mapbox_token npm run dev
```

No CSS-only map mockup should be used for the dashboard map route.

Required behavior:

- full world coverage,
- dark basemap,
- country click and fly-to zoom,
- point click reverse-geocoding,
- 2D / 3D mode toggle,
- 3D terrain and building extrusion,
- address-level marker tracking,
- device, GPS, camera, weather, traffic, and threat overlays.
