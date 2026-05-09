from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_runbook_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_runbook.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_runbook_payload(" not in source
    assert "def _runbook_card(" not in source
    assert "def _checklist(" not in source
    assert "ui_semantic_validator_handoff_runbook_common" in source
    assert "ui_semantic_validator_handoff_runbook_rows" in source
    assert "ui_semantic_validator_handoff_runbook_payload" in source


def test_semantic_validator_handoff_runbook_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_runbook_common.py")
    rows = _function_names("ui_semantic_validator_handoff_runbook_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_runbook_payload.py")

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
        "_template_fields",
        "_first_issue",
        "_checklist",
        "_runbook_decision",
        "_runbook_card",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_runbook_payload",
        "build_ui_semantic_validator_handoff_runbook_latest_payload",
    }


def test_semantic_validator_handoff_runbook_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_runbook as facade
    from strategy_validator.application import ui_semantic_validator_handoff_runbook_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_runbook_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_runbook import (
        _checklist,
        _first_issue,
        _haystack,
        _matches,
        _runbook_card,
        _runbook_decision,
        _template_fields,
    )

    assert callable(_template_fields)
    assert callable(_first_issue)
    assert callable(_checklist)
    assert callable(_runbook_decision)
    assert callable(_runbook_card)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_runbook_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_runbook as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_continuity_payload",
        lambda **_: {
            "schema_version": "synthetic-continuity/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"continuity_count_total": 1, "open_action_count": 1},
            "continuity_rows": [
                {
                    "continuity_id": "continuity-1",
                    "experiment_id": "EXP-RUNBOOK",
                    "terminal_status": "AWAITING_EXTERNAL_CLOSURE_ATTESTATION",
                    "current_stage": "closure",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest",
                    "closure_gate_id": "closure-1",
                    "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
                    "closure_packet_digest": "closure-digest",
                    "archive_gate_id": "archive-1",
                    "decision_id": "decision-1",
                    "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
                    "stage_count_expected": 5,
                    "stage_count_present": 5,
                    "ready_stage_count": 4,
                    "open_action": True,
                    "external_artifact_required": True,
                    "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation",
                    "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1",
                    "closure_template": {
                        "schema_version": "semantic_validator_handoff_closure_attestation/v1",
                        "closure_packet_digest": "closure-digest",
                        "closed_by": "<REQUIRED_EXTERNALLY>",
                        "closure_statement": "<REQUIRED_EXTERNALLY>",
                    },
                    "recommended_action": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
                    "source_route": "/ui/semantic-validator-handoff/closure",
                    "continuity_route": "/ui/semantic-validator-handoff/continuity",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_runbook_payload(action_kind=("CREATE_EXTERNAL_CLOSURE_ATTESTATION",))

    assert payload["source_schema_version"] == "synthetic-continuity/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["runbook_card_count_returned"] == 1
    assert payload["summary"]["open_runbook_card_count"] == 1
    card = payload["runbook_cards"][0]
    assert card["action_kind"] == "CREATE_EXTERNAL_CLOSURE_ATTESTATION"
    assert card["priority"] == "P1"
    assert card["severity"] == "WARN"
    assert "closed_by" in card["required_template_fields"]
    assert card["authority"]["execution_allowed"] is False
    assert payload["validator_submission_authority"] == "none_read_plane"
