# GPS Module

GPS and satellite-based positioning integration for Orca.

## Container Image

- Build file: `gps_module/Dockerfile`
- What the image does: runs the FastAPI GPS-domain API on port `8011` for NMEA parsing, standards lookup, and location stream normalization.
- What ships in the image: the `gps_module/` package and this README at `/app/gps_module/README.md`.

## Capabilities

- Live device + asset tracking via `gpsd` or serial NMEA
- Reverse geocoding and routing via `geopy`
- Satellite API integrations (e.g. Iridium, Globalstar) for off-grid coverage
- Geo-fencing, route deviation alerts, and dwell-time analytics

## Layout

```
gps_module/
├── Dockerfile       # Container image for the GPS-domain API
├── requirements.txt # Python runtime dependencies
├── nmea.py          # NMEA parsing helpers
├── service.py       # FastAPI GPS-domain service
└── README.md
```

## Conventions

- Coordinates are stored as **WGS84** (lat/lon, decimal degrees).
- Time is stored in **UTC**.
- All location events publish to the Kafka topic configured in
  `orcaapi`'s settings.
- NMEA 0183 and NMEA 2000 are the preferred interoperability standards for
  incoming GNSS data.
- GPS payloads must be protected in transit with TLS and per-message
  integrity tags as defined in
  [`../security/crypto/STANDARDS.md`](../security/crypto/STANDARDS.md).
- Access to location data must be controlled through RBAC policies in
  [`../security/rbac/policies.yaml`](../security/rbac/policies.yaml).
- Contributor-facing hardware guidance lives in
  [`../hardware/gps_module/`](../hardware/gps_module/).

## Fusion with Cameras

GPS streams are joined with camera metadata at the analytics layer to enable
location-aware surveillance (e.g. "show all detections within 500 m of
asset X in the last hour").

## Technologies Used

- Python 3.11
- FastAPI
- Uvicorn
- NMEA parsing helpers

## How To Run Its Container

```bash
docker build -f gps_module/Dockerfile -t orca-gps-module .
docker run --rm -p 8011:8011 orca-gps-module
```

## Example Usage

```bash
curl http://localhost:8011/standards
curl -X POST http://localhost:8011/parse \
  -H 'Content-Type: application/json' \
  -d '{"sentence":"$GPGGA,123519,4807.038,N,01131.000,E,1,08"}'
```
