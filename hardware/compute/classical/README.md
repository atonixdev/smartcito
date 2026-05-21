# Classical Compute

Reference classical compute baseline for SmartCito.

## Purpose

This layer runs the present-day production backbone:
- API services and orchestration
- ingestion, streaming, and storage services
- dashboard and visualization workloads
- GPU-backed AI inference and analytics

## Reference Profile

- CPU: Intel Xeon or AMD EPYC
- GPU: NVIDIA A100/H100 or equivalent accelerator where needed
- RAM: 256 GB or more for heavy analytics nodes
- NVMe scratch storage for high-rate ingestion and temporary processing
- dual PSUs and redundant network uplinks

## Placement

Use this layer for all workloads that must run reliably today without any
quantum dependency. This is the default execution plane for SmartCito.
