from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_archive_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_archive.py")

    assert len(source.splitlines()) <= 85
    assert "def build_ui_semantic_validator_handoff_archive_payload(" not in source
    assert "def _normalize_archive_manifest(" not in source
    assert "def _archive_packet(" not in source
    assert "def _archive_row(" not in source
    assert "ui_semantic_validator_handoff_archive_common" in source
    assert "ui_semantic_validator_handoff_archive_manifests" in source
    assert "ui_semantic_validator_handoff_archive_packet" in source
    assert "ui_semantic_validator_handoff_archive_rows" in source
    assert "ui_semantic_validator_handoff_archive_payload" in source


def test_semantic_validator_handoff_archive_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_archive_common.py")
    manifests = _function_names("ui_semantic_validator_handoff_archive_manifests.py")
    packet = _function_names("ui_semantic_validator_handoff_archive_packet.py")
    rows = _function_names("ui_semantic_validator_handoff_archive_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_archive_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_counts", "_digest", "_sha256", "_read_json", "_placeholder", "_authority_assertion_true", "_manifest_value"} <= common
    assert manifests == {"_is_archive_manifest_candidate", "_archive_manifest_artifacts", "_normalize_archive_manifest"}
    assert packet == {"_archive_packet", "_archive_template"}
    assert rows == {"_match_manifests", "_archive_status", "_issue_codes", "_archive_row", "_haystack", "_matches"}
    assert payload == {"build_ui_semantic_validator_handoff_archive_payload", "build_ui_semantic_validator_handoff_archive_latest_payload"}


def test_semantic_validator_handoff_archive_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_archive as facade
    from strategy_validator.application import ui_semantic_validator_handoff_archive_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_archive_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_archive import (
        _archive_manifest_artifacts,
        _archive_packet,
        _archive_row,
        _normalize_archive_manifest,
    )

    assert callable(_archive_manifest_artifacts)
    assert callable(_archive_packet)
    assert callable(_archive_row)
    assert callable(_normalize_archive_manifest)
