"""Static proofs for UI router mutation auth wiring (repo-native AST checks)."""
from __future__ import annotations

import ast
from pathlib import Path

UI_ROUTE_DECLARATION_ROOT = Path('strategy_validator/api/routes')
HTTP_DECORATORS = {
    'get': 'GET',
    'post': 'POST',
    'put': 'PUT',
    'patch': 'PATCH',
    'delete': 'DELETE',
    'head': 'HEAD',
    'options': 'OPTIONS',
}


def _normalise_ui_path(path: str) -> str:
    if not path.startswith('/'):
        path = '/' + path
    if not path.startswith('/ui'):
        path = '/ui' + path
    return path.replace('//', '/')


_READ_PLANE_HTTP = frozenset({'get', 'head', 'options'})
_MUTATION_POST_PATHS = frozenset({_normalise_ui_path('/commands/{action}'), _normalise_ui_path('/strategy-intake')})


def _depends_arg_contains_require_mutation_auth(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Depends':
        if not node.args:
            return False
        return _expr_is_require_mutation_auth_ref(node.args[0])
    return False


def _expr_is_require_mutation_auth_ref(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == 'require_mutation_auth':
        return True
    if isinstance(node, ast.Name) and node.id == 'require_mutation_auth':
        return True
    return False


def _iter_arg_defaults(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[ast.arg, ast.AST | None]]:
    pairs: list[tuple[ast.arg, ast.AST | None]] = []
    pos = list(fn.args.posonlyargs) + list(fn.args.args)
    defaults = list(fn.args.defaults)
    tail = len(pos) - len(defaults)
    for idx, arg in enumerate(pos):
        default = defaults[idx - tail] if idx >= tail else None
        pairs.append((arg, default))
    for arg, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults):
        pairs.append((arg, default))
    return pairs


def _decorator_router_methods_paths(dec: ast.expr) -> list[tuple[str, str]]:
    """Return (HTTP_METHOD, normalised /ui path) for ``@router.get(...)``-style calls."""
    out: list[tuple[str, str]] = []
    if not isinstance(dec, ast.Call):
        return out
    func = dec.func
    if not isinstance(func, ast.Attribute):
        return out
    method = HTTP_DECORATORS.get(func.attr)
    if method is None:
        return out
    if not isinstance(func.value, ast.Name) or func.value.id != 'router':
        return out
    if not dec.args or not isinstance(dec.args[0], ast.Constant):
        return out
    raw = dec.args[0].value
    if not isinstance(raw, str):
        return out
    out.append((method, _normalise_ui_path(raw)))
    return out


def _decorator_dependencies_calls(dec: ast.Call) -> list[ast.Call]:
    """Collect ``Depends(...)`` call nodes from ``dependencies=[...]`` on route decorators."""
    found: list[ast.Call] = []
    for kw in dec.keywords:
        if kw.arg != 'dependencies' or not isinstance(kw.value, (ast.List, ast.Tuple)):
            continue
        for elt in kw.value.elts:
            if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id == 'Depends':
                found.append(elt)
    return found


def collect_ui_mutation_post_auth_violations(repo_root: Path) -> tuple[str, ...]:
    """POST mutation UI handlers must depend on ``require_mutation_auth``."""
    path = repo_root / UI_ROUTE_DECLARATION_ROOT / 'ui_routes_mutation.py'
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=path.as_posix())
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        post_paths: list[str] = []
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            for method, route_path in _decorator_router_methods_paths(dec):
                if method == 'POST':
                    post_paths.append(route_path)
        for route_path in post_paths:
            if route_path not in _MUTATION_POST_PATHS:
                continue
            ok = any(_depends_arg_contains_require_mutation_auth(d) for _, d in _iter_arg_defaults(node))
            ok = ok or any(
                _expr_is_require_mutation_auth_ref(call.args[0])
                for dec in node.decorator_list
                if isinstance(dec, ast.Call)
                for call in _decorator_dependencies_calls(dec)
                if call.args
            )
            if not ok:
                errors.append(
                    f'{path.as_posix()}:{node.lineno}: POST {route_path} must use Depends(...require_mutation_auth...)'
                )
    return tuple(errors)


def collect_ui_read_plane_mutation_auth_violations(repo_root: Path) -> tuple[str, ...]:
    """GET/HEAD/OPTIONS UI handlers must not pull in ``require_mutation_auth`` via Depends."""
    route_root = repo_root / UI_ROUTE_DECLARATION_ROOT
    errors: list[str] = []
    paths = sorted(route_root.glob('ui.py')) + sorted(route_root.glob('ui_routes_*.py'))
    for path in paths:
        if path.name == 'ui_routes_mutation.py':
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=path.as_posix())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            has_read_decorator = False
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                for method, _route_path in _decorator_router_methods_paths(dec):
                    if method.lower() not in _READ_PLANE_HTTP:
                        continue
                    has_read_decorator = True
                    for dep in _decorator_dependencies_calls(dec):
                        if dep.args and _expr_is_require_mutation_auth_ref(dep.args[0]):
                            errors.append(
                                f'{path.as_posix()}:{node.lineno}: {method} route must not use '
                                f'require_mutation_auth in dependencies='
                            )
            if not has_read_decorator:
                continue
            for _arg, default in _iter_arg_defaults(node):
                if _depends_arg_contains_require_mutation_auth(default):
                    errors.append(
                        f'{path.as_posix()}:{node.lineno}: read-plane handler must not use '
                        f'Depends(require_mutation_auth) on parameters'
                    )
    return tuple(errors)


__all__ = [
    'collect_ui_mutation_post_auth_violations',
    'collect_ui_read_plane_mutation_auth_violations',
]
