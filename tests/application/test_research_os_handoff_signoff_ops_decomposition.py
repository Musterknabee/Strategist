from __future__ import annotations

import ast
import importlib
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_research_os_handoff_signoff_ops_facade_remains_thin() -> None:
    source = _source("research_os_handoff_signoff_ops.py")

    assert len(source.splitlines()) <= 90
    assert "def build_research_os_handoff_verification_result(" not in source
    assert "def build_research_os_handoff_reviewer_signoff(" not in source
    assert "def build_ui_research_os_handoff_signoff_latest_payload(" not in source
    assert "research_os_handoff_signoff_verification" in source
    assert "research_os_handoff_signoff_reviewer" in source
    assert "research_os_handoff_signoff_ui" in source


def test_research_os_handoff_signoff_subphase_ownership() -> None:
    common = _function_names("research_os_handoff_signoff_common.py")
    verification = _function_names("research_os_handoff_signoff_verification.py")
    reviewer = _function_names("research_os_handoff_signoff_reviewer.py")
    ui = _function_names("research_os_handoff_signoff_ui.py")

    assert {
        "_artifact_root",
        "research_os_handoff_signoff_root",
        "research_os_handoff_verification_latest_path",
        "research_os_handoff_reviewer_signoff_latest_path",
        "_read_json",
        "_write_json",
        "_canonical_sha256",
        "_contains_secret_marker",
    } <= common
    assert {
        "_source_check",
        "_with_verification_digest",
        "build_research_os_handoff_verification_result",
        "write_research_os_handoff_verification_result",
        "build_and_write_research_os_handoff_verification_result",
        "load_latest_research_os_handoff_verification_result",
    } <= verification
    assert {
        "_with_signoff_digest",
        "build_research_os_handoff_reviewer_signoff",
        "write_research_os_handoff_reviewer_signoff",
        "build_and_write_research_os_handoff_reviewer_signoff",
        "load_latest_research_os_handoff_reviewer_signoff",
    } <= reviewer
    assert ui == {"build_ui_research_os_handoff_signoff_latest_payload"}


def test_research_os_handoff_signoff_facade_exports_expected_surface() -> None:
    facade = importlib.import_module("strategy_validator.application.research_os_handoff_signoff_ops")

    for name in [
        "build_research_os_handoff_verification_result",
        "build_and_write_research_os_handoff_verification_result",
        "load_latest_research_os_handoff_verification_result",
        "build_research_os_handoff_reviewer_signoff",
        "build_and_write_research_os_handoff_reviewer_signoff",
        "load_latest_research_os_handoff_reviewer_signoff",
        "build_ui_research_os_handoff_signoff_latest_payload",
        "research_os_handoff_signoff_root",
        "research_os_handoff_verification_latest_path",
        "research_os_handoff_reviewer_signoff_latest_path",
    ]:
        assert callable(getattr(facade, name))


def test_research_os_handoff_signoff_legacy_helper_imports_remain_available() -> None:
    from strategy_validator.application.research_os_handoff_signoff_ops import (
        _canonical_sha256,
        _read_json,
        _source_check,
        _with_signoff_digest,
        _with_verification_digest,
        _write_json,
    )

    assert callable(_canonical_sha256)
    assert callable(_read_json)
    assert callable(_write_json)
    assert callable(_source_check)
    assert callable(_with_signoff_digest)
    assert callable(_with_verification_digest)
