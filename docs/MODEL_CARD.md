# SmartCito-LLaMA3-8B Model Card

## Model Overview

- Model name: `SmartCito-LLaMA3-8B`
- Base model: `meta-llama/Meta-Llama-3-8B-Instruct`
- Adaptation method: LoRA and QLoRA fine-tuning
- Distribution: SmartCito LoRA adapter weights only

SmartCito-LLaMA3-8B is a domain-specialized operational assistant for city monitoring, drone and robot missions, camera analytics, sensor fusion, security triage, geographic reasoning, and OpenStack or Kubernetes incident response.

## Intended Use

- Drone mission planning and telemetry interpretation
- Robot navigation summaries and route adjustments
- Camera event triage and threat detection
- Sensor-fusion analysis across city infrastructure
- Geographic deployment recommendations
- Infrastructure orchestration and incident response playbooks

## Training Data

SmartCito adapters are fine-tuned on structured instruction data using the schema documented in [training/dataset_format.md](training/dataset_format.md). Example domains include:

- drone telemetry and mission logs
- robot navigation traces
- city camera and security event summaries
- geographic engine outputs
- sensor fusion and anomaly patterns
- OpenStack and Kubernetes operations signals

The repository ships only sample and prepared contributor data. Base model weights are not included.

## Limitations

- The model can hallucinate and must not be treated as an autonomous authority.
- All safety-critical outputs require operator review.
- Performance depends on the quality and governance of contributed data.
- The model should not be used for identity decisions, arrests, or other high-impact actions without a verified human process.

## Safety and Governance

- Do not contribute personal data, secrets, or regulated data without approval.
- Remove access tokens, passwords, and raw credentials from logs before training.
- Upload only adapter weights to Kaggle or pull requests.
- Validate deployment behavior against SmartCito security and privacy policies before production rollout.

## Distribution Notes

- Legal artifact to share: `output/smartcito-lora/`
- Do not commit or redistribute Meta LLaMA-3 base checkpoints through this repository.
- Contributors may reference the base model from Hugging Face and combine it locally with SmartCito adapters for inference.