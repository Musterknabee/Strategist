from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_release_readiness_ops import (
    build_research_os_release_readiness_report,
    build_and_write_research_os_release_readiness_report,
    build_ui_research_os_release_readiness_latest_payload,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_release_readiness_missing_inputs_is_not_ready(tmp_path: Path) -> None:
    report = build_research_os_release_readiness_report(artifact_root=tmp_path, report_id="missing")
    assert report.status.value in {"NOT_READY", "EMPTY"}
    assert report.release_review_ready is False
    assert report.deployment_approved is False
    assert report.no_live_trading is True


def test_release_readiness_blocks_open_p1_remediation(tmp_path: Path) -> None:
    _write(tmp_path / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {"gate_id": "g1", "decision": "PASS", "blockers": [], "warnings": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_remediation/latest/research_os_remediation_plan.json", {"plan_id": "r1", "open_count": 1, "blocked_count": 0, "waived_count": 0, "items": [{"priority": "P1", "status": "OPEN", "title": "missing evidence"}]})
    _write(tmp_path / "research_os_operator_runs/latest/research_os_operator_run_manifest.json", {"run_id": "run1", "status": "COMPLETE", "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json", {"catalog_id": "c1", "status": "READY", "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    report = build_research_os_release_readiness_report(artifact_root=tmp_path, report_id="p1")
    assert report.release_review_ready is False
    assert report.p1_open_count == 1
    assert any("OPEN_P1" in b for b in report.blockers)


def test_release_readiness_warn_with_active_exception_is_restricted_review(tmp_path: Path) -> None:
    _write(tmp_path / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {"gate_id": "g1", "decision": "WARN", "blockers": [], "warnings": ["RESTRICTED"], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_exceptions/latest/research_os_exception_record.json", {"exception_id": "e1", "status": "ACTIVE", "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_remediation/latest/research_os_remediation_plan.json", {"plan_id": "r1", "open_count": 2, "blocked_count": 0, "waived_count": 0, "items": [{"priority": "P2", "status": "OPEN"}, {"priority": "P3", "status": "OPEN"}], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_operator_runs/latest/research_os_operator_run_manifest.json", {"run_id": "run1", "status": "RESTRICTED", "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json", {"catalog_id": "c1", "status": "RESTRICTED", "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    _write(tmp_path / "research_os_drift/latest/research_os_drift_report.json", {"drift_id": "d1", "status": "RESTRICTED", "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "deployment_approval_unchanged": True})
    report = build_research_os_release_readiness_report(artifact_root=tmp_path, report_id="restricted")
    assert report.status.value == "RESTRICTED_REVIEW"
    assert report.decision.value == "REVIEW_WITH_RESTRICTIONS"
    assert report.release_review_ready is True
    assert report.deployment_approved is False


def test_release_readiness_ui_payload(tmp_path: Path) -> None:
    report, _ = build_and_write_research_os_release_readiness_report(artifact_root=tmp_path, report_id="ui", overwrite=True)
    payload = build_ui_research_os_release_readiness_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["report_id"] == report.report_id
