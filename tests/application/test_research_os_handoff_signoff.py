from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_handoff_ops import build_and_write_research_os_handoff_pack
from strategy_validator.application.research_os_handoff_signoff_ops import (
    build_and_write_research_os_handoff_reviewer_signoff,
    build_and_write_research_os_handoff_verification_result,
    build_research_os_handoff_verification_result,
    build_ui_research_os_handoff_signoff_latest_payload,
)
from strategy_validator.contracts.research_os_handoff_signoff import ResearchOsHandoffReviewerDecision


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _seed(root: Path) -> None:
    rows = {
        "research_os_release_readiness/latest/research_os_release_readiness_report.json": {"schema_version": "research_os_release_readiness_report/v1", "report_id": "r1", "status": "RESTRICTED_REVIEW", "decision": "REVIEW_WITH_RESTRICTIONS", "release_review_ready": True, "deployment_approved": False, "deployment_approval_unchanged": True, "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "no_profitability_claim": True, "manifest_sha256": "release-sha", "warnings": ["restricted"], "blockers": []},
        "research_os_policy_gate/latest/research_os_policy_gate_report.json": {"schema_version": "research_os_policy_gate_report/v1", "gate_id": "g1", "decision": "WARN", "manifest_sha256": "gate-sha", "warnings": ["warn"], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_exceptions/latest/research_os_exception_record.json": {"schema_version": "research_os_exception_record/v1", "exception_id": "e1", "status": "ACTIVE", "constraints": ["paper only"], "manifest_sha256": "exception-sha", "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_remediation/latest/research_os_remediation_plan.json": {"schema_version": "research_os_remediation_plan/v1", "plan_id": "m1", "status": "RESTRICTED", "manifest_sha256": "rem-sha", "recommended_next_actions": ["fix provider loop"], "warnings": ["open p2"], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_exports/latest/research_os_export_manifest.json": {"schema_version": "research_os_export_manifest/v1", "export_id": "x1", "status": "RESTRICTED", "manifest_sha256": "export-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_evidence_catalog/latest/research_os_evidence_catalog.json": {"schema_version": "research_os_evidence_catalog/v1", "catalog_id": "c1", "status": "RESTRICTED", "manifest_sha256": "cat-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_operator_runs/latest/research_os_operator_run_manifest.json": {"schema_version": "research_os_operator_run_manifest/v1", "run_id": "o1", "status": "RESTRICTED", "manifest_sha256": "run-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_drift/latest/research_os_drift_report.json": {"schema_version": "research_os_drift_report/v1", "drift_id": "d1", "status": "RESTRICTED", "manifest_sha256": "drift-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_briefings/latest/research_os_briefing_pack.json": {"schema_version": "research_os_briefing_pack/v1", "briefing_id": "b1", "status": "READY", "manifest_sha256": "briefing-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_closure/latest/research_os_closure_manifest.json": {"schema_version": "research_os_closure_manifest/v1", "closure_id": "cl1", "status": "DEGRADED", "manifest_sha256": "closure-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
        "research_os_attestation/latest/operator_attestation.json": {"schema_version": "research_os_operator_attestation/v1", "attestation_id": "a1", "decision": "ACCEPTED_WITH_RESTRICTIONS", "manifest_sha256": "attestation-sha", "warnings": [], "blockers": [], "no_live_trading": True, "no_broker_orders": True, "no_order_controls": True, "deployment_approval_unchanged": True},
    }
    for rel, payload in rows.items():
        _write(root / rel, payload)


def test_handoff_verification_matches_seeded_sources(tmp_path: Path) -> None:
    _seed(tmp_path)
    build_and_write_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="h1", overwrite=True)
    result = build_research_os_handoff_verification_result(artifact_root=tmp_path, verification_id="v1")
    assert result.status.value in {"VERIFIED", "STALE"}
    assert result.source_handoff_id == "h1"
    assert result.mismatch_count == 0
    assert result.deployment_approved is False


def test_handoff_verification_detects_source_manifest_tamper(tmp_path: Path) -> None:
    _seed(tmp_path)
    build_and_write_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="h2", overwrite=True)
    path = tmp_path / "research_os_policy_gate/latest/research_os_policy_gate_report.json"
    raw = json.loads(path.read_text())
    raw["manifest_sha256"] = "changed"
    _write(path, raw)
    result = build_research_os_handoff_verification_result(artifact_root=tmp_path, verification_id="v2")
    assert result.status.value == "TAMPERED"
    assert result.mismatch_count >= 1
    assert any("SOURCE_MANIFEST_SHA256_MISMATCH" in b for b in result.blockers)


def test_handoff_signoff_writes_and_ui_payload(tmp_path: Path) -> None:
    _seed(tmp_path)
    build_and_write_research_os_handoff_pack(artifact_root=tmp_path, handoff_id="h3", overwrite=True)
    verification, _ = build_and_write_research_os_handoff_verification_result(artifact_root=tmp_path, verification_id="v3", overwrite=True)
    signoff, _ = build_and_write_research_os_handoff_reviewer_signoff(
        artifact_root=tmp_path,
        signoff_id="s3",
        reviewer_id="reviewer",
        decision=ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS,
        overwrite=True,
    )
    assert verification.result_sha256
    assert signoff.manifest_sha256
    assert signoff.deployment_approved is False
    payload = build_ui_research_os_handoff_signoff_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "PRESENT"
    assert payload["latest_signoff"]["signoff_id"] == "s3"
