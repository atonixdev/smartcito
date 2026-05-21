"""
================================================================================
 File: backend/app/services/analytics.py
 Purpose:
   Lightweight, dependency-light analytics primitives for SmartCito.

   - `RollingAnomalyDetector`: online z-score detector. Cheap, robust,
     interpretable. Good default before reaching for ML.
   - `IsolationForestDetector`: scikit-learn based multivariate detector,
     trained on historical readings.

   These are intentionally framework-agnostic — they take and return plain
   numpy arrays / dataclasses so they can be invoked from the API, a Kafka
   consumer, a Spark/Dask job, or a notebook.

 When to graduate from this module:
   - Volume > ~10k events/sec → port the logic to PySpark Structured
     Streaming and consume the same Kafka topic.
   - Need deep learning → keep this module and add a sibling `ml_tf.py`
     module that loads a TensorFlow/PyTorch model.
================================================================================
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable

import numpy as np


@dataclass
class AnomalyVerdict:
    """Result of an anomaly check."""

    is_anomaly: bool
    score: float
    reason: str


class RollingAnomalyDetector:
    """Online z-score detector over a sliding window of values.

    A reading is flagged when |x - mean| > `threshold` * stddev. Until the
    window is full, the detector returns `is_anomaly=False` to avoid noisy
    cold-start alerts.
    """

    def __init__(self, window: int = 50, threshold: float = 3.0) -> None:
        if window < 5:
            raise ValueError("window must be >= 5 to compute a stable stddev")
        self._window = window
        self._threshold = threshold
        self._values: Deque[float] = deque(maxlen=window)

    def observe(self, value: float) -> AnomalyVerdict:
        """Record a value and return whether it looks anomalous."""
        self._values.append(value)
        if len(self._values) < self._window:
            return AnomalyVerdict(False, 0.0, "warming up")

        arr = np.asarray(self._values, dtype=np.float64)
        mean = float(arr.mean())
        std = float(arr.std(ddof=1)) or 1e-9  # avoid div-by-zero on flat signals
        z = (value - mean) / std
        return AnomalyVerdict(
            is_anomaly=abs(z) > self._threshold,
            score=float(z),
            reason=f"|z|={abs(z):.2f} threshold={self._threshold}",
        )


class IsolationForestDetector:
    """Wrapper around sklearn's IsolationForest with a stable API.

    The heavy `sklearn` import is deferred so that contributors who don't
    need ML can keep their environments lean.
    """

    def __init__(self, contamination: float = 0.01, random_state: int = 42) -> None:
        from sklearn.ensemble import IsolationForest  # local import

        self._model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self._fitted = False

    def fit(self, samples: Iterable[Iterable[float]]) -> "IsolationForestDetector":
        x = np.asarray(list(samples), dtype=np.float64)
        if x.ndim != 2:
            raise ValueError("expected a 2-D iterable of feature rows")
        self._model.fit(x)
        self._fitted = True
        return self

    def predict(self, sample: Iterable[float]) -> AnomalyVerdict:
        if not self._fitted:
            raise RuntimeError("call .fit(...) before .predict(...)")
        x = np.asarray([list(sample)], dtype=np.float64)
        score = float(self._model.score_samples(x)[0])
        is_anom = int(self._model.predict(x)[0]) == -1
        return AnomalyVerdict(
            is_anomaly=is_anom,
            score=score,
            reason=f"isolation-forest score={score:.3f}",
        )
