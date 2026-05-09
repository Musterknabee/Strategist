from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_payload(" not in source
    assert "def _discover(" not in source
    assert "def _decision_ledger_entry(" not in source
    assert "ui_semantic_validator_handoff_common" in source
    assert "ui_semantic_validator_handoff_entries" in source
    assert "ui_semantic_validator_handoff_discovery" in source
    assert "ui_semantic_validator_handoff_rows" in source
    assert "ui_semantic_validator_handoff_payload" in source


def test_semantic_validator_handoff_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_common.py")
    entries = _function_names("ui_semantic_validator_handoff_entries.py")
    discovery = _function_names("ui_semantic_validator_handoff_discovery.py")
    rows = _function_names("ui_semantic_validator_handoff_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_payload.py")

    assert {
        "_utc_now",
        "_coerce_root",
        "_read_json",
        "_sha256",
        "_norm_set",
        "_contains",
        "_as_list",
        "_issue_haystack",
        "_counts",
        "_bool_counts",
        "_authority",
    } <= common
    assert entries == {
        "_base_entry",
        "_decision_ledger_entry",
        "_handoff_certificate_entry",
        "_validator_packet_entry",
        "_ingress_certificate_entry",
        "_artifact_entry",
    }
    assert discovery == {"_discover"}
    assert rows == {"_matches"}
    assert payload == {
        "build_ui_semantic_validator_handoff_payload",
        "build_ui_semantic_validator_handoff_latest_payload",
    }


def test_semantic_validator_handoff_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff as facade
    from strategy_validator.application import ui_semantic_validator_handoff_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff import (
        _artifact_entry,
        _base_entry,
        _bool_counts,
        _coerce_root,
        _counts,
        _decision_ledger_entry,
        _discover,
        _handoff_certificate_entry,
        _ingress_certificate_entry,
        _matches,
        _validator_packet_entry,
    )

    assert callable(_coerce_root)
    assert callable(_base_entry)
    assert callable(_decision_ledger_entry)
    assert callable(_handoff_certificate_entry)
    assert callable(_validator_packet_entry)
    assert callable(_ingress_certificate_entry)
    assert callable(_artifact_entry)
    assert callable(_discover)
    assert callable(_matches)
    assert callable(_counts)
    assert callable(_bool_counts)
