from __future__ import annotations

import ast
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from strategy_validator.application.public_surface import (
    APPLICATION_EXPORT_BUDGETS,
    build_application_public_surface_inventory,
)
from strategy_validator.cli_support.public_surface_inventory import (
    CLI_SURFACE_BUDGETS,
    build_cli_public_surface_inventory,
)

PUBLIC_SURFACE_DASHBOARD_BUDGETS: Mapping[str, int] = {
    "api_route_modules": 32,
    "api_route_count": 366,
    "application_exports": APPLICATION_EXPORT_BUDGETS["export_count"],
    "cli_files": max(CLI_SURFACE_BUDGETS["cli_file_count"], 220),
    "console_scripts": 47,
    "frontend_pages": 88,
    "test_files": 725,
    "docs_pages": 182,
    "adr_count": 98,
    "compatibility_shims": CLI_SURFACE_BUDGETS["compatibility_file_count"],
}

NO_HEADROOM_RULE = (
    "Any category with no headroom requires consolidation, an explicit budget "
    "update with rationale, or rejection of new public surface."
)


@dataclass(frozen=True)
class PublicSurfaceMetric:
    actual: int
    budget: int
    headroom: int
    status: str
    rationale_required: bool

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PublicSurfaceDashboard:
    schema_version: str
    ok: bool
    no_headroom_rule: str
    metrics: Mapping[str, PublicSurfaceMetric]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "no_headroom_rule": self.no_headroom_rule,
            "metrics": {key: value.to_payload() for key, value in self.metrics.items()},
            "violations": [
                {"metric": key, **value.to_payload()}
                for key, value in self.metrics.items()
                if value.actual > value.budget
            ],
            "no_headroom": [
                key for key, value in self.metrics.items() if value.headroom == 0
            ],
        }


def _py_files(path: Path) -> list[Path]:
    return sorted(item for item in path.glob("*.py") if item.name != "__init__.py") if path.exists() else []


def _count_api_route_modules(repo_root: Path) -> int:
    return len(_py_files(repo_root / "strategy_validator" / "api" / "routes"))


def _count_api_route_decorators(repo_root: Path) -> int:
    """Count explicitly declared route decorators without importing the ASGI app."""
    route_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    count = 0
    for path in _py_files(repo_root / "strategy_validator" / "api" / "routes"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                if isinstance(target, ast.Attribute) and target.attr in route_methods:
                    count += 1
    return count


def _count_console_scripts(repo_root: Path) -> int:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return 0
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = payload.get("project", {}).get("scripts", {})
    return len(scripts) if isinstance(scripts, dict) else 0


def _count_frontend_pages(repo_root: Path) -> int:
    app_root = repo_root / "ui" / "strategist-web" / "app"
    return len(list(app_root.rglob("page.tsx"))) if app_root.exists() else 0


def _count_test_files(repo_root: Path) -> int:
    tests_root = repo_root / "tests"
    return len(list(tests_root.rglob("test*.py"))) if tests_root.exists() else 0


def _count_docs_pages(repo_root: Path) -> int:
    docs_root = repo_root / "docs"
    return len(list(docs_root.rglob("*.md"))) if docs_root.exists() else 0


def _count_adrs(repo_root: Path) -> int:
    architecture_root = repo_root / "docs" / "architecture"
    return len(list(architecture_root.glob("ADR*.md"))) if architecture_root.exists() else 0


def _metric(actual: int, budget: int) -> PublicSurfaceMetric:
    headroom = budget - actual
    if actual > budget:
        status = "OVER_BUDGET"
    elif headroom == 0:
        status = "NO_HEADROOM"
    else:
        status = "WITH_HEADROOM"
    return PublicSurfaceMetric(
        actual=actual,
        budget=budget,
        headroom=headroom,
        status=status,
        rationale_required=headroom <= 0,
    )


def build_public_surface_dashboard(repo_root: str | Path | None = None) -> PublicSurfaceDashboard:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    application_inventory = build_application_public_surface_inventory(root)
    cli_inventory = build_cli_public_surface_inventory(root)

    actuals = {
        "api_route_modules": _count_api_route_modules(root),
        "api_route_count": _count_api_route_decorators(root),
        "application_exports": application_inventory.export_count,
        "cli_files": cli_inventory.cli_file_count,
        "console_scripts": _count_console_scripts(root),
        "frontend_pages": _count_frontend_pages(root),
        "test_files": _count_test_files(root),
        "docs_pages": _count_docs_pages(root),
        "adr_count": _count_adrs(root),
        "compatibility_shims": cli_inventory.compatibility_file_count,
    }
    metrics = {
        key: _metric(actuals[key], PUBLIC_SURFACE_DASHBOARD_BUDGETS[key])
        for key in PUBLIC_SURFACE_DASHBOARD_BUDGETS
    }
    return PublicSurfaceDashboard(
        schema_version="public_surface_dashboard/v1",
        ok=all(metric.actual <= metric.budget for metric in metrics.values()),
        no_headroom_rule=NO_HEADROOM_RULE,
        metrics=metrics,
    )


__all__ = [
    "NO_HEADROOM_RULE",
    "PUBLIC_SURFACE_DASHBOARD_BUDGETS",
    "PublicSurfaceDashboard",
    "PublicSurfaceMetric",
    "build_public_surface_dashboard",
]
