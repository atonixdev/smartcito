<!--
================================================================================
 File: docs/processes/assets/PNG_ASSET_MANIFEST.md
 Purpose:
  Register PNG visual assets used by Smartcito process documentation.
================================================================================
-->

# PNG Asset Manifest

All images used by the process documentation must be stored in PNG format under
[png/](png/). Each asset should be clean, readable at documentation scale, and
suitable for technical onboarding, operations, or review material.

## Current Assets

| PNG File | Used By | Purpose |
|---|---|---|
| [png/smartcito-process-map.png](png/smartcito-process-map.png) | [../README.md](../README.md) | High-level map of Smartcito process areas |
| [png/developer-onboarding-flow.png](png/developer-onboarding-flow.png) | [../01-project-onboarding/PROCEDURE.md](../01-project-onboarding/PROCEDURE.md) | New developer onboarding sequence |
| [png/delivery-lifecycle.png](png/delivery-lifecycle.png) | [../03-feature-delivery/PROCEDURE.md](../03-feature-delivery/PROCEDURE.md) | Feature delivery lifecycle |
| [png/operations-response-flow.png](png/operations-response-flow.png) | [../08-incident-response/PROCEDURE.md](../08-incident-response/PROCEDURE.md) | Operational incident response path |

## Asset Requirements

- Format: PNG.
- Background: white or transparent unless the target document needs contrast.
- Typography: readable at 100 percent browser zoom.
- Style: technical, restrained, and consistent with the SmartCito documentation.
- Naming: lowercase words separated by hyphens.
- Versioning: replace only when the procedure changes; do not keep stale copies.

## Intake Checklist

- The file opens successfully as a PNG.
- The visual matches the procedure it supports.
- The text is legible on laptop and tablet screens.
- The manifest row is updated with the asset purpose and owning procedure.
- The procedure links to the asset near the relevant step or overview section.
