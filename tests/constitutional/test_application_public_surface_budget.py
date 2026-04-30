from __future__ import annotations

import ast
from pathlib import Path

from strategy_validator.application.public_surface import (
    build_application_public_surface_inventory,
    check_application_public_surface_budgets,
)


def _export_map_count(path: Path) -> int | None:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "_EXPORT_MAP" for target in node.targets):
                return len(node.value.keys)
    return None


def test_application_root_uses_single_canonical_lazy_export_map() -> None:
    init_source = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")
    exports_source = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")

    assert "from strategy_validator.application._exports import _EXPORT_MAP" in init_source
    assert _export_map_count(Path("strategy_validator/application/__init__.py")) is None
    export_map_count = _export_map_count(Path("strategy_validator/application/_exports.py"))
    assert export_map_count is not None
    assert export_map_count <= 316
    assert len(init_source.splitlines()) <= 40
    assert "def __getattr__" in init_source
    assert "_EXPORT_MAP" in exports_source


def test_application_public_surface_inventory_reports_and_ratchets_exports() -> None:
    inventory = build_application_public_surface_inventory(Path('.').resolve())
    payload = inventory.to_payload()

    assert payload['schema_version'] == 'application_public_surface_inventory/v1'
    assert payload['export_count'] <= 316
    assert 'application public surface inventory' in payload['summary_line']
    assert 'materialize_temporal_semantic_sensor_payloads' not in payload['exports']

    budget = check_application_public_surface_budgets(Path('.').resolve())
    assert budget['ok'] is True
    assert budget['violations'] == []
