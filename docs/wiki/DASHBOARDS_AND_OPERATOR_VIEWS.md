<!--
================================================================================
 File: docs/wiki/DASHBOARDS_AND_OPERATOR_VIEWS.md
 Purpose:
   Dedicated wiki page for SmartCito dashboards, panels, operator workflows,
   and visual monitoring surfaces.
================================================================================
-->

# Dashboards and Operator Views

## What This Module Does

This area explains the operator-facing web experience: dashboard panels,
camera fleet views, recent readings, traffic summaries, and monitoring intent.

## Why It Is Important

The platform only becomes operationally useful when raw telemetry becomes
readable, actionable, and trustworthy for human operators.

## How It Connects To Other Modules

- consumes API and event data,
- exposes security and fleet state to operators,
- visualizes device health and traffic conditions,
- supports hardware-backed operational decisions.

## Security Measures Applied

- dashboard access follows API auth and RBAC,
- operator data is sourced through controlled endpoints,
- live operational context is bounded by backend policy checks.

## View Flow

```mermaid
flowchart LR
    A[Device and Event Data] --> B[API Gateway]
    B --> C[Dashboard Data Hooks]
    C --> D[Operator Panels]
    D --> E[Analyst and Admin Actions]
```

## Related Surfaces

- [../../webapp/src/pages/Dashboard.tsx](../../webapp/src/pages/Dashboard.tsx)
- [../../webapp/src/components/RegisteredCamerasPanel.tsx](../../webapp/src/components/RegisteredCamerasPanel.tsx)
- [../../webapp/src/components/TrafficSummaryPanel.tsx](../../webapp/src/components/TrafficSummaryPanel.tsx)
- [../../webapp/src/components/RecentReadingsPanel.tsx](../../webapp/src/components/RecentReadingsPanel.tsx)

## Container Run Instructions

```bash
docker compose up --build webapp
open http://localhost:5173
```

## Visual Design Note

As real screenshots or exports become available, this page should be updated
with images of the dashboard, Grafana panels, and operator alert states.