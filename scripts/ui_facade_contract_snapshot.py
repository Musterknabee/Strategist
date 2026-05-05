#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import os
import json
import sys
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_dir, safe_input_file, safe_output_file

DEFAULT_SNAPSHOT = Path('docs/api/ui-public-facade.snapshot.json')
FRONTEND_UI_FACADE_ROUTES_CONTRACT = Path('ui/strategist-web/lib/contracts/ui-facade-routes.json')
OPENAPI_CONTRACT_SNAPSHOT = Path('docs/architecture/openapi.snapshot.json')
UI_ROUTE_DECLARATION_ROOT = Path('strategy_validator/api/routes')
UI_ROUTE_MODULE_PATTERNS = ('ui.py', 'ui_routes_*.py')
HTTP_DECORATORS = {
    'get': 'GET',
    'post': 'POST',
    'put': 'PUT',
    'patch': 'PATCH',
    'delete': 'DELETE',
    'head': 'HEAD',
    'options': 'OPTIONS',
}


def _repo_root_from_script() -> Path:
    return _REPO_ROOT


def _validate_repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is None:
        return _repo_root_from_script()
    checked = safe_input_dir(repo_root, label="UI_FACADE_REPO_ROOT", required=True)
    assert checked is not None
    return checked


def _ensure_repo_on_path(repo_root: Path) -> None:
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def _route_key(method: str, path: str) -> tuple[str, str]:
    return method.upper(), path


def _normalise_ui_path(path: str) -> str:
    if not path.startswith('/'):
        path = '/' + path
    if not path.startswith('/ui'):
        path = '/ui' + path
    return path.replace('//', '/')


def _normalise_route(route: dict[str, object]) -> dict[str, object]:
    return {
        'method': str(route['method']).upper(),
        'path': str(route['path']),
        'kind': str(route['kind']),
        'auth_required': bool(route['auth_required']),
        'payload_schema': str(route['payload_schema']),
    }


def _route_hash(routes: Iterable[dict[str, object]]) -> str:
    text = json.dumps(list(routes), sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def build_frontend_ui_facade_routes_contract(facade_snapshot_payload: dict[str, object]) -> dict[str, object]:
    """Minimal route list artifact consumed by ``ui/strategist-web`` contract tests."""
    return {
        'schema_version': 'ui_facade_frontend_routes_contract/v1',
        'routes_sha256': facade_snapshot_payload['routes_sha256'],
        'route_count': facade_snapshot_payload['route_count'],
        'routes': facade_snapshot_payload['routes'],
    }


def _collect_openapi_ui_facade_drift(facade_routes: list[dict[str, object]], openapi: dict[str, object]) -> list[str]:
    """Each facade route must be registered under ``openapi['paths']`` with the same HTTP method."""
    errors: list[str] = []
    paths_block = openapi.get('paths')
    if not isinstance(paths_block, dict):
        return ['OpenAPI snapshot paths block missing or invalid']
    for route in facade_routes:
        path = str(route['path'])
        method = str(route['method']).lower()
        entry = paths_block.get(path)
        if not isinstance(entry, dict):
            errors.append(f'OpenAPI paths missing {path}')
            continue
        if method not in entry:
            errors.append(f'OpenAPI paths[{path!r}] missing operation {method.upper()}')
    return errors


def collect_declared_ui_routes_static(repo_root: Path) -> list[dict[str, str]]:
    route_root = repo_root / UI_ROUTE_DECLARATION_ROOT
    files: set[Path] = set()
    for pattern in UI_ROUTE_MODULE_PATTERNS:
        files.update(path for path in route_root.glob(pattern) if path.is_file())

    declared: set[tuple[str, str]] = set()
    for path in sorted(files, key=lambda item: item.as_posix()):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=path.as_posix())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not isinstance(func, ast.Attribute):
                    continue
                method = HTTP_DECORATORS.get(func.attr)
                if method is None:
                    continue
                if not isinstance(func.value, ast.Name) or func.value.id != 'router':
                    continue
                if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                    continue
                raw_path = decorator.args[0].value
                if not isinstance(raw_path, str):
                    continue
                declared.add(_route_key(method, _normalise_ui_path(raw_path)))

    return [{'method': method, 'path': path} for method, path in sorted(declared)]


def collect_registered_ui_routes_fastapi(repo_root: Path) -> list[dict[str, str]]:
    _ensure_repo_on_path(repo_root)
    from fastapi.routing import APIRoute  # type: ignore
    from strategy_validator.api.app import create_app

    registered: set[tuple[str, str]] = set()
    for route in create_app().routes:
        if not isinstance(route, APIRoute):
            continue
        path = str(route.path)
        if not path.startswith('/ui/') and path != '/ui':
            continue
        for method in sorted(route.methods or ()):  # type: ignore[attr-defined]
            registered.add(_route_key(str(method), path))
    return [{'method': method, 'path': path} for method, path in sorted(registered)]


def collect_registered_ui_routes(repo_root: Path, *, allow_static_fallback: bool = True) -> list[dict[str, str]]:
    # Prefer static route declaration reconciliation by default. Importing the full
    # FastAPI app pulls the complete operator/oracle surface into snapshot checks,
    # which is unnecessary for drift detection and can make simple CI checks slow
    # or sensitive to optional runtime stacks. Set this env var to force true
    # FastAPI route-table introspection when needed.
    force_fastapi = os.environ.get('STRATEGY_VALIDATOR_UI_FACADE_FASTAPI_INTROSPECTION', '').strip().lower() in {
        '1', 'true', 'yes'
    }
    if allow_static_fallback and not force_fastapi:
        return collect_declared_ui_routes_static(repo_root)
    if importlib.util.find_spec('fastapi') is None:
        if not allow_static_fallback:
            raise ModuleNotFoundError('fastapi')
        return collect_declared_ui_routes_static(repo_root)
    try:
        return collect_registered_ui_routes_fastapi(repo_root)
    except ModuleNotFoundError:
        if not allow_static_fallback:
            raise
        return collect_declared_ui_routes_static(repo_root)


def build_ui_facade_contract_snapshot(
    *,
    repo_root: str | Path | None = None,
    allow_static_fallback: bool = True,
) -> dict[str, object]:
    root = _validate_repo_root(repo_root)
    _ensure_repo_on_path(root)
    from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory

    facade = build_ui_public_facade_inventory(repo_root=root)
    facade_routes = sorted((_normalise_route(route) for route in facade['routes']), key=lambda route: (route['path'], route['method']))
    facade_route_keys = {(str(route['method']), str(route['path'])) for route in facade_routes}
    registered_routes = collect_registered_ui_routes(root, allow_static_fallback=allow_static_fallback)
    registered_route_keys = {(route['method'], route['path']) for route in registered_routes}

    missing_from_facade = sorted(registered_route_keys - facade_route_keys)
    extra_in_facade = sorted(facade_route_keys - registered_route_keys)
    if missing_from_facade or extra_in_facade:
        raise SystemExit(
            'UI facade route drift: '
            f'missing_from_facade={missing_from_facade!r} extra_in_facade={extra_in_facade!r}'
        )

    facade_by_key = {(str(route['method']), str(route['path'])): route for route in facade_routes}
    semantic_errors: list[str] = []
    for route in facade_routes:
        kind = str(route['kind'])
        method = str(route['method'])
        auth_required = bool(route['auth_required'])
        path = str(route['path'])
        payload_schema = str(route['payload_schema']).strip()
        if not payload_schema:
            semantic_errors.append(f'{method} {path}: empty payload_schema')
        if kind == 'mutation':
            if method != 'POST':
                semantic_errors.append(f'{method} {path}: kind=mutation requires POST')
            if not auth_required:
                semantic_errors.append(f'{method} {path}: mutation routes must declare auth_required=true')
        if auth_required and (kind != 'mutation' or method != 'POST'):
            semantic_errors.append(f'{method} {path}: auth_required=true is only allowed for POST mutation routes')
        if kind in {'read', 'metadata', 'export'} and auth_required:
            semantic_errors.append(
                f'{method} {path}: kind={kind} must not set auth_required=true (no mutation auth on read plane)'
            )
    for method, path in registered_route_keys:
        facade_route = facade_by_key[(method, path)]
        if method == 'POST':
            if not bool(facade_route['auth_required']) or str(facade_route['kind']) != 'mutation':
                semantic_errors.append(
                    f'{method} {path}: declared POST UI route must match facade mutation+auth_required contract'
                )
        elif bool(facade_route['auth_required']):
            semantic_errors.append(f'{method} {path}: non-POST route must not require mutation auth in facade')

    from scripts.ui_route_mutation_auth_ast import (
        collect_ui_mutation_post_auth_violations,
        collect_ui_read_plane_mutation_auth_violations,
    )

    semantic_errors.extend(collect_ui_mutation_post_auth_violations(root))
    semantic_errors.extend(collect_ui_read_plane_mutation_auth_violations(root))

    openapi_path = root / OPENAPI_CONTRACT_SNAPSHOT
    if not openapi_path.exists():
        semantic_errors.append(
            f'OpenAPI contract snapshot missing at {openapi_path.as_posix()}; cannot cross-check UI facade routes'
        )
    else:
        try:
            openapi_payload = json.loads(openapi_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            semantic_errors.append(f'OpenAPI snapshot JSON invalid: {exc}')
        else:
            semantic_errors.extend(_collect_openapi_ui_facade_drift(facade_routes, openapi_payload))

    if semantic_errors:
        raise SystemExit('UI facade semantic contract failed: ' + '; '.join(semantic_errors))

    return {
        'schema_version': 'ui_public_facade_snapshot/v1',
        'source_endpoint': '/ui/facade',
        'source_schema_version': facade['schema_version'],
        'surface': facade['surface'],
        'frontend_expected_package': facade['frontend_expected_package'],
        'frontend_package_present': facade['frontend_package_present'],
        'frontend_package_detected_by_backend': facade['frontend_package_detected_by_backend'],
        'frontend_readiness_claimed': facade['frontend_readiness_claimed'],
        'frontend_runtime_reachable': facade['frontend_runtime_reachable'],
        'frontend_operator_console_hint': facade['frontend_operator_console_hint'],
        'read_plane_only': facade['read_plane_only'],
        'mutation_route': facade['mutation_route'],
        'route_count': len(facade_routes),
        'routes_sha256': _route_hash(facade_routes),
        'routes': facade_routes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate or verify the public backend UI facade contract snapshot.')
    parser.add_argument('--repo-root', default=None, help='Repository root; defaults to this script parent repository.')
    parser.add_argument('--output', default=str(DEFAULT_SNAPSHOT), help='Snapshot path relative to repo root unless absolute.')
    parser.add_argument('--check', action='store_true', help='Verify the existing snapshot instead of writing it.')
    parser.add_argument(
        '--no-static-fallback',
        action='store_true',
        help='Require FastAPI route-table introspection instead of AST fallback when dependencies are unavailable.',
    )
    args = parser.parse_args(argv)

    try:
        repo_root = _validate_repo_root(args.repo_root)
    except PathIntegrityError as exc:
        print(json.dumps(path_error_payload(exc, schema_version="ui_facade_contract_snapshot_path_error/v1"), sort_keys=True))
        return 1

    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output

    try:
        checked_output = (
            safe_input_file(output, label="UI_FACADE_SNAPSHOT", required=True)
            if args.check
            else safe_output_file(output, label="UI_FACADE_SNAPSHOT_OUTPUT")
        )
    except PathIntegrityError as exc:
        print(json.dumps(path_error_payload(exc, schema_version="ui_facade_contract_snapshot_path_error/v1"), sort_keys=True))
        return 1
    assert checked_output is not None
    output = checked_output

    payload = build_ui_facade_contract_snapshot(
        repo_root=repo_root,
        allow_static_fallback=not args.no_static_fallback,
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + '\n'
    frontend_rel = FRONTEND_UI_FACADE_ROUTES_CONTRACT
    if not frontend_rel.is_absolute():
        frontend_output = repo_root / frontend_rel
    else:
        frontend_output = frontend_rel
    frontend_payload = build_frontend_ui_facade_routes_contract(payload)
    frontend_text = json.dumps(frontend_payload, indent=2, sort_keys=True) + '\n'

    if args.check:
        if not output.exists():
            print(f'missing UI facade contract snapshot: {output}')
            return 1
        current = output.read_text(encoding='utf-8')
        if current != text:
            print(f'UI facade contract snapshot drift: {output}')
            return 1
        try:
            checked_frontend = safe_input_file(frontend_output, label='UI_FACADE_FRONTEND_ROUTES_CONTRACT', required=True)
        except PathIntegrityError as exc:
            print(json.dumps(path_error_payload(exc, schema_version='ui_facade_contract_snapshot_path_error/v1'), sort_keys=True))
            return 1
        assert checked_frontend is not None
        frontend_output = checked_frontend
        fe_current = frontend_output.read_text(encoding='utf-8')
        if fe_current != frontend_text:
            print(f'frontend UI facade routes contract drift: {frontend_output}')
            return 1
        print(f'UI facade contract snapshot OK: {output}')
        print(f'frontend UI facade routes contract OK: {frontend_output}')
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding='utf-8')
    try:
        safe_fe = safe_output_file(frontend_output, label='UI_FACADE_FRONTEND_ROUTES_CONTRACT_OUTPUT')
    except PathIntegrityError as exc:
        print(json.dumps(path_error_payload(exc, schema_version='ui_facade_contract_snapshot_path_error/v1'), sort_keys=True))
        return 1
    assert safe_fe is not None
    frontend_output = safe_fe
    frontend_output.parent.mkdir(parents=True, exist_ok=True)
    frontend_output.write_text(frontend_text, encoding='utf-8')
    print(str(output))
    print(str(frontend_output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
