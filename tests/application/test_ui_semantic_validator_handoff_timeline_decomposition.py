from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _stage(stage: str, *, present: bool = True, ready: bool = True, issue_codes: list[str] | None = None) -> dict[str, object]:
    return {
        "stage": stage,
        "label": stage.title(),
        "route": f"/ui/semantic-validator-handoff/{stage}",
        "record_id": f"{stage}-1" if present else None,
        "digest": f"{stage}-digest" if present else None,
        "present": present,
        "ready": ready,
        "status": "PRESENT" if stage != "closure" else "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
        "issue_codes": issue_codes or [],
    }


def test_semantic_validator_handoff_timeline_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_timeline.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_timeline_payload(" not in source
    assert "def _timeline_event(" not in source
    assert "def _event_state(" not in source
    assert "ui_semantic_validator_handoff_timeline_common" in source
    assert "ui_semantic_validator_handoff_timeline_rows" in source
    assert "ui_semantic_validator_handoff_timeline_payload" in source


def test_semantic_validator_handoff_timeline_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_timeline_common.py")
    rows = _function_names("ui_semantic_validator_handoff_timeline_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_timeline_payload.py")

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
    assert rows == {
        "_event_state",
        "_event_severity",
        "_operator_focus",
        "_timeline_event",
        "_timeline_events",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_timeline_payload",
        "build_ui_semantic_validator_handoff_timeline_latest_payload",
    }


def test_semantic_validator_handoff_timeline_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_timeline as facade
    from strategy_validator.application import ui_semantic_validator_handoff_timeline_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_timeline_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_timeline import (
        _event_severity,
        _event_state,
        _haystack,
        _matches,
        _operator_focus,
        _timeline_event,
        _timeline_events,
    )

    assert callable(_event_state)
    assert callable(_event_severity)
    assert callable(_operator_focus)
    assert callable(_timeline_event)
    assert callable(_timeline_events)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_timeline_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_timeline as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_continuity_payload",
        lambda **_: {
            "schema_version": "synthetic-continuity/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"continuity_count_total": 1},
            "continuity_rows": [
                {
                    "continuity_id": "continuity-1",
                    "experiment_id": "EXP-TIMELINE",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest",
                    "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION",
                    "current_stage": "closure",
                    "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
                    "trust_banner": "TRUST_RESTRICTED",
                    "open_action": True,
                    "external_artifact_required": True,
                    "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation",
                    "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1",
                    "stage_path": [
                        _stage("decision"),
                        _stage("closure", ready=False, issue_codes=["EXTERNAL_CLOSURE_ATTESTATION_MISSING"]),
                    ],
                    "continuity_route": "/ui/semantic-validator-handoff/continuity",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_timeline_payload(event_state=("AWAITING_EXTERNAL_ARTIFACT",))

    assert payload["source_schema_version"] == "synthetic-continuity/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["timeline_event_count_returned"] == 1
    row = payload["timeline_events"][0]
    assert row["experiment_id"] == "EXP-TIMELINE"
    assert row["stage"] == "closure"
    assert row["event_state"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["authority"]["execution_allowed"] is False
