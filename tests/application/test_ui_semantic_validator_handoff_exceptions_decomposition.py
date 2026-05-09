from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_exceptions_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_exceptions.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_exceptions_payload(" not in source
    assert "def _exception_row(" not in source
    assert "def _exception_kind(" not in source
    assert "ui_semantic_validator_handoff_exceptions_common" in source
    assert "ui_semantic_validator_handoff_exceptions_rows" in source
    assert "ui_semantic_validator_handoff_exceptions_payload" in source


def test_semantic_validator_handoff_exceptions_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_exceptions_common.py")
    rows = _function_names("ui_semantic_validator_handoff_exceptions_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_exceptions_payload.py")

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
        "_exception_kind",
        "_exception_state",
        "_escalation_lane",
        "_exception_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_exceptions_payload",
        "build_ui_semantic_validator_handoff_exceptions_latest_payload",
    }


def test_semantic_validator_handoff_exceptions_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_exceptions as facade
    from strategy_validator.application import ui_semantic_validator_handoff_exceptions_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_exceptions_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_exceptions import (
        _escalation_lane,
        _exception_kind,
        _exception_row,
        _exception_state,
        _haystack,
        _matches,
    )

    assert callable(_exception_kind)
    assert callable(_exception_state)
    assert callable(_escalation_lane)
    assert callable(_exception_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_exceptions_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_exceptions as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_runbook_payload",
        lambda **_: {
            "schema_version": "synthetic-runbook/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"runbook_card_count_total": 1, "open_runbook_card_count": 1},
            "runbook_cards": [
                {
                    "runbook_card_id": "runbook-1",
                    "continuity_id": "continuity-1",
                    "experiment_id": "EXP-EXCEPTION",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest",
                    "closure_gate_id": "closure-1",
                    "archive_gate_id": "archive-1",
                    "decision_id": "decision-1",
                    "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION",
                    "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
                    "current_stage": "closure",
                    "action_kind": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
                    "priority": "P1",
                    "severity": "WARN",
                    "completed": False,
                    "blocked": False,
                    "external_artifact_required": True,
                    "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation",
                    "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1",
                    "required_template_fields": ["closed_by", "closure_statement"],
                    "first_issue_code": "EXTERNAL_CLOSURE_ATTESTATION_MISSING",
                    "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
                    "operator_action": "Create external closure attestation",
                    "checklist": ["Inspect row", "Repair externally"],
                    "next_route": "/ui/semantic-validator-handoff/closure",
                    "continuity_route": "/ui/semantic-validator-handoff/continuity",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_exceptions_payload(exception_state=("AWAITING_EXTERNAL_ARTIFACT",))

    assert payload["source_schema_version"] == "synthetic-runbook/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["exception_count_returned"] == 1
    assert payload["summary"]["open_exception_count"] == 1
    row = payload["exception_rows"][0]
    assert row["experiment_id"] == "EXP-EXCEPTION"
    assert row["exception_state"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["exception_kind"] == "EXTERNAL_ARTIFACT_REQUIRED_EXCEPTION"
    assert row["escalation_lane"] == "operator_external_attestation"
    assert row["authority"]["validator_submission_allowed"] is False
    assert payload["execution_authority"] == "none_read_plane"
