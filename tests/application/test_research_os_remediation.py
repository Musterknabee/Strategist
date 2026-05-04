from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_remediation_ops import (
    build_research_os_remediation_plan,
    build_and_write_research_os_remediation_plan,
    build_ui_research_os_remediation_latest_payload,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_remediation_plan_builds_from_warn_policy_gate(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {
        "schema_version": "research_os_policy_gate_report/v1",
        "gate_id": "gate-1",
        "decision": "WARN",
        "trust_banner": "TRUST_RESTRICTED",
        "warnings": ["MISSING_PROVIDER_PAPER_LOOP_LATEST_ARTIFACT"],
        "blockers": [],
        "recommended_operator_actions": ["Run provider paper loop demo"],
        "rules": [],
    })
    _write(root / "research_os_exceptions/latest/research_os_exception_record.json", {
        "schema_version": "research_os_exception_record/v1",
        "exception_id": "exception-1",
        "status": "ACTIVE",
        "decision": "GRANTED_WITH_RESTRICTIONS",
        "recommended_followups": ["Resolve provider loop"],
        "residual_warnings": [],
        "residual_blockers": [],
    })
    _write(root / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json", {
        "schema_version": "research_os_evidence_catalog/v1",
        "catalog_id": "catalog-1",
        "latest_by_category": {},
        "warnings": [],
        "blockers": [],
    })
    _write(root / "research_os_drift/latest/research_os_drift_report.json", {
        "schema_version": "research_os_drift_report/v1",
        "drift_id": "drift-1",
        "changed_count": 1,
        "removed_count": 0,
        "added_count": 0,
        "warnings": [],
        "blockers": [],
    })
    plan = build_research_os_remediation_plan(plan_id="plan-1", artifact_root=root)
    assert plan.status.value == "RESTRICTED"
    assert plan.item_count >= 1
    assert plan.manifest_sha256
    assert any(item.category.value == "PROVIDER_LOOP" for item in plan.items)


def test_remediation_ui_payload_empty_root_degrades(tmp_path: Path) -> None:
    payload = build_ui_research_os_remediation_latest_payload(artifact_root=tmp_path / "artifacts")
    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_REMEDIATION_PLAN" in payload["degraded"]


def test_remediation_write_and_latest_payload(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {
        "schema_version": "research_os_policy_gate_report/v1",
        "gate_id": "gate-pass",
        "decision": "PASS",
        "trust_banner": "TRUSTED",
        "warnings": [],
        "blockers": [],
        "rules": [],
    })
    plan, path = build_and_write_research_os_remediation_plan(plan_id="plan-pass", artifact_root=root, overwrite=True)
    assert path.is_file()
    payload = build_ui_research_os_remediation_latest_payload(artifact_root=root)
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["plan_id"] == plan.plan_id
