from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "strategy_validator" / "application"


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_ui_detail_views_is_legacy_facade_not_payload_owner() -> None:
    facade = APP / "ui_detail_views.py"

    assert _line_count(facade) <= 80
    assert _function_names(facade) == set()


def test_ui_detail_view_builders_are_owned_by_family_modules() -> None:
    expected = {
        "ui_detail_runtime_status": {"_build_provider_paths", "build_ui_runtime_status_payload"},
        "ui_detail_burnin": {"_default_cpcv_curve", "_default_calibration_curve", "build_ui_burnin_payload"},
        "ui_detail_pack": {"_select_pack_item", "build_ui_pack_detail_payload"},
        "ui_detail_tribunal": {"_default_tribunal_workspace", "build_ui_tribunal_payload"},
        "ui_detail_evidence": {"_load_json", "_collect_named_artifacts", "build_ui_evidence_payload"},
    }

    for module_name, names in expected.items():
        owned = _function_names(APP / f"{module_name}.py")
        assert names <= owned


def test_ui_detail_legacy_import_surface_remains_stable() -> None:
    facade = importlib.import_module("strategy_validator.application.ui_detail_views")

    for name in (
        "build_ui_runtime_status_payload",
        "build_ui_burnin_payload",
        "build_ui_pack_detail_payload",
        "build_ui_tribunal_payload",
        "build_ui_evidence_payload",
    ):
        assert callable(getattr(facade, name))
        assert name in facade.__all__
