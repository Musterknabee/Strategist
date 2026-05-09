from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_closeout_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_closeout_board.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_closeout_board_payload(" not in source
    assert "def _card(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_closeout_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_closeout_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_closeout_board_payload" in source


def test_clearance_closeout_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_closeout_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_closeout_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_closeout_board_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_as_list",
        "_uniq",
        "_norm_set",
        "_contains",
        "_digest",
        "_counts",
        "_best_priority",
        "_best_severity",
        "_authority",
    } <= common
    assert rows == {
        "_closeout_status",
        "_readiness",
        "_closeout_gate",
        "_closeout_note",
        "_card",
        "_sort_card",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_closeout_board_payload",
        "build_ui_semantic_validator_handoff_clearance_closeout_board_latest_payload",
    }


def test_clearance_closeout_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_closeout_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_closeout_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_closeout_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_closeout_board import (
        _card,
        _closeout_gate,
        _closeout_note,
        _closeout_status,
        _matches,
        _readiness,
        _sort_card,
    )

    assert callable(_closeout_status)
    assert callable(_readiness)
    assert callable(_closeout_gate)
    assert callable(_closeout_note)
    assert callable(_card)
    assert callable(_sort_card)
    assert callable(_matches)


def test_clearance_closeout_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_closeout_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_verification_board_payload",
        lambda **_: {
            "schema_version": "synthetic-verification-board/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "verification_cards": [
                {
                    "verification_card_id": "verification-monkeypatch",
                    "verification_status": "READY_FOR_AUTHORIZED_REVIEW_OBSERVED",
                    "verification_result": "REVIEW_OBSERVATION",
                    "verification_passed": True,
                    "evidence_lane": "AUTHORIZED_REVIEW",
                    "priority": "P3",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-CLOSEOUT"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_closeout_board_payload()

    assert payload["source_schema_version"] == "synthetic-verification-board/v1"
    assert payload["summary"]["closeout_card_count_returned"] == 1
    assert payload["closeout_cards"][0]["closeout_status"] == "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW"
    assert payload["closeout_cards"][0]["closeout_write_authority"] == "none_read_plane"
    assert payload["closeout_cards"][0]["clearance_decision_authority"] == "none_read_plane"
