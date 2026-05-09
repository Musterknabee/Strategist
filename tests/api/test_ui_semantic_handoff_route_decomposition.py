from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROUTES = Path("strategy_validator/api/routes")


def _function_names(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def test_semantic_handoff_route_module_is_family_facade() -> None:
    facade = ROUTES / "ui_routes_detail_semantic_handoff.py"
    source = facade.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 140
    assert "router.include_router(release_router)" in source
    assert "router.include_router(lifecycle_router)" in source
    assert "router.include_router(operations_router)" in source
    assert "@router.get(" not in source


def test_semantic_handoff_route_subfamilies_own_expected_endpoints() -> None:
    expected = {
        "ui_routes_detail_semantic_handoff_release.py": {
            "get_semantic_release_handoff",
            "get_semantic_release_handoff_latest",
            "get_semantic_validator_handoff",
            "get_semantic_validator_handoff_latest",
        },
        "ui_routes_detail_semantic_handoff_lifecycle.py": {
            "get_semantic_validator_handoff_lineage",
            "get_semantic_validator_handoff_remediation",
            "get_semantic_validator_handoff_review",
            "get_semantic_validator_handoff_decision",
            "get_semantic_validator_handoff_signoff",
            "get_semantic_validator_handoff_custody",
            "get_semantic_validator_handoff_archive",
            "get_semantic_validator_handoff_closure",
            "get_semantic_validator_handoff_continuity",
            "get_semantic_validator_handoff_runbook",
        },
        "ui_routes_detail_semantic_handoff_operations.py": {
            "get_semantic_validator_handoff_exceptions",
            "get_semantic_validator_handoff_timeline",
            "get_semantic_validator_handoff_evidence_gaps",
            "get_semantic_validator_handoff_audit_packet",
            "get_semantic_validator_handoff_action_queue",
            "get_semantic_validator_handoff_escalation_board",
            "get_semantic_validator_handoff_resolution_plan",
        },
    }

    for filename, names in expected.items():
        found = _function_names(ROUTES / filename)
        assert names <= found


def test_semantic_handoff_facade_preserves_router_and_endpoint_exports() -> None:
    facade = importlib.import_module("strategy_validator.api.routes.ui_routes_detail_semantic_handoff")
    release = importlib.import_module("strategy_validator.api.routes.ui_routes_detail_semantic_handoff_release")
    lifecycle = importlib.import_module("strategy_validator.api.routes.ui_routes_detail_semantic_handoff_lifecycle")
    operations = importlib.import_module("strategy_validator.api.routes.ui_routes_detail_semantic_handoff_operations")

    expected_paths = {
        route.path
        for module in (release, lifecycle, operations)
        for route in module.router.routes
    }
    assert {route.path for route in facade.router.routes} == expected_paths
    assert facade.get_semantic_release_handoff is release.get_semantic_release_handoff
    assert facade.get_semantic_validator_handoff_lineage is lifecycle.get_semantic_validator_handoff_lineage
    assert facade.get_semantic_validator_handoff_action_queue is operations.get_semantic_validator_handoff_action_queue
