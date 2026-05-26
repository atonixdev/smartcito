# SmartCito Adapter Evaluation Report

- Model: SmartCito Model
- Base model: meta-llama/Meta-Llama-3-8B-Instruct
- Backend: merged-local
- Dataset: datasets/sample_evaluation_data.json
- Adapter path: output/smartcito-lora
- Average overall score: 0.8178
- Pass rate: 1.0000
- Records: 3

## Domain Summary

| Domain | Records | Avg Score | Pass Rate |
| ------ | ------- | --------- | --------- |
| camera-analytics | 1 | 0.8544 | 1.0000 |
| drone-operations | 1 | 0.7823 | 1.0000 |
| orchestration | 1 | 0.8167 | 1.0000 |

## Per-Example Results

| ID | Domain | Overall | Recall | Precision | F1 | Required | Rubric | Passed | Violations |
| -- | ------ | ------- | ------ | --------- | -- | -------- | ------ | ------ | ---------- |
| drone-anomaly-001 | drone-operations | 0.7823 | 0.6667 | 0.8235 | 0.7369 | 1.0000 | 1.0000 | yes | none |
| camera-intrusion-001 | camera-analytics | 0.8544 | 0.8500 | 0.7727 | 0.8095 | 1.0000 | 1.0000 | yes | none |
| orchestration-001 | orchestration | 0.8167 | 0.8125 | 0.8125 | 0.8125 | 1.0000 | 0.6667 | yes | none |
