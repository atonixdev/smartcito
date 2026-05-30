import json
from pathlib import Path

import yaml


def test_rbac_policy_has_default_deny_rule() -> None:
    policy_path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "security_domain"
        / "rbac"
        / "policies.yaml"
    )
    data = yaml.safe_load(policy_path.read_text())

    rule_ids = {rule["id"] for rule in data["policy_rules"]}
    assert "deny-by-default" in rule_ids


def test_admin_inherits_operator_permissions() -> None:
    policy_path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "security_domain"
        / "rbac"
        / "policies.yaml"
    )
    data = yaml.safe_load(policy_path.read_text())

    roles = data["roles"]
    assert "operator" in roles["admin"]["inherits"]
    assert roles["admin"]["mfa_required"] is True
