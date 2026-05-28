# GPS Modules

GNSS reference components and integration notes for Orca camera hardware.

## Recommended Chip Families

- u-blox for broad ecosystem support
- Broadcom for compact high-accuracy modules
- optional dead-reckoning capable modules for urban canyon deployments

## Data Requirements

Every device location sample should include:
- latitude and longitude in WGS84
- altitude when available
- speed and heading when available
- satellite fix quality
- horizontal accuracy estimate
- UTC timestamp from trusted source
- device identifier and stream/session identifier

## Integration

- local device firmware can emit NMEA or structured JSON
- Linux-based devices can bridge through `gpsd`
- Orca services normalize location events in [`../../gps_module/`](../../gps_module/)

## Security

- sign or MAC each location update before transit when possible
- use TLS for every uplink
- bind device identity to issued API credentials
