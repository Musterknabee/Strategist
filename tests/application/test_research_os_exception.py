from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_exception_ops import (
    build_research_os_exception_record,
    build_ui_research_os_exception_latest_payload,
    write_research_os_exception_record,
)


def _write_policy_gate(root: Path, *, decision: str = "WARN") -> None:
    path = root / "research_os_policy_gate/latest/research_os_policy_gate_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    warnings = ["RULE_WARN:restricted_evidence_review"] if decision == "WARN" else []
    blockers = ["RULE_BLOCK:no_input_blockers"] if decision == "BLOCK" else []
    path.write_text(
        json.dumps(
            {
                "schema_version": "research_os_policy_gate_report/v1",
                "gate_id": f"gate-{decision.lower()}",
                "decision": decision,
                "trust_banner": "TRUST_RESTRICTED" if decision == "WARN" else "UNTRUSTED" if decision == "BLOCK" else "TRUSTED",
                "manifest_sha256": "a" * 64,
                "warnings": warnings,
                "blockers": blockers,
                "read_plane_only": True,
                "no_live_trading": True,
                "no_broker_orders": True,
                "no_order_controls": True,
                "no_profitability_claim": True,
                "deployment_approval_unchanged": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_warn_policy_gate_can_create_active_exception(tmp_path: Path) -> None:
    _write_policy_gate(tmp_path, decision="WARN")
    record = build_research_os_exception_record(
        exception_id="ex1",
        operator_id="operator",
        rationale="restricted evidence reviewed",
        ttl_hours=1,
        artifact_root=tmp_path,
    )
    assert record.status.value == "ACTIVE"
    assert record.decision.value == "GRANTED_WITH_RESTRICTIONS"
    assert record.no_live_trading is True
    assert record.no_broker_orders is True
    assert record.manifest_sha256


def test_block_policy_gate_rejects_exception(tmp_path: Path) -> None:
    _write_policy_gate(tmp_path, decision="BLOCK")
    record = build_research_os_exception_record(
        exception_id="ex2",
        operator_id="operator",
        rationale="cannot bypass blockers",
        ttl_hours=1,
        artifact_root=tmp_path,
    )
    assert record.status.value == "REJECTED"
    assert record.decision.value == "REJECTED_POLICY_BLOCK"
    assert record.residual_blockers


def test_exception_latest_payload_degrades_when_absent(tmp_path: Path) -> None:
    payload = build_ui_research_os_exception_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "NOT_PRESENT"
    assert "NO_RESEARCH_OS_EXCEPTION_RECORD" in payload["degraded"]


def test_written_exception_can_be_loaded_by_ui_payload(tmp_path: Path) -> None:
    _write_policy_gate(tmp_path, decision="WARN")
    record = build_research_os_exception_record(
        exception_id="ex3",
        operator_id="operator",
        rationale="write it",
        ttl_hours=1,
        artifact_root=tmp_path,
    )
    write_research_os_exception_record(record, artifact_root=tmp_path, overwrite=True)
    payload = build_ui_research_os_exception_latest_payload(artifact_root=tmp_path)
    assert payload["status"] == "PRESENT"
    assert payload["latest"]["exception_id"] == "ex3"
