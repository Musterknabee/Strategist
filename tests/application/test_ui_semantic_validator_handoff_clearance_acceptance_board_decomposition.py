from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_acceptance_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_acceptance_board.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_acceptance_board_payload(" not in source
    assert "def _card_from_packet(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_acceptance_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_acceptance_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_acceptance_board_payload" in source


def test_clearance_acceptance_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_acceptance_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_acceptance_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_acceptance_board_payload.py")

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
        "_acceptance_status",
        "_acceptance_readiness",
        "_acceptance_gate",
        "_acceptance_instruction",
        "_card_from_packet",
        "_sort_card",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_acceptance_board_payload",
        "build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload",
    }


def test_clearance_acceptance_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_acceptance_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_acceptance_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_acceptance_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_acceptance_board import (
        _acceptance_gate,
        _acceptance_instruction,
        _acceptance_readiness,
        _acceptance_status,
        _card_from_packet,
        _matches,
        _sort_card,
    )

    assert callable(_acceptance_status)
    assert callable(_acceptance_readiness)
    assert callable(_acceptance_gate)
    assert callable(_acceptance_instruction)
    assert callable(_card_from_packet)
    assert callable(_sort_card)
    assert callable(_matches)


def test_clearance_acceptance_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_acceptance_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload",
        lambda **_: {
            "schema_version": "synthetic-signoff-packet/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "signoff_packets": [
                {
                    "signoff_packet_id": "signoff-monkeypatch",
                    "evidence_lane": "ACCEPTANCE_READY",
                    "signoff_status": "CLEARANCE_SIGNOFF_PACKET_READY_FOR_HUMAN_SIGNOFF_OBSERVATION",
                    "signoff_readiness": "SIGNOFF_READY_OBSERVATION",
                    "ready_for_human_signoff_observation": True,
                    "priority": "P2",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-ACCEPTANCE"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_acceptance_board_payload()

    assert payload["source_schema_version"] == "synthetic-signoff-packet/v1"
    assert payload["summary"]["acceptance_card_count_returned"] == 1
    assert payload["acceptance_cards"][0]["acceptance_readiness"] == "ACCEPTANCE_READY_OBSERVATION"
    assert payload["acceptance_cards"][0]["acceptance_record_write_authority"] == "none_read_plane"
    assert payload["acceptance_cards"][0]["operator_signoff_authority"] == "none_read_plane"
