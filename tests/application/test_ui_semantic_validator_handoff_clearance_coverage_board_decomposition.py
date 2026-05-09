from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_coverage_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_coverage_board.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_coverage_board_payload(" not in source
    assert "def _board_card(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_coverage_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_coverage_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_coverage_board_payload" in source


def test_clearance_coverage_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_coverage_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_coverage_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_coverage_board_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {"_status", "_coverage_percent", "_highest", "_operator_instruction", "_board_card", "_sort_card", "_haystack", "_matches", "_cards_from_rows", "_degraded"}
    assert payload == {"_source_builder", "build_ui_semantic_validator_handoff_clearance_coverage_board_payload", "build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload"}


def test_clearance_coverage_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_coverage_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_coverage_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_coverage_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_coverage_board import _board_card, _cards_from_rows, _matches, _sort_card, _status

    assert callable(_status)
    assert callable(_board_card)
    assert callable(_cards_from_rows)
    assert callable(_sort_card)
    assert callable(_matches)


def test_clearance_coverage_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_coverage_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-evidence-matrix/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "evidence_rows": [
                {
                    "evidence_matrix_row_id": "row-monkeypatch",
                    "evidence_lane": "EXTERNAL_ARTIFACT",
                    "evidence_state": "WAITING_EXTERNAL_ARTIFACT",
                    "attention_required": True,
                    "blocks_clearance": False,
                    "requires_external_artifact": True,
                    "check_id": "external_artifact_gap_absent",
                    "source_route": "/ui/semantic-validator-handoff/clearance-gate",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_coverage_board_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-evidence-matrix/v1"
    assert payload["summary"]["coverage_card_count_returned"] == 1
    assert payload["coverage_cards"][0]["coverage_status"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["coverage_cards"][0]["external_artifact_write_authority"] == "none_read_plane"
