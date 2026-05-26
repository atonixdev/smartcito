from __future__ import annotations

import json
from pathlib import Path

from ai.training.train import train_from_dataset_dir


def test_train_from_dataset_dir_creates_versioned_model(tmp_path) -> None:
    dataset_dir = tmp_path / "datasets"
    models_dir = tmp_path / "models"
    dataset_dir.mkdir()

    records = [
        {
            "instruction": "Analyze GPS movement.",
            "input": "Lat: -26.2041; Lon: 28.0473; Speed: 12km/h",
            "output": "Movement normal. No action required.",
            "metadata": {"domain": "gps-analytics", "source": "test-fixture"},
        },
        {
            "instruction": "Interpret satellite observation.",
            "input": "Cloud cover: 62%; Region: Johannesburg; Temp: 18C",
            "output": "Weather stable. No operational risk.",
            "metadata": {"domain": "satellite-observation", "source": "test-fixture"},
        },
    ]
    (dataset_dir / "batch_external_sources.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    result = train_from_dataset_dir(
        dataset_dir=dataset_dir,
        models_dir=models_dir,
        version="smartcito_model_vtest",
        activate=False,
    )

    model_dir = Path(str(result["model_dir"]))
    assert result["version"] == "smartcito_model_vtest"
    assert result["records"] == 2
    assert model_dir.exists()
    assert (model_dir / "model.json").exists()
    assert (model_dir / "metrics.json").exists()
    assert (model_dir / "training_run.json").exists()
    assert (model_dir / "metadata.json").exists()
