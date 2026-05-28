# Trajectory Prediction

This module predicts the next GPS positions from a past movement history.

## Inputs

- Past GPS sequence with the shared Orca GPS schema

## Outputs

- Future position sequence in relative coordinate space

## Train

```bash
python -m ai.keras_stack.models.trajectory_prediction.train \
  --dataset path/to/trajectory_examples.json \
  --output-dir ai/models/keras/trajectory_v1
```

## Infer

```python
from ai.keras_stack.models.trajectory_prediction.infer import predict_trajectory

result = predict_trajectory("ai/models/keras/trajectory_v1", past_sequence)
```