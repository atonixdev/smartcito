from fastapi.testclient import TestClient
from io import BytesIO

from PIL import Image

from ai.ai_models.inference import app


client = TestClient(app)


def test_health(monkeypatch) -> None:
    monkeypatch.delenv("LLAMA_STACK_BASE_URL", raising=False)
    monkeypatch.delenv("LLAMA_STACK_MODEL", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-models",
        "llama_stack": "not-configured",
        "orca_model": "not-deployed",
    }


def test_infer_returns_bounded_score() -> None:
    response = client.post("/infer", json={"features": [0.1, -0.8, 2.5]})

    assert response.status_code == 200
    assert response.json()["score"] == 1.0


def test_models_endpoint_reports_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("LLAMA_STACK_BASE_URL", raising=False)
    monkeypatch.delenv("LLAMA_STACK_MODEL", raising=False)

    response = client.get("/models")

    assert response.status_code == 200
    assert response.json() == {
        "service": "ai-models",
        "provider": "llama-stack",
        "configured": False,
        "models": [],
        "default_model": None,
    }


def test_generate_requires_llama_stack_configuration(monkeypatch) -> None:
    monkeypatch.delenv("LLAMA_STACK_BASE_URL", raising=False)
    monkeypatch.delenv("LLAMA_STACK_MODEL", raising=False)

    response = client.post("/generate", json={"prompt": "Summarize traffic anomalies."})

    assert response.status_code == 503
    assert "LLAMA_STACK_BASE_URL and LLAMA_STACK_MODEL" in response.json()["detail"]


def test_generate_proxies_to_llama_stack(monkeypatch) -> None:
    async def fake_generate_text(
        prompt: str,
        *,
        system_prompt: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int,
        backend: str | None = None,
        adapter_path: str | None = None,
        merge_lora: bool = False,
    ) -> dict[str, object]:
        assert prompt == "Summarize traffic anomalies."
        assert system_prompt == "You are an analyst."
        assert model == "Llama-4-Maverick"
        assert temperature == 0.1
        assert max_tokens == 128
        assert backend == "remote"
        assert adapter_path is None
        assert merge_lora is False
        return {
            "model": "Llama-4-Maverick",
            "provider": "llama-stack",
            "text": "No anomalies detected.",
            "raw": {"choices": [{"message": {"content": "No anomalies detected."}}]},
        }

    monkeypatch.setattr("ai.ai_models.inference.generate_text", fake_generate_text)

    response = client.post(
        "/generate",
        json={
            "prompt": "Summarize traffic anomalies.",
            "system_prompt": "You are an analyst.",
            "model": "Llama-4-Maverick",
            "backend": "remote",
            "temperature": 0.1,
            "max_tokens": 128,
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "No anomalies detected."


def test_generate_supports_local_lora_backend(monkeypatch) -> None:
    async def fake_generate_text(
        prompt: str,
        *,
        system_prompt: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int,
        backend: str | None = None,
        adapter_path: str | None = None,
        merge_lora: bool = False,
    ) -> dict[str, object]:
        assert prompt == "Analyze drone telemetry for anomalies."
        assert backend == "merged-local"
        assert model == "meta-llama/Meta-Llama-3-8B-Instruct"
        assert adapter_path == "./ai/output/orca-lora"
        assert merge_lora is True
        return {
            "model": "Orca Model",
            "provider": "local-peft-merged",
            "text": "Rotor imbalance detected on drone alpha.",
            "raw": {"adapter_path": adapter_path},
        }

    monkeypatch.setattr("ai.ai_models.inference.generate_text", fake_generate_text)

    response = client.post(
        "/generate",
        json={
            "prompt": "Analyze drone telemetry for anomalies.",
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "backend": "merged-local",
            "adapter_path": "./ai/output/orca-lora",
            "merge_lora": True,
            "temperature": 0.0,
            "max_tokens": 128,
        },
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "local-peft-merged"


def test_classify_alert_returns_operational_label() -> None:
    response = client.post(
        "/classify_alert",
        json={
            "message": "Unauthorized person detected near the north perimeter gate.",
            "source": "city-camera-7",
            "tags": ["perimeter", "motion"],
            "anomaly_score": 0.72,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "intrusion"
    assert payload["severity"] == "high"
    assert payload["requires_human_review"] is True


def test_summarize_event_builds_operator_summary() -> None:
    response = client.post(
        "/summarize_event",
        json={
            "title": "North Gate Alert",
            "classification": "intrusion",
            "severity": "high",
            "location": "North Gate",
            "alerts": [
                "Unauthorized person detected near restricted area",
                "Camera motion score exceeded threshold",
            ],
            "sensor_readings": {"motion_score": 0.91, "thermal_delta": 3.4},
            "max_sentences": 2,
        },
    )

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert "North Gate Alert" in summary
    assert "high severity" in summary
    assert "Unauthorized person detected" in summary


def test_detect_objects_returns_bounding_box_for_bright_region() -> None:
    image = Image.new("L", (20, 20), color=0)
    for x in range(5, 13):
        for y in range(6, 15):
            image.putpixel((x, y), 255)

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    response = client.post(
        "/detect_objects",
        json={
            "image_b64": __import__("base64").b64encode(buffer.getvalue()).decode("ascii"),
            "labels": ["vehicle"],
            "threshold": 0.55,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] in {"heuristic", "opencv", "yolo"}
    assert payload["requested_backend"] == "auto"
    assert payload["detections"]
    assert payload["detections"][0]["label"] == "vehicle"


def test_detect_objects_rejects_unknown_backend() -> None:
    image = Image.new("L", (20, 20), color=0)
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    response = client.post(
        "/detect_objects",
        json={
            "image_b64": __import__("base64").b64encode(buffer.getvalue()).decode("ascii"),
            "backend": "unsupported-backend",
        },
    )

    assert response.status_code == 400
    assert "Unsupported detection backend" in response.json()["detail"]


def test_detect_objects_returns_service_unavailable_for_missing_yolo() -> None:
    image = Image.new("L", (20, 20), color=0)
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    response = client.post(
        "/detect_objects",
        json={
            "image_b64": __import__("base64").b64encode(buffer.getvalue()).decode("ascii"),
            "backend": "yolo",
        },
    )

    assert response.status_code == 503