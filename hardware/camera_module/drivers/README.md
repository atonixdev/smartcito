# Camera Driver Standards

Contributors should implement camera integrations against open protocols first.

## Preferred Order

1. ONVIF for discovery, capabilities, PTZ, and camera management
2. RTSP for video streaming
3. HTTP/2 APIs for metadata, provisioning, and vendor extensions
4. Vendor-private SDKs only when open protocols are insufficient

## Contributor Contract

Every hardware driver document should state:
- supported camera models or vendor family
- discovery method
- auth mode
- stream URI format
- metadata fields mapped into Orca
- failure and reconnect behavior

## Interoperability Goal

By anchoring on ONVIF and RTSP, Orca can ingest globally compliant IP
camera feeds without coupling the platform to a single brand.
