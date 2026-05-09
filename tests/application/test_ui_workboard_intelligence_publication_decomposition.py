from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_workboard_intelligence_publication_facade_remains_thin() -> None:
    source = _source("ui_workboard_intelligence_publication.py")
    assert len(source.splitlines()) <= 60
    assert "def _build_board_publication_surface(" not in source
    assert "def _build_board_export_payload(" not in source
    assert "ui_workboard_intelligence_publication_members" in source
    assert "ui_workboard_intelligence_publication_surface" in source
    assert "ui_workboard_intelligence_publication_manifest" in source
    assert "ui_workboard_intelligence_publication_export" in source


def test_workboard_intelligence_publication_subphase_ownership() -> None:
    assert _function_names("ui_workboard_intelligence_publication_members.py") == {
        "_build_publication_member_payload",
    }
    assert _function_names("ui_workboard_intelligence_publication_surface.py") == {
        "_build_board_publication_surface",
    }
    assert _function_names("ui_workboard_intelligence_publication_manifest.py") == {
        "_stable_json_sha256",
        "_build_board_publication_verification_envelope",
        "_build_board_publication_bundle_manifest",
    }
    assert _function_names("ui_workboard_intelligence_publication_export.py") == {
        "_build_board_export_payload",
    }


def test_workboard_intelligence_publication_facade_exports_match_subphases() -> None:
    from strategy_validator.application import ui_workboard_intelligence_publication as facade
    from strategy_validator.application import ui_workboard_intelligence_publication_export as export
    from strategy_validator.application import ui_workboard_intelligence_publication_manifest as manifest
    from strategy_validator.application import ui_workboard_intelligence_publication_members as members
    from strategy_validator.application import ui_workboard_intelligence_publication_surface as surface

    expected = [
        *members.__all__,
        *surface.__all__,
        *manifest.__all__,
        *export.__all__,
    ]
    assert facade.__all__ == expected
    for name in expected:
        assert getattr(facade, name) is not None


def test_workboard_intelligence_runtime_keeps_legacy_publication_import_path() -> None:
    source = _source("ui_workboard_intelligence.py")
    assert "strategy_validator.application.ui_workboard_intelligence_publication" in source
    assert "ui_workboard_intelligence_publication_export" not in source
    assert "ui_workboard_intelligence_publication_manifest" not in source
