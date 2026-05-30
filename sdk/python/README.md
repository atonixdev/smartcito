# Orca Python SDK

`orca_sdk` is a lightweight standard-library client for the repository's stable
API surfaces.

Current coverage includes:

- health endpoints
- control-plane overview, map, and scene endpoints
- live fleet and last-position GPS endpoints
- GPS ingest and gateway-ingest helpers
- camera registry read and write helpers
- operator control updates and map-device registration helpers

Example:

```python
from orca_sdk import OrcaClient

client = OrcaClient("http://localhost:8000", token="viewer-token")
print(client.health_status())
print(client.control_plane_overview())
```

For ready-to-edit request bodies, use the bundled CLI templates:

- `orca workspace templates`
- `orca workspace template camera-register`
- `orca workspace template-write camera-register --output camera-register.json`

## Installed Usage

From the repository root you can install the packaged CLI and SDK with:

```bash
python3 -m pip install .
```

If you need the lightweight service runtime dependencies as well, use:

```bash
python3 -m pip install ".[services]"
```

After installation, the CLI commands documented above are available as `orca ...`,
and the SDK can be imported with:

```python
from orca_sdk import OrcaClient
```