# GPS Standards

Orca standardizes GPS and GNSS integrations around open, globally adopted
formats.

## Supported Standards

- NMEA 0183 for serial and embedded GNSS output
- NMEA 2000 for marine and specialized equipment where applicable
- GNSS metadata expressed as normalized JSON after ingestion

## Required Fields

- device identifier
- UTC timestamp
- latitude and longitude in WGS84
- altitude when available
- speed, heading, and accuracy when available
- fix quality and satellite count when available

## Goal

By standardizing on NMEA-derived fields, Orca can accept positioning data
from global device vendors without rewriting the rest of the platform.
