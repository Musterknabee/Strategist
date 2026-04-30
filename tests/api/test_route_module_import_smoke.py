from __future__ import annotations

import importlib
from pathlib import Path


ROUTES_DIR = Path("strategy_validator/api/routes")


def test_api_route_modules_import_individually() -> None:
    module_names = sorted(
        f"strategy_validator.api.routes.{path.stem}"
        for path in ROUTES_DIR.glob("*.py")
        if path.name != "__init__.py"
    )

    assert module_names
    for module_name in module_names:
        importlib.import_module(module_name)
