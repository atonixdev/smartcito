# GPS Classification

This module classifies short GPS windows into configurable operational classes.

## Inputs

- Sequence of GPS points with latitude, longitude, altitude, speed, heading, acceleration, and timestamp

## Outputs

- Predicted class index and label
- Softmax probabilities
- Learned GPS embedding for downstream fusion

## Train

```bash
python -m ai.keras_stack.models.gps_classification.train \
  --dataset path/to/gps_classification.json \
  --output-dir ai/models/keras/gps_classifier_v1
```

## Infer

```python
from ai.keras_stack.models.gps_classification.infer import classify_gps_sequence

result = classify_gps_sequence("ai/models/keras/gps_classifier_v1", gps_window)
```