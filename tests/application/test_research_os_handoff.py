from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_handoff_ops import (
    build_and_write_research_os_handoff_pack,
    build_research_os_handoff_pack,
    build_ui_research_os_handoff_latest_payload,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _seed(root: Path) -> None:
    _write(root / "research_os_release_readiness/latest/research_os_release_readiness_report.json", {
        "schema_version": "research_os_release_readiness_report/v1",
        "report_id": "r1",
        "status": "RESTRICTED_REVIEW",
        "decision": "REVIEW_WITH_RESTRICTIONS",
        "release_review_ready": True,
        "deployment_approved": False,
        "deployment_approval_unchanged": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "no_profitability_claim": True,
        "manifest_sha256": "release-sha",
        "warnings": ["restricted"],
        "blockers": [],
    })
    _write(root / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {"schema_version": "research_os_policy_gate_report/v1", "gate_id": "g1", "decision": "WARN", "manifest_sha256": "gate-sha", "warnings": ["warn"], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})
    _write(root / "research_os_exceptions/latest/research_os_exception_record.json", {"schema_version": "research_os_exception_record/v1", "exception_id": "e1", "status": "ACTIVE", "constraints": ["paper only"], "manifest_sha256": "exception-sha", "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})
    _write(root / "research_os_remediation/latest/research_os_remediation_plan.json", {"schema_version": "research_os_remediation_plan/v1", "plan_id": "m1", "status": "RESTRICTED", "manifest_sha256": "rem-sha", "recommended_next_actions": ["fix provider loop"], "warnings": ["open p2"], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})
    _write(root / "research_os_exports/latest/research_os_export_manifest.json", {"schema_version": "research_os_export_manifest/v1", "export_id": "x1", "status": "RESTRICTED", "manifest_sha256": "export-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})
    _write(root / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json", {"schema_version": "research_os_evidence_catalog/v1", "catalog_id": "c1", "status": "RESTRICTED", "manifest_sha256": "cat-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})
    _write(root / "research_os_operator_runs/latest/research_os_operator_run_manifest.json", {"schema_version": "research_os_operator_run_manifest/v1", "run_id": "o1", "status": "RESTRICTED", "manifest_sha256": "run-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True})


def test_handoff_restricted_warn_with_active_exception(tmp_path: Path) -> None:
    _seed(tmp_path)
    pack = build_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="h1")
    assert pack.status.value == "RESTRICTED"
    assert pack.decision.value == "HANDOFF_WITH_RESTRICTIONS"
    assert pack.handoff_ready is True
    assert pack.deployment_approved is False
    assert pack.no_live_trading is True
    assert pack.manifest_sha256


def test_handoff_missing_inputs_not_ready(tmp_path: Path) -> None:
    pack = build_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="missing")
    assert pack.status.value in {"EMPTY", "NOT_READY", "BLOCKED"}
    assert pack.handoff_ready is False
    assert pack.blockers


def test_handoff_write_and_ui_payload(tmp_path: Path) -> None:
    _seed(tmp_path)
    pack, path = build_and_write_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="h2", overwrite=True)
    assert path.is_file()
    payload = build_ui_research_os_handoff_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["handoff_id"] == pack.handoff_id
