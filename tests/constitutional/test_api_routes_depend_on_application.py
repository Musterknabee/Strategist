from __future__ import annotations

import ast
from pathlib import Path

ROUTES_ROOT = Path('strategy_validator/api/routes')
_ALLOWED_INTERNAL_ROUTE_FACADES = (
    'strategy_validator.api.routes import ui as ui_root',
    'strategy_validator.api.routes import ui_route_responses as _ui_route_responses',
)
_FORBIDDEN_DOMAIN_IMPORTS = (
    'strategy_validator.validator',
    'strategy_validator.control_plane',
    'strategy_validator.projections',
    'strategy_validator.ledger',
)


def _route_files() -> tuple[Path, ...]:
    return tuple(sorted(path for path in ROUTES_ROOT.glob('*.py') if path.name != '__init__.py'))


def _defines_router_or_routes(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == 'router' for target in node.targets):
                return True
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                text = ast.unparse(decorator)
                if text.startswith('router.'):
                    return True
    return False


def test_all_api_route_modules_stay_behind_application_or_bounded_route_facades() -> None:
    files = _route_files()
    assert files, 'no API route modules discovered'
    for path in files:
        text = path.read_text(encoding='utf-8')
        if not _defines_router_or_routes(text):
            continue
        assert not any(forbidden in text for forbidden in _FORBIDDEN_DOMAIN_IMPORTS), path.as_posix()
        assert (
            'strategy_validator.application.' in text
            or any(allowed in text for allowed in _ALLOWED_INTERNAL_ROUTE_FACADES)
        ), path.as_posix()
