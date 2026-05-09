from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _event(
    *,
    stage: str = "closure",
    event_state: str = "AWAITING_EXTERNAL_ARTIFACT",
    severity: str = "WARN",
    present: bool = True,
    ready: bool = False,
    blocking: bool = True,
    external_required: bool = True,
    issue_codes: list[str] | None = None,
) -> dict[str, object]:
    issues = issue_codes if issue_codes is not None else (["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if external_required else [])
    return {
        "timeline_event_id": f"event-{stage}-{event_state}",
        "continuity_id": "continuity-1",
        "experiment_id": "EXP-GAPS",
        "chain_id": "chain-1",
        "chain_digest": "chain-digest",
        "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION",
        "current_stage": stage,
        "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
        "stage": stage,
        "stage_label": stage.title(),
        "stage_position": 5 if stage == "closure" else 3,
        "stage_route": f"/ui/semantic-validator-handoff/{stage}",
        "stage_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
        "record_id": f"{stage}-1" if present else None,
        "digest": f"{stage}-digest" if present else None,
        "present": present,
        "ready": ready,
        "event_state": event_state,
        "severity": severity,
        "blocking": blocking,
        "external_artifact_required": external_required,
        "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_required else None,
        "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_required else None,
        "operator_focus": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
        "issue_codes": issues,
        "issue_count": len(issues),
        "continuity_route": "/ui/semantic-validator-handoff/continuity",
        "runbook_route": "/ui/semantic-validator-handoff/runbook",
        "exceptions_route": "/ui/semantic-validator-handoff/exceptions",
        "summary_line": "EXP-GAPS · closure · wait · execute=false",
    }


def test_semantic_validator_handoff_evidence_gaps_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_evidence_gaps.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_evidence_gaps_payload(" not in source
    assert "def _gap_row(" not in source
    assert "def _classify(" not in source
    assert "ui_semantic_validator_handoff_evidence_gaps_common" in source
    assert "ui_semantic_validator_handoff_evidence_gaps_rows" in source
    assert "ui_semantic_validator_handoff_evidence_gaps_payload" in source


def test_semantic_validator_handoff_evidence_gaps_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_evidence_gaps_common.py")
    rows = _function_names("ui_semantic_validator_handoff_evidence_gaps_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_evidence_gaps_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_as_list",
        "_norm_set",
        "_counts",
        "_contains",
        "_authority",
    } <= common
    assert rows == {"_classify", "_repair_route", "_checklist", "_gap_row", "_haystack", "_matches"}
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_evidence_gaps_payload",
        "build_ui_semantic_validator_handoff_evidence_gaps_latest_payload",
    }


def test_semantic_validator_handoff_evidence_gaps_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_evidence_gaps as facade
    from strategy_validator.application import ui_semantic_validator_handoff_evidence_gaps_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_evidence_gaps_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps import (
        _checklist,
        _classify,
        _gap_row,
        _haystack,
        _matches,
        _repair_route,
    )

    assert callable(_classify)
    assert callable(_repair_route)
    assert callable(_checklist)
    assert callable(_gap_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_evidence_gaps_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_evidence_gaps as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_timeline_payload",
        lambda **_: {
            "schema_version": "synthetic-timeline/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"timeline_event_count_total": 1},
            "timeline_events": [_event()],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_evidence_gaps_payload(gap_kind=("EXTERNAL_ARTIFACT_GAP",))

    assert payload["source_schema_version"] == "synthetic-timeline/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["gap_count_returned"] == 1
    row = payload["gap_rows"][0]
    assert row["experiment_id"] == "EXP-GAPS"
    assert row["stage"] == "closure"
    assert row["gap_kind"] == "EXTERNAL_ARTIFACT_GAP"
    assert row["authority"]["execution_allowed"] is False
