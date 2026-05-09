from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_custody_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_custody.py")

    assert len(source.splitlines()) <= 85
    assert "def build_ui_semantic_validator_handoff_custody_payload(" not in source
    assert "def _normalize_custody_seal(" not in source
    assert "def _custody_packet(" not in source
    assert "def _custody_row(" not in source
    assert "ui_semantic_validator_handoff_custody_common" in source
    assert "ui_semantic_validator_handoff_custody_seals" in source
    assert "ui_semantic_validator_handoff_custody_packet" in source
    assert "ui_semantic_validator_handoff_custody_rows" in source
    assert "ui_semantic_validator_handoff_custody_payload" in source


def test_semantic_validator_handoff_custody_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_custody_common.py")
    seals = _function_names("ui_semantic_validator_handoff_custody_seals.py")
    packet = _function_names("ui_semantic_validator_handoff_custody_packet.py")
    rows = _function_names("ui_semantic_validator_handoff_custody_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_custody_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_as_list",
        "_norm_set",
        "_contains",
        "_counts",
        "_digest",
        "_sha256",
        "_read_json",
        "_placeholder",
        "_authority_assertion_true",
        "_seal_value",
    } <= common
    assert seals == {
        "_is_custody_seal_candidate",
        "_custody_seal_artifacts",
        "_normalize_custody_seal",
    }
    assert packet == {"_custody_packet_digest", "_custody_packet", "_custody_template"}
    assert rows == {
        "_match_seals",
        "_custody_status",
        "_issue_codes",
        "_custody_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "build_ui_semantic_validator_handoff_custody_payload",
        "build_ui_semantic_validator_handoff_custody_latest_payload",
    }


def test_semantic_validator_handoff_custody_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_custody as facade
    from strategy_validator.application import ui_semantic_validator_handoff_custody_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_custody_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_custody import (
        _custody_packet,
        _custody_row,
        _custody_seal_artifacts,
        _normalize_custody_seal,
    )

    assert callable(_custody_seal_artifacts)
    assert callable(_custody_packet)
    assert callable(_custody_row)
    assert callable(_normalize_custody_seal)
