from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "strategy_validator" / "application"


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_paper_tracking_ops_is_not_the_lifecycle_owner() -> None:
    ops = APP / "paper_tracking_ops.py"
    lifecycle = APP / "paper_tracking_lifecycle.py"
    common = APP / "paper_tracking_common.py"
    assessment = APP / "paper_tracking_lifecycle_assessment.py"
    persistence = APP / "paper_tracking_lifecycle_persistence.py"
    inventory = APP / "paper_tracking_lifecycle_inventory.py"

    assert _line_count(ops) < 500
    assert _line_count(lifecycle) < 80
    assert _line_count(common) < 80

    ops_funcs = _function_names(ops)
    lifecycle_funcs = _function_names(lifecycle)
    assessment_funcs = _function_names(assessment)
    persistence_funcs = _function_names(persistence)
    inventory_funcs = _function_names(inventory)

    assert "derive_candidate_lifecycle_assessment" not in ops_funcs
    assert "assess_paper_tracking" not in ops_funcs
    assert "list_paper_tracking_entries" not in ops_funcs
    assert "derive_candidate_lifecycle_assessment" not in lifecycle_funcs
    assert "assess_paper_tracking" not in lifecycle_funcs
    assert "list_paper_tracking_entries" not in lifecycle_funcs
    assert "derive_candidate_lifecycle_assessment" in assessment_funcs
    assert "assess_paper_tracking" in persistence_funcs
    assert "apply_manifest_governance_updates" in persistence_funcs
    assert "list_paper_tracking_entries" in inventory_funcs


def test_paper_tracking_legacy_import_surface_remains_stable() -> None:
    from strategy_validator.application import paper_tracking_ops

    assert callable(paper_tracking_ops.derive_candidate_lifecycle_assessment)
    assert callable(paper_tracking_ops.assess_paper_tracking)
    assert callable(paper_tracking_ops.list_paper_tracking_entries)
    assert callable(paper_tracking_ops.read_persisted_lifecycle_assessment)
    assert callable(paper_tracking_ops.enroll_strategies_from_batch_run)
    assert callable(paper_tracking_ops.append_daily_snapshot)
    assert callable(paper_tracking_ops.evaluate_paper_tracking)
