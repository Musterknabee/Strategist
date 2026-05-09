from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_verification_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_verification_board.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_verification_board_payload(" not in source
    assert "def _card(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_verification_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_verification_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_verification_board_payload" in source


def test_clearance_verification_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_verification_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_verification_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_verification_board_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_as_list",
        "_norm_set",
        "_contains",
        "_digest",
        "_counts",
        "_authority",
    } <= common
    assert rows == {
        "_verification_status",
        "_verification_result",
        "_verification_note",
        "_verification_gate",
        "_card",
        "_sort_card",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_verification_board_payload",
        "build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload",
    }


def test_clearance_verification_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_verification_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_verification_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_verification_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_verification_board import (
        _card,
        _matches,
        _sort_card,
        _verification_gate,
        _verification_note,
        _verification_result,
        _verification_status,
    )

    assert callable(_verification_status)
    assert callable(_verification_result)
    assert callable(_verification_note)
    assert callable(_verification_gate)
    assert callable(_card)
    assert callable(_sort_card)
    assert callable(_matches)


def test_clearance_verification_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_verification_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload",
        lambda **_: {
            "schema_version": "synthetic-resolution-plan/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "resolution_steps": [
                {
                    "resolution_step_id": "resolution-monkeypatch",
                    "phase": "AUTHORIZED_CLEARANCE_REVIEW",
                    "evidence_lane": "AUTHORIZED_REVIEW",
                    "step_state": "READY_FOR_AUTHORIZED_CLEARANCE_REVIEW",
                    "action_state": "READY_REVIEW_CANDIDATE",
                    "action_type": "REVIEW_READY_COVERAGE",
                    "operation_state": "OPERATOR_REVIEW_OPERATION",
                    "action_group": "OPERATOR_REVIEW",
                    "coverage_status": "OBSERVED_COVERED",
                    "coverage_percent": 100,
                    "priority": "P3",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-VERIFY"],
                    "ready_for_operator_clearance_review": True,
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_verification_board_payload()

    assert payload["source_schema_version"] == "synthetic-resolution-plan/v1"
    assert payload["summary"]["verification_card_count_returned"] == 1
    assert payload["verification_cards"][0]["verification_status"] == "READY_FOR_AUTHORIZED_REVIEW_OBSERVED"
    assert payload["verification_cards"][0]["verification_write_authority"] == "none_read_plane"
    assert payload["verification_cards"][0]["completion_assertion_authority"] == "none_read_plane"
