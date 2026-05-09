from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_action_register_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_action_register.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_action_register_payload(" not in source
    assert "def _register_action(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_action_register_common" in source
    assert "ui_semantic_validator_handoff_clearance_action_register_rows" in source
    assert "ui_semantic_validator_handoff_clearance_action_register_payload" in source


def test_clearance_action_register_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_action_register_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_action_register_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_action_register_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {
        "_action_state",
        "_action_type",
        "_operator_action",
        "_completion_gate",
        "_verification_hint",
        "_register_action",
        "_sort_action",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_action_register_payload",
        "build_ui_semantic_validator_handoff_clearance_action_register_latest_payload",
    }


def test_clearance_action_register_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_action_register as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_action_register_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_action_register_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_action_register import (
        _action_state,
        _action_type,
        _matches,
        _register_action,
        _sort_action,
    )

    assert callable(_action_state)
    assert callable(_action_type)
    assert callable(_register_action)
    assert callable(_sort_action)
    assert callable(_matches)


def test_clearance_action_register_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_action_register as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_operations_board_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-operations/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "operation_cards": [
                {
                    "operation_card_id": "operation-monkeypatch",
                    "operation_state": "EXTERNAL_ARTIFACT_OPERATION",
                    "evidence_lane": "EXTERNAL_ARTIFACT",
                    "coverage_status": "NEEDS_OPERATOR_REVIEW",
                    "highest_priority": "P1",
                    "highest_severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": ["EXTERNAL_ARTIFACT_MISSING"],
                    "requires_external_artifact": True,
                    "operator_attention_required": True,
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_action_register_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-operations/v1"
    assert payload["summary"]["action_count_returned"] == 1
    assert payload["action_rows"][0]["action_state"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["action_rows"][0]["external_artifact_write_authority"] == "none_read_plane"
