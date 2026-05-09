from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_release_packet_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_release_packet.py")

    assert len(source.splitlines()) <= 95
    assert "def build_ui_semantic_validator_handoff_clearance_release_packet_payload(" not in source
    assert "def _packet_from_release(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_release_packet_common" in source
    assert "ui_semantic_validator_handoff_clearance_release_packet_rows" in source
    assert "ui_semantic_validator_handoff_clearance_release_packet_payload" in source


def test_clearance_release_packet_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_release_packet_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_release_packet_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_release_packet_payload.py")

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
        "_packet_status",
        "_packet_readiness",
        "_packet_gate",
        "_packet_instruction",
        "_packet_from_release",
        "_rank",
        "_sort_packet",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_release_packet_payload",
        "build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload",
    }


def test_clearance_release_packet_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_packet as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_packet_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_release_packet_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_packet import (
        _matches,
        _packet_from_release,
        _packet_gate,
        _packet_instruction,
        _packet_readiness,
        _packet_status,
        _sort_packet,
    )

    assert callable(_packet_status)
    assert callable(_packet_readiness)
    assert callable(_packet_gate)
    assert callable(_packet_instruction)
    assert callable(_packet_from_release)
    assert callable(_sort_packet)
    assert callable(_matches)


def test_clearance_release_packet_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_packet as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload",
        lambda **_: {
            "schema_version": "synthetic-release-readiness-board/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "release_readiness_cards": [
                {
                    "release_readiness_card_id": "rr-monkeypatch",
                    "evidence_lane": "READY",
                    "release_status": "CLEARANCE_RELEASE_READY_FOR_OBSERVATION",
                    "release_readiness": "RELEASE_READY_OBSERVATION",
                    "ready_for_release_observation": True,
                    "priority": "P2",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-RELEASE-PACKET"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_release_packet_payload()

    assert payload["source_schema_version"] == "synthetic-release-readiness-board/v1"
    assert payload["summary"]["release_packet_count_returned"] == 1
    assert payload["release_packets"][0]["release_packet_readiness"] == "HUMAN_RELEASE_READY_OBSERVATION"
    assert payload["release_packets"][0]["release_packet_write_authority"] == "none_read_plane"
    assert payload["release_packets"][0]["handoff_release_authority"] == "none_read_plane"
