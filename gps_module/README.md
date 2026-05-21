# GPS Module

GPS and satellite-based positioning integration for SmartCito.

## Capabilities

- Live device + asset tracking via `gpsd` or serial NMEA
- Reverse geocoding and routing via `geopy`
- Satellite API integrations (e.g. Iridium, Globalstar) for off-grid coverage
- Geo-fencing, route deviation alerts, and dwell-time analytics

## Layout

```
gps_module/
├── drivers/         # Device + protocol drivers (NMEA, gpsd, vendor SDKs)
├── providers/       # Cloud / satellite provider integrations
├── geofencing/      # Geo-fence engine and alerting
└── README.md
```

## Conventions

- Coordinates are stored as **WGS84** (lat/lon, decimal degrees).
- Time is stored in **UTC**.
- All location events publish to the Kafka topic configured in
  `citosmart`'s settings.
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
