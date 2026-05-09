from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_release_disposition_board_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_release_disposition_board.py")

    assert len(source.splitlines()) <= 95
    assert "def build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload(" not in source
    assert "def _row(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_release_disposition_board_common" in source
    assert "ui_semantic_validator_handoff_clearance_release_disposition_board_rows" in source
    assert "ui_semantic_validator_handoff_clearance_release_disposition_board_payload" in source


def test_clearance_release_disposition_board_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_release_disposition_board_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_release_disposition_board_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_release_disposition_board_payload.py")

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
        "_status",
        "_readiness",
        "_gate",
        "_instruction",
        "_row",
        "_matches",
        "_sort",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload",
        "build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload",
    }


def test_clearance_release_disposition_board_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_disposition_board as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_disposition_board_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_release_disposition_board_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_release_disposition_board import (
        _gate,
        _instruction,
        _matches,
        _readiness,
        _row,
        _sort,
        _status,
    )

    assert callable(_status)
    assert callable(_readiness)
    assert callable(_gate)
    assert callable(_instruction)
    assert callable(_row)
    assert callable(_sort)
    assert callable(_matches)


def test_clearance_release_disposition_board_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_disposition_board as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_release_retention_board_payload",
        lambda **_: {
            "schema_version": "synthetic-release-retention/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "release_retentions": [
                {
                    "release_retention_id": "r-retention-monkeypatch",
                    "evidence_lane": "READY",
                    "release_retention_status": "CLEARANCE_RELEASE_RETENTION_READY_FOR_HUMAN_RETENTION_OBSERVATION",
                    "release_retention_readiness": "HUMAN_RETENTION_READY_OBSERVATION",
                    "ready_for_human_retention_observation": True,
                    "priority": "P2",
                    "severity": "INFO",
                    "trust_banner": "TRUSTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "issue_codes": [],
                    "experiment_ids": ["EXP-RELEASE-DISPOSITION"],
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload()

    assert payload["source_schema_version"] == "synthetic-release-retention/v1"
    assert payload["summary"]["release_disposition_count_returned"] == 1
    assert payload["release_dispositions"][0]["release_disposition_readiness"] == "HUMAN_DISPOSITION_READY_OBSERVATION"
    assert payload["release_dispositions"][0]["release_disposition_write_authority"] == "none_read_plane"
    assert payload["release_dispositions"][0]["release_retention_write_authority"] == "none_read_plane"
