#!/usr/bin/env python3
"""Fail-fast checks: frontend hook HTTP paths align with the UI public facade snapshot.

- Every literal GET path used in ui/strategist-web/hooks (strategistGetJson / useReadPlaneJsonQuery /
  strategistProbeGetJson) must exist in the facade (or probe/readiness allowlist).
- Every literal POST path in hooks must map to a POST mutation route with auth_required=true.
- Read-plane calls must not target POST-only facade paths.

Authoritative route list: docs/api/ui-public-facade.snapshot.json
Generated mirror: ui/strategist-web/lib/generated/ui-facade-contract.json (see generate_frontend_ui_facade_contract.py)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.generate_frontend_ui_facade_contract import build_contract_payload

_DEFAULT_SNAPSHOT = _REPO_ROOT / "docs" / "api" / "ui-public-facade.snapshot.json"
_HOOKS_DIR = _REPO_ROOT / "ui" / "strategist-web" / "hooks"
_GENERATED_JSON = _REPO_ROOT / "ui" / "strategist-web" / "lib" / "generated" / "ui-facade-contract.json"
_FRONTEND_ROUTES_CONTRACT = _REPO_ROOT / "ui" / "strategist-web" / "lib" / "contracts" / "ui-facade-routes.json"

# Not listed in the UI facade inventory (non-/ui/* read-plane or probes).
_ALLOWLIST_GET_EXACT = frozenset({"/", "/healthz"})
_ALLOWLIST_GET_PREFIX = ("/readiness/",)
_PROBE_PATHS = frozenset({"/livez", "/readyz"})


def _path_segments(path: str) -> list[str]:
    p = path.strip("/")
    if not p:
        return []
    return p.split("/")


def path_matches_template(instance: str, template: str) -> bool:
    """True if instance matches template where ``{param}`` segments accept any single path segment."""
    iseg = _path_segments(instance)
    tseg = _path_segments(template)
    if len(iseg) != len(tseg):
        return False
    for inst, tmpl in zip(iseg, tseg, strict=True):
        if len(tmpl) >= 2 and tmpl[0] == "{" and tmpl[-1] == "}":
            continue
        if inst != tmpl:
            return False
    return True


def facade_route_match(method: str, path_no_query: str, routes: list[dict[str, object]]) -> dict[str, object] | None:
    m = method.upper()
    for route in routes:
        if str(route["method"]).upper() != m:
            continue
        if path_matches_template(path_no_query, str(route["path"])):
            return route
    return None


def _strip_query(path: str) -> str:
    return path.split("?", 1)[0].strip()


def _normalize_backtick_path(raw: str) -> str:
    """Take static prefix of template literal before ? or ${."""
    cut = re.split(r"[\?$\{]", raw, maxsplit=1)
    return _strip_query(cut[0].strip())


_RE_STRATEGIST_GET = re.compile(
    r"strategistGetJson(?:<[^>]*>)?\(\s*(['\"])(/[^'\"]+)\1",
)
_RE_STRATEGIST_POST = re.compile(
    r"strategistPostJson(?:<[^>]*>)?\(\s*(['\"])(/[^'\"]+)\1",
)
_RE_PROBE_GET = re.compile(
    r"strategistProbeGetJson(?:<[^>]*>)?\(\s*(['\"])(/[^'\"]+)\1",
)
_RE_READ_PLANE_JSON = re.compile(
    r"useReadPlaneJsonQuery(?:<[^>]*>)?\(\s*[^,]+,\s*(['\"])(/[^'\"]+)\1",
)
_RE_READ_PLANE_BT = re.compile(
    r"useReadPlaneJsonQuery(?:<[^>]*>)?\(\s*[^,]+,\s*`([^`]+)`",
)
_RE_POST_TEMPLATE = re.compile(
    r"strategistPostJson(?:<[^>]*>)?\(\s*`([^`]+)`",
)


def _iter_hook_files(hooks_dir: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(hooks_dir.glob("*.ts")):
        if p.name.endswith(".test.ts") or p.name.endswith(".test.tsx"):
            continue
        out.append(p)
    return out


def extract_hook_http_usages(hooks_dir: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Return (usages as method, path, relpath), errors."""
    usages: list[tuple[str, str, str]] = []
    errors: list[str] = []
    for path in _iter_hook_files(hooks_dir):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for rx, method in (
            (_RE_STRATEGIST_GET, "GET"),
            (_RE_PROBE_GET, "GET"),
            (_RE_STRATEGIST_POST, "POST"),
            (_RE_READ_PLANE_JSON, "GET"),
        ):
            for m in rx.finditer(text):
                raw = m.group(2)
                usages.append((method, _strip_query(raw), rel))
        for m in _RE_READ_PLANE_BT.finditer(text):
            raw = _normalize_backtick_path(m.group(1))
            if raw.startswith("/ui") or raw.startswith("/readiness"):
                usages.append(("GET", raw, rel))
        for m in _RE_POST_TEMPLATE.finditer(text):
            raw = m.group(1)
            if "${" in raw:
                if "/ui/commands/" in raw:
                    usages.append(("POST", "/ui/commands/claim-item", rel))
                else:
                    errors.append(f"{rel}: unsupported POST template literal: {raw[:80]!r}")
            else:
                cleaned = _strip_query(_normalize_backtick_path(raw))
                usages.append(("POST", cleaned, rel))
    return usages, errors


def _allowlisted(method: str, path: str) -> bool:
    if method != "GET":
        return False
    if path in _ALLOWLIST_GET_EXACT:
        return True
    if path in _PROBE_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _ALLOWLIST_GET_PREFIX)


def validate_hooks_against_facade(
    snapshot: dict[str, object],
    hooks_dir: Path,
) -> list[str]:
    errors: list[str] = []
    routes_obj = snapshot.get("routes")
    if not isinstance(routes_obj, list):
        return ["snapshot.routes is not a list"]
    routes: list[dict[str, object]] = [r for r in routes_obj if isinstance(r, dict)]

    for r in routes:
        ps = str(r.get("payload_schema", "")).strip()
        if not ps:
            errors.append(f"facade route has empty payload_schema: {r.get('method')} {r.get('path')}")

    usages, ext_err = extract_hook_http_usages(hooks_dir)
    errors.extend(ext_err)

    for method, path, rel in usages:
        pq = _strip_query(path)
        if _allowlisted(method, pq):
            continue
        if not pq.startswith("/ui"):
            errors.append(f"{rel}: unexpected non-UI path {method} {pq!r}")
            continue
        hit = facade_route_match(method, pq, routes)
        if hit is None:
            errors.append(f"{rel}: {method} {pq!r} not found in UI facade snapshot")
            continue
        if method == "GET":
            kind = str(hit.get("kind", ""))
            if kind == "mutation":
                errors.append(f"{rel}: read-plane call targets mutation route {pq!r}")
            if str(hit.get("method")).upper() == "POST":
                errors.append(f"{rel}: GET usage matched POST-only route {pq!r}")
        if method == "POST":
            if str(hit.get("kind")) != "mutation":
                errors.append(f"{rel}: POST {pq!r} is not a mutation route in facade")
            if not bool(hit.get("auth_required")):
                errors.append(f"{rel}: POST {pq!r} must declare auth_required=true in facade")

    post_routes = [r for r in routes if str(r.get("method", "")).upper() == "POST"]
    for r in post_routes:
        if not bool(r.get("auth_required")):
            errors.append(f"facade POST {r.get('path')!r} must have auth_required=true")
        if str(r.get("kind")) != "mutation":
            errors.append(f"facade POST {r.get('path')!r} must have kind=mutation")

    return errors


def _verify_generated_matches_snapshot(snapshot: dict[str, object]) -> list[str]:
    errors: list[str] = []
    expected = build_contract_payload(snapshot)
    if not _GENERATED_JSON.is_file():
        return [f"missing generated contract (run: python scripts/generate_frontend_ui_facade_contract.py): {_GENERATED_JSON}"]
    current = json.loads(_GENERATED_JSON.read_text(encoding="utf-8"))
    if current != expected:
        errors.append(
            f"generated ui-facade-contract.json drift; regenerate with "
            f"python scripts/generate_frontend_ui_facade_contract.py (compare routes_sha256 "
            f"{current.get('routes_sha256')!r} vs expected {expected.get('routes_sha256')!r})"
        )
    return errors


def _verify_frontend_routes_contract(snapshot: dict[str, object]) -> list[str]:
    if not _FRONTEND_ROUTES_CONTRACT.is_file():
        return [f"missing {_FRONTEND_ROUTES_CONTRACT}"]
    fe = json.loads(_FRONTEND_ROUTES_CONTRACT.read_text(encoding="utf-8"))
    if fe.get("routes_sha256") != snapshot.get("routes_sha256"):
        return ["ui/strategist-web/lib/contracts/ui-facade-routes.json routes_sha256 does not match snapshot"]
    if fe.get("route_count") != snapshot.get("route_count"):
        return ["ui/strategist-web/lib/contracts/ui-facade-routes.json route_count does not match snapshot"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate frontend UI hook paths against the facade snapshot.")
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--snapshot", type=Path, default=_DEFAULT_SNAPSHOT)
    parser.add_argument("--hooks-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    repo = args.repo_root.resolve()
    snap_path = args.snapshot if args.snapshot.is_absolute() else repo / args.snapshot
    hooks_dir = args.hooks_dir or (repo / "ui" / "strategist-web" / "hooks")

    if not snap_path.is_file():
        print(f"missing snapshot: {snap_path}", file=sys.stderr)
        return 1
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    errors.extend(_verify_generated_matches_snapshot(snapshot))
    errors.extend(_verify_frontend_routes_contract(snapshot))
    errors.extend(validate_hooks_against_facade(snapshot, hooks_dir))

    if errors:
        print("frontend_ui_contract_check FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("frontend_ui_contract_check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
