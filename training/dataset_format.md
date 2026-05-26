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
- Do not include raw LLaMA weights, access tokens, or proprietary keys in dataset rows.

## Supported Domains

- Drone mission planning and telemetry
- Robot navigation and edge autonomy
- City camera analytics and event triage
- Sensor fusion and anomaly detection
- Geographic reasoning and routing
- OpenStack and Kubernetes incident response

## Preparation Flow

1. Add or collect JSON/JSONL records using the schema above.
2. Run `python training/prepare_dataset.py --input <raw-data> --output datasets/prepared_smartcito_training_data.jsonl`.
3. Train with `python training/lora_training.py` or `python training/qlora_training.py`.
4. Share only the adapter directory from `output/smartcito-lora/`.