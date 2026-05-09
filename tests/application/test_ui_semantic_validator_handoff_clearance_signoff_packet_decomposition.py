from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_signoff_packet_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_signoff_packet.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(" not in source
    assert "def _packet_from_docket(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_signoff_packet_common" in source
    assert "ui_semantic_validator_handoff_clearance_signoff_packet_rows" in source
    assert "ui_semantic_validator_handoff_clearance_signoff_packet_payload" in source


def test_clearance_signoff_packet_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_signoff_packet_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_signoff_packet_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_signoff_packet_payload.py")

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
        "_signoff_status",
        "_signoff_readiness",
        "_signoff_gate",
        "_signoff_instruction",
        "_packet_from_docket",
        "_sort_packet",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload",
        "build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload",
    }


def test_clearance_signoff_packet_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_signoff_packet as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_signoff_packet_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_signoff_packet_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_signoff_packet import (
        _matches,
        _packet_from_docket,
        _signoff_gate,
        _signoff_instruction,
        _signoff_readiness,
        _signoff_status,
        _sort_packet,
    )

    assert callable(_signoff_status)
    assert callable(_signoff_readiness)
    assert callable(_signoff_gate)
    assert callable(_signoff_instruction)
    assert callable(_packet_from_docket)
    assert callable(_sort_packet)
    assert callable(_matches)


def test_clearance_signoff_packet_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_signoff_packet as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_review_docket_payload",
        lambda **_: {
            "schema_version": "synthetic-review-docket/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "review_dockets": [
                {
                    "review_docket_id": "docket-monkeypatch",
                    "evidence_lane": "AUTHORIZED_REVIEW",
                    "docket_status": "CLEARANCE_REVIEW_DOCKET_READY_FOR_AUTHORIZED_REVIEW",
                    "docket_readiness": "AUTHORIZED_REVIEW_OBSERVATION",
                    "ready_for_authorized_review": True,
                    "priority": "P2",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "owner_hints": ["human_operator_clearance_owner"],
                    "issue_codes": [],
                    "experiment_ids": ["EXP-SIGNOFF"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_signoff_packet_payload()

    assert payload["source_schema_version"] == "synthetic-review-docket/v1"
    assert payload["summary"]["signoff_packet_count_returned"] == 1
    assert payload["signoff_packets"][0]["signoff_readiness"] == "SIGNOFF_READY_OBSERVATION"
    assert payload["signoff_packets"][0]["signoff_packet_write_authority"] == "none_read_plane"
    assert payload["signoff_packets"][0]["operator_signoff_authority"] == "none_read_plane"
