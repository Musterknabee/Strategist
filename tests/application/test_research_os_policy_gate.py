from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_policy_gate_ops import build_research_os_policy_gate_report


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _minimal_spine(root: Path) -> None:
    safe = {
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "no_profitability_claim": True,
        "deployment_approval_unchanged": True,
        "warnings": [],
        "blockers": [],
    }
    _write(root / "research_os_operator_runs/latest/research_os_operator_run_manifest.json", {**safe, "schema_version": "research_os_operator_run_manifest/v1", "status": "COMPLETE", "trust_banner": "TRUSTED"})
    _write(root / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json", {**safe, "schema_version": "research_os_evidence_catalog/v1", "status": "READY", "trust_banner": "TRUSTED", "entries": []})
    _write(root / "research_os_closure/latest/research_os_closure_manifest.json", {**safe, "schema_version": "research_os_closure_manifest/v1", "status": "COMPLETE", "trust_banner": "TRUSTED"})
    _write(root / "research_os_attestation/latest/closure_verification_result.json", {**safe, "schema_version": "research_os_closure_verification_result/v1", "status": "VERIFIED", "trust_banner": "TRUSTED"})
    _write(root / "research_os_attestation/latest/operator_attestation.json", {**safe, "schema_version": "research_os_operator_attestation/v1", "decision": "ACKNOWLEDGED", "verification_status": "VERIFIED", "trust_banner": "TRUSTED"})
    _write(root / "research_os_briefings/latest/research_os_briefing_pack.json", {**safe, "schema_version": "research_os_briefing_pack/v1", "status": "READY", "trust_banner": "TRUSTED"})
    _write(root / "research_os_exports/latest/research_os_export_manifest.json", {**safe, "schema_version": "research_os_export_manifest/v1", "status": "READY", "trust_banner": "TRUSTED"})
    _write(root / "research_os_drift/latest/research_os_drift_report.json", {**safe, "schema_version": "research_os_evidence_drift_report/v1", "status": "READY", "trust_banner": "TRUSTED", "added_count": 0, "removed_count": 0, "changed_count": 0})


def test_policy_gate_passes_minimal_trusted_spine(tmp_path: Path) -> None:
    _minimal_spine(tmp_path)
    report = build_research_os_policy_gate_report(gate_id="pass", artifact_root=tmp_path)
    assert report.decision.value == "PASS"
    assert report.blocker_count == 0
    assert report.manifest_sha256


def test_policy_gate_warns_on_restricted_evidence(tmp_path: Path) -> None:
    _minimal_spine(tmp_path)
    p = tmp_path / "research_os_evidence_catalog/latest/research_os_evidence_catalog.json"
    raw = json.loads(p.read_text())
    raw["status"] = "RESTRICTED"
    raw["trust_banner"] = "TRUST_RESTRICTED"
    raw["warnings"] = ["PARTIAL_ARTIFACT_ROOT"]
    _write(p, raw)
    report = build_research_os_policy_gate_report(gate_id="warn", artifact_root=tmp_path)
    assert report.decision.value == "WARN"
    assert any("restricted_evidence_review" == r.rule_id and r.status.value == "WARN" for r in report.rules)


def test_policy_gate_blocks_false_safety_flag(tmp_path: Path) -> None:
    _minimal_spine(tmp_path)
    p = tmp_path / "research_os_operator_runs/latest/research_os_operator_run_manifest.json"
    raw = json.loads(p.read_text())
    raw["no_broker_orders"] = False
    _write(p, raw)
    report = build_research_os_policy_gate_report(gate_id="block", artifact_root=tmp_path)
    assert report.decision.value == "BLOCK"
    assert any("SAFETY_FLAG_FALSE" in b for b in report.blockers)
