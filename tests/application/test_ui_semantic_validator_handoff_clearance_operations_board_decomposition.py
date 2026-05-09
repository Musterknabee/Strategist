from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_operations_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_operations_board.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_operations_board_payload(" not in source
    assert "def _operation_card(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_operations_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_operations_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_operations_board_payload" in source


def test_clearance_operations_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_operations_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_operations_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_operations_board_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {
        "_operation_state",
        "_action_group",
        "_next_safe_action",
        "_source_row_values",
        "_operation_card",
        "_sort_card",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_operations_board_payload",
        "build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload",
    }


def test_clearance_operations_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_operations_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_operations_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_operations_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_operations_board import (
        _action_group,
        _matches,
        _operation_card,
        _operation_state,
        _sort_card,
    )

    assert callable(_operation_state)
    assert callable(_action_group)
    assert callable(_operation_card)
    assert callable(_sort_card)
    assert callable(_matches)


def test_clearance_operations_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_operations_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_coverage_board_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-coverage/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "coverage_cards": [
                {
                    "coverage_card_id": "coverage-monkeypatch",
                    "evidence_lane": "EXTERNAL_ARTIFACT",
                    "coverage_status": "WAITING_EXTERNAL_ARTIFACT",
                    "coverage_percent": 0,
                    "row_count": 1,
                    "highest_priority": "P1",
                    "highest_severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": ["EXTERNAL_ARTIFACT_MISSING"],
                    "requires_external_artifact": True,
                    "source_evidence_rows": [{"experiment_id": "EXP-MONKEY"}],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_operations_board_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-coverage/v1"
    assert payload["summary"]["operation_card_count_returned"] == 1
    assert payload["operation_cards"][0]["operation_state"] == "EXTERNAL_ARTIFACT_OPERATION"
    assert payload["operation_cards"][0]["external_artifact_write_authority"] == "none_read_plane"
