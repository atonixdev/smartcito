# SmartCito Dataset Format

SmartCito fine-tuning data uses four fields per record:

- `instruction`: the task the model must complete.
- `input`: the structured mission, telemetry, sensor, map, or security context.
- `output`: the expected operational response.
- `metadata`: optional provenance and governance details such as source system, domain, risk level, and reviewer status.

## JSON Schema

```json
{
  "instruction": "Analyze drone telemetry for anomalies",
  "input": "GPS: -26.2041,28.0473; Altitude: 128m; Battery: 41%; Camera: stable; Rotor vibration: 0.83",
  "output": "Anomaly detected: rotor imbalance on rear-left motor. Reduce speed, return to inspection waypoint, and schedule maintenance.",
  "metadata": {
    "domain": "drone-operations",
    "source": "drone-edge",
    "priority": "high",
    "reviewed": true
  }
}
```

## Required Guidelines

- Keep `instruction` imperative and specific.
- Keep `input` factual. Include sensor values, timestamps, locations, and system context.
- Keep `output` actionable and bounded to what an operator could reasonably infer.
- Keep `metadata` free of secrets or personal data.
- Do not include raw foundation-model weights, access tokens, or proprietary keys in dataset rows.

## Supported Domains

- Drone mission planning and telemetry
- Robot navigation and edge autonomy
- City camera analytics and event triage
- Sensor fusion and anomaly detection
- Geographic reasoning and routing
- OpenStack and Kubernetes incident response

## Preparation Flow

1. Add or collect JSON/JSONL records using the schema above.
2. Run `python ai/training/prepare_dataset.py --input <raw-data> --output ai/datasets/prepared_smartcito_training_data.jsonl` when your source data already follows the SmartCito schema.
3. For edge-device logs, pass a source type to normalize them into SmartCito training records:

```bash
python ai/training/prepare_dataset.py \
  --input ai/datasets/raw_drone_logs.json \
  --source-type drone \
  --output ai/datasets/prepared_smartcito_training_data.jsonl
```

Supported source types:

- `drone` for patrol, telemetry, and mission logs
- `robot` for navigation and autonomy traces
- `camera` for city camera anomaly and perimeter events
- `sensor` for IoT and sensor-fusion alerts
- `geographic` for routing and deployment-planning inputs
- `threat` for incident and threat-reasoning logs
- `operator` for operator actions, command decisions, and follow-up workflows

The normalizer exposes source-specific hooks in [prepare_dataset.py](prepare_dataset.py):

- `build_record_from_drone_log`
- `build_record_from_robot_log`
- `build_record_from_camera_log`
- `build_record_from_sensor_log`
- `build_record_from_geographic_log`
- `build_record_from_threat_log`
- `build_record_from_operator_log`

Contributors can extend these helpers or add their own source type to convert sovereign operational data into SmartCito instruction records.
4. Train with `python ai/training/lora_training.py --base-model <provider-model-id>` or `python ai/training/qlora_training.py --base-model <provider-model-id>`.
5. Share only the adapter directory from `ai/output/smartcito-lora/`.