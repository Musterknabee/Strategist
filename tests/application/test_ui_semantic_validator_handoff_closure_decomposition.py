from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_closure_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_closure.py")

    assert len(source.splitlines()) <= 80
    assert "def build_ui_semantic_validator_handoff_closure_payload(" not in source
    assert "def _normalize_closure_attestation(" not in source
    assert "def _closure_packet(" not in source
    assert "def _closure_row(" not in source
    assert "ui_semantic_validator_handoff_closure_common" in source
    assert "ui_semantic_validator_handoff_closure_attestations" in source
    assert "ui_semantic_validator_handoff_closure_packet" in source
    assert "ui_semantic_validator_handoff_closure_rows" in source
    assert "ui_semantic_validator_handoff_closure_payload" in source


def test_semantic_validator_handoff_closure_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_closure_common.py")
    attestations = _function_names("ui_semantic_validator_handoff_closure_attestations.py")
    packet = _function_names("ui_semantic_validator_handoff_closure_packet.py")
    rows = _function_names("ui_semantic_validator_handoff_closure_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_closure_payload.py")

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
        "_closure_value",
    } <= common
    assert attestations == {
        "_is_closure_attestation_candidate",
        "_closure_attestation_artifacts",
        "_normalize_closure_attestation",
    }
    assert packet == {"_closure_packet", "_closure_template"}
    assert rows == {
        "_match_attestations",
        "_closure_status",
        "_issue_codes",
        "_closure_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "build_ui_semantic_validator_handoff_closure_payload",
        "build_ui_semantic_validator_handoff_closure_latest_payload",
    }


def test_semantic_validator_handoff_closure_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_closure as facade
    from strategy_validator.application import ui_semantic_validator_handoff_closure_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_closure_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_closure import (
        _closure_attestation_artifacts,
        _closure_packet,
        _closure_row,
        _normalize_closure_attestation,
    )

    assert callable(_closure_attestation_artifacts)
    assert callable(_closure_packet)
    assert callable(_closure_row)
    assert callable(_normalize_closure_attestation)
