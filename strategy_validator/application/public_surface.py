from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

APPLICATION_EXPORT_BUDGETS: Mapping[str, int] = {
    'export_count': 316,
}


@dataclass(frozen=True)
class ApplicationPublicSurfaceInventory:
    schema_version: str
    export_count: int
    exports: tuple[str, ...]
    summary_line: str

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload['exports'] = list(self.exports)
        return payload


def _export_map_path(repo_root: Path) -> Path:
    return repo_root / 'strategy_validator' / 'application' / '_exports.py'


def _load_export_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == '_EXPORT_MAP' for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            return ()
        names: list[str] = []
        for key in node.value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                names.append(key.value)
        return tuple(sorted(names))
    return ()


def build_application_public_surface_inventory(repo_root: str | Path | None = None) -> ApplicationPublicSurfaceInventory:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[2]
    exports = _load_export_names(_export_map_path(root))
    summary_line = f'application public surface inventory: exports={len(exports)}.'
    return ApplicationPublicSurfaceInventory(
        schema_version='application_public_surface_inventory/v1',
        export_count=len(exports),
        exports=exports,
        summary_line=summary_line,
    )


def check_application_public_surface_budgets(repo_root: str | Path | None = None) -> dict[str, object]:
    inventory = build_application_public_surface_inventory(repo_root)
    actuals = inventory.to_payload()
    violations = []
    for metric, budget in APPLICATION_EXPORT_BUDGETS.items():
        actual = int(actuals.get(metric, 0))
        if actual > budget:
            violations.append({
                'metric': metric,
                'actual': actual,
                'budget': budget,
                'excess': actual - budget,
            })
    return {
        'schema_version': 'application_public_surface_budget/v1',
        'ok': not violations,
        'budgets': dict(APPLICATION_EXPORT_BUDGETS),
        'violations': violations,
        'inventory': actuals,
    }


__all__ = [
    'APPLICATION_EXPORT_BUDGETS',
    'ApplicationPublicSurfaceInventory',
    'build_application_public_surface_inventory',
    'check_application_public_surface_budgets',
]
