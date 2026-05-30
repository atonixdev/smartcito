import json
from pathlib import Path


def test_audit_schema_has_hash_chain() -> None:
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "security_domain"
        / "audit"
        / "audit_log_schema.json"
    )
    schema = json.loads(schema_path.read_text())

    assert "hash_chain" in schema["required"]
    assert schema["properties"]["hash_chain"]["properties"]["algorithm"]["enum"] == [
        "sha-256"
    ]


def test_audit_schema_requires_actor_and_request() -> None:
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "security_domain"
        / "audit"
        / "audit_log_schema.json"
    )
    schema = json.loads(schema_path.read_text())

    required = set(schema["required"])
    assert {"actor", "request"}.issubset(required)
