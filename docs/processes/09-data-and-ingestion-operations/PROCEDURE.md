<!--
================================================================================
 File: docs/processes/09-data-and-ingestion-operations/PROCEDURE.md
 Purpose:
   Data ingestion, stream, schema, and storage operations procedure.
================================================================================
-->

# Data And Ingestion Operations Procedure

## Purpose

Define the operational steps for onboarding, validating, and monitoring data
sources across SmartCito ingestion paths.

## Scope

This procedure covers MQTT, HTTP, RTSP, ONVIF, GPS, Kafka, storage updates,
schemas, and data quality checks.

## Procedure

1. Identify the source type, protocol, expected payload, update frequency, and
   ownership team.
2. Confirm authentication, authorization, encryption, and network requirements.
3. Validate the payload against the relevant schema before accepting production
   traffic.
4. Configure the ingestion adapter, topic, stream, or endpoint.
5. Confirm data lands in the expected queue, cache, database, or downstream
   service.
6. Monitor lag, malformed messages, dropped frames, duplicate events, and schema
   drift.
7. Record onboarding evidence, data quality expectations, and rollback steps.
8. Update API or operator documentation when the source becomes user-visible.

## Validation Checklist

- Source owner and protocol are documented.
- Payload validation succeeds.
- Authentication and encryption controls are confirmed.
- Downstream consumers receive expected data.
- Monitoring signals are defined.

## Related Documentation

- [../../../ingestion/README.md](../../../ingestion/README.md)
- [../../../camera_module/README.md](../../../camera_module/README.md)
- [../../../gps_module/README.md](../../../gps_module/README.md)
- [../../API.md](../../API.md)
