from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_review_docket_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_review_docket.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_review_docket_payload(" not in source
    assert "def _docket_from_card(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_review_docket_common" in source
    assert "ui_semantic_validator_handoff_clearance_review_docket_rows" in source
    assert "ui_semantic_validator_handoff_clearance_review_docket_payload" in source


def test_clearance_review_docket_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_review_docket_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_review_docket_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_review_docket_payload.py")

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
        "_authority",
    } <= common
    assert rows == {
        "_docket_status",
        "_docket_readiness",
        "_review_gate",
        "_review_instruction",
        "_docket_from_card",
        "_sort_docket",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_review_docket_payload",
        "build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload",
    }


def test_clearance_review_docket_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_review_docket as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_review_docket_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_review_docket_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_review_docket import (
        _docket_from_card,
        _docket_readiness,
        _docket_status,
        _matches,
        _review_gate,
        _review_instruction,
        _sort_docket,
    )

    assert callable(_docket_status)
    assert callable(_docket_readiness)
    assert callable(_review_gate)
    assert callable(_review_instruction)
    assert callable(_docket_from_card)
    assert callable(_sort_docket)
    assert callable(_matches)


def test_clearance_review_docket_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_review_docket as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_closeout_board_payload",
        lambda **_: {
            "schema_version": "synthetic-closeout-board/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "closeout_cards": [
                {
                    "closeout_card_id": "closeout-monkeypatch",
                    "evidence_lane": "AUTHORIZED_REVIEW",
                    "closeout_status": "CLEARANCE_CLOSEOUT_READY_FOR_AUTHORIZED_REVIEW",
                    "closeout_readiness": "REVIEW_READY_OBSERVATION",
                    "ready_for_authorized_clearance_review": True,
                    "priority": "P2",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-REVIEW"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_review_docket_payload()

    assert payload["source_schema_version"] == "synthetic-closeout-board/v1"
    assert payload["summary"]["review_docket_count_returned"] == 1
    assert payload["review_dockets"][0]["docket_readiness"] == "AUTHORIZED_REVIEW_OBSERVATION"
    assert payload["review_dockets"][0]["review_record_write_authority"] == "none_read_plane"
    assert payload["review_dockets"][0]["review_authorization_authority"] == "none_read_plane"
