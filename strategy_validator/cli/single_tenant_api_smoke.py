#!/usr/bin/env python3
"""HTTP smoke check for a booted single-tenant backend API.

The script uses only the Python standard library so it can run from CI, a host
shell, or a minimal container without pytest/httpx.  It verifies the public
health probes, UI facade contract, and mutation auth boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

_SCHEMA_VERSION = "single_tenant_api_http_smoke/v1"
_ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE = "SMOKE_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE"
_ERROR_ENV_FILE_IS_SYMLINK = "SMOKE_ENV_FILE_IS_SYMLINK"
_ERROR_ENV_FILE_PARENT_IS_SYMLINK = "SMOKE_ENV_FILE_PARENT_IS_SYMLINK"
_ERROR_ENV_FILE_NOT_FILE = "SMOKE_ENV_FILE_NOT_FILE"
_ERROR_ENV_FILE_MISSING = "SMOKE_ENV_FILE_MISSING"

SmokeTokenSource = Literal["auto", "env", "env-file"]


@dataclass(frozen=True)
class SmokeTokenResolution:
    """Resolved bearer token plus non-secret diagnostics for operator visibility."""

    token: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SmokeStep:
    name: str
    method: str
    path: str
    expected_status: tuple[int, ...]
    status_code: int | None
    ok: bool
    detail: str


@dataclass(frozen=True)
class SmokeReport:
    schema_version: str
    ok: bool
    base_url: str
    step_count: int
    failed_step_count: int
    steps: tuple[SmokeStep, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "base_url": self.base_url,
            "step_count": self.step_count,
            "failed_step_count": self.failed_step_count,
            "steps": [asdict(step) for step in self.steps],
        }


def _strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            quote = None if quote == char else char if quote is None else quote
            continue
        if char == "#" and quote is None:
            before = value[index - 1:index]
            if not before or before.isspace():
                return value[:index].rstrip()
    return value.strip()


def _absolute_path_preserving_symlink(path: str | Path) -> Path:
    """Return an absolute path without following symlink components.

    The smoke runner is copied into generated deployment bundles as a standalone
    stdlib script, so it cannot import the main deployment env validator.  Keep
    this helper local and deliberately avoid ``Path.resolve()`` because that
    would hide symlinked env-file inputs before validation.
    """

    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate


def _symlink_components_preserving_path(path: str | Path) -> tuple[Path, ...]:
    absolute = _absolute_path_preserving_symlink(path)
    candidates = [item for item in reversed(absolute.parents) if item != item.parent]
    candidates.append(absolute)
    return tuple(candidate for candidate in candidates if candidate.is_symlink())


def _validate_env_file_path(path: str | Path) -> Path:
    """Validate ``--env-file`` before reading token/base-URL material.

    This smoke script often runs after Docker has consumed the same env file. A
    symlinked or non-regular path would make the post-deploy proof depend on
    filesystem indirection rather than the reviewed deployment artifact.
    """

    target = _absolute_path_preserving_symlink(path)
    symlinks = _symlink_components_preserving_path(target)
    if target in symlinks:
        raise ValueError(f"{_ERROR_ENV_FILE_IS_SYMLINK}: --env-file must be a regular file, not a symlink: {target}")
    if symlinks:
        joined = ", ".join(str(item) for item in symlinks)
        raise ValueError(f"{_ERROR_ENV_FILE_PARENT_IS_SYMLINK}: --env-file must not be under symlinked parent directories: {joined}")
    if not target.exists():
        raise ValueError(f"{_ERROR_ENV_FILE_MISSING}: --env-file does not exist: {target}")
    if not target.is_file():
        raise ValueError(f"{_ERROR_ENV_FILE_NOT_FILE}: --env-file must be a regular file: {target}")
    return target


def _parse_env_file(path: str | Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE env file without shell evaluation.

    This intentionally duplicates the small parser shape used by the deployment
    env check instead of importing project modules, because generated deployment
    bundles copy this file as a standalone stdlib smoke runner.
    """

    target = _validate_env_file_path(path)
    values: dict[str, str] = {}
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value).strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value
    return values




def resolve_smoke_base_url(
    *,
    base_url: str | None = None,
    env_file: str | Path | None = None,
    host: str = "127.0.0.1",
    default_port: str = "8000",
) -> str:
    """Resolve the smoke target URL from explicit URL, env, or deployment env port.

    The generated Compose template binds the API to
    127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000.  Deriving the
    smoke URL from the same deployment env avoids a false smoke failure when an
    operator uses a non-default host port.
    """

    explicit = (base_url or "").strip()
    if explicit:
        return explicit.rstrip("/")

    env_url = os.environ.get("STRATEGY_VALIDATOR_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    file_values = _parse_env_file(env_file) if env_file else {}
    file_url = file_values.get("STRATEGY_VALIDATOR_BASE_URL", "").strip()
    if file_url:
        return file_url.rstrip("/")

    port = os.environ.get("STRATEGY_VALIDATOR_HOST_PORT", "").strip()
    if not port:
        port = file_values.get("STRATEGY_VALIDATOR_HOST_PORT", "").strip()
    if not port:
        port = default_port
    if not re.fullmatch(r"[0-9]{1,5}", port):
        raise ValueError(
            "STRATEGY_VALIDATOR_HOST_PORT must be a numeric TCP port when deriving smoke base URL"
        )
    port_int = int(port)
    if port_int < 1 or port_int > 65535:
        raise ValueError(
            "STRATEGY_VALIDATOR_HOST_PORT must be between 1 and 65535 when deriving smoke base URL"
        )
    return f"http://{host}:{port_int}"


def _sha256_prefix(value: str, *, hex_chars: int = 16) -> str:
    """First hex_chars characters of SHA256 (hex) for operator-safe fingerprinting."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:hex_chars]


def resolve_smoke_token(
    *,
    token: str | None = None,
    token_env_var: str = "STRATEGY_VALIDATOR_API_TOKEN",
    env_file: str | Path | None = None,
    token_source: SmokeTokenSource = "auto",
) -> SmokeTokenResolution:
    """Resolve the smoke token without requiring it in argv.

    ``--token`` (deprecated) always wins when non-empty. Otherwise:

    - ``auto``: process environment, then ``--env-file`` (legacy precedence). If both
      define a non-empty token and they differ, a warning is returned (emit to stderr
      in the CLI) with SHA256 prefixes only—never raw secrets.
    - ``env``: process environment only.
    - ``env-file``: ``--env-file`` only; requires a non-empty env file path.
    """

    if token:
        return SmokeTokenResolution(token=token, warnings=())

    if not token_env_var:
        raise ValueError("token_env_var must be non-empty")

    env_path = Path(env_file) if env_file and str(env_file).strip() else None

    if token_source == "env-file":
        if env_path is None:
            raise ValueError(
                f"{_ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE}: "
                "--token-source env-file requires --env-file"
            )
        file_value = _parse_env_file(env_path).get(token_env_var, "").strip()
        if not file_value:
            raise ValueError(
                f"mutation API token not found for {token_env_var} in --env-file "
                f"(token-source env-file)"
            )
        return SmokeTokenResolution(token=file_value, warnings=())

    if token_source == "env":
        env_value = os.environ.get(token_env_var, "").strip()
        if not env_value:
            raise ValueError(
                f"mutation API token not found in process environment ({token_env_var}); "
                "token-source env requires this variable to be set"
            )
        return SmokeTokenResolution(token=env_value, warnings=())

    # auto
    env_value = os.environ.get(token_env_var, "").strip()
    file_value = ""
    if env_path is not None:
        file_value = _parse_env_file(env_path).get(token_env_var, "").strip()

    warnings: list[str] = []
    if env_value and file_value and env_value != file_value:
        warnings.append(
            "single_tenant_api_smoke: "
            f"{token_env_var} differs between process environment and --env-file; "
            "using process environment (auto precedence). "
            f"env_sha256_prefix={_sha256_prefix(env_value)} "
            f"file_sha256_prefix={_sha256_prefix(file_value)}. "
            "For deterministic alignment with Docker --env-file, use "
            "--token-source env-file --env-file <path>, or unset the variable in your shell."
        )

    if env_value:
        return SmokeTokenResolution(token=env_value, warnings=tuple(warnings))
    if file_value:
        return SmokeTokenResolution(token=file_value, warnings=tuple(warnings))
    raise ValueError(
        f"mutation API token is required; set {token_env_var} in the environment, "
        "pass --env-file, or use deprecated --token"
    )


def _request_json(
    *,
    base_url: str,
    method: str,
    path: str,
    timeout: float,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | None, str]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    data = None if body is None else json.dumps(body, sort_keys=True).encode("utf-8")
    request = Request(url, data=data, method=method.upper())
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - operator-supplied local deployment URL.
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw.strip() else None
            return int(response.status), payload, "ok"
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = None
        try:
            payload = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            payload = None
        return int(exc.code), payload, raw[:240]
    except (URLError, TimeoutError, OSError) as exc:
        return 0, None, str(exc)


def _step(
    *,
    name: str,
    method: str,
    path: str,
    expected_status: tuple[int, ...],
    base_url: str,
    timeout: float,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    validate_payload: str | None = None,
) -> SmokeStep:
    status, payload, detail = _request_json(
        base_url=base_url,
        method=method,
        path=path,
        timeout=timeout,
        headers=headers,
        body=body,
    )
    ok = status in expected_status
    if ok and validate_payload == "ui_facade":
        ok = bool(
            isinstance(payload, dict)
            and payload.get("schema_version") == "ui_public_facade_inventory/v1"
            and payload.get("surface") == "ui"
            and payload.get("frontend_readiness_claimed") is False
            and payload.get("read_plane_only") is True
            and isinstance(payload.get("frontend_package_detected_by_backend"), bool)
            and payload.get("frontend_package_present") == payload.get("frontend_package_detected_by_backend")
            and payload.get("frontend_runtime_reachable") is None
            and isinstance(payload.get("frontend_operator_console_hint"), str)
            and len(str(payload.get("frontend_operator_console_hint"))) > 10
        )
        if not ok:
            detail = "UI facade payload did not match expected backend-only contract"
    if ok and validate_payload == "command_receipt":
        ok = bool(isinstance(payload, dict) and payload.get("schema_version") == "ui_operator_command_receipt/v1" and payload.get("accepted") is True)
        if not ok:
            detail = "authenticated command did not return accepted ui_operator_command_receipt/v1"
    return SmokeStep(
        name=name,
        method=method.upper(),
        path=path,
        expected_status=expected_status,
        status_code=status if status else None,
        ok=ok,
        detail=detail if not ok else "ok",
    )


def build_single_tenant_api_smoke(
    *,
    base_url: str,
    token: str,
    timeout: float = 5.0,
    operator_id: str = "deployment-smoke",
) -> SmokeReport:
    command_body = {
        "operator_id": operator_id,
        "work_item_key": "deployment-smoke",
        "idempotency_key": f"deployment-smoke-{uuid.uuid4().hex}",
    }
    steps = [
        _step(name="healthz", method="GET", path="/healthz", expected_status=(200,), base_url=base_url, timeout=timeout),
        _step(name="readyz", method="GET", path="/readyz", expected_status=(200,), base_url=base_url, timeout=timeout),
        _step(name="ui_facade", method="GET", path="/ui/facade", expected_status=(200,), base_url=base_url, timeout=timeout, validate_payload="ui_facade"),
        _step(name="unauthenticated_ui_command_rejected", method="POST", path="/ui/commands/claim-item", expected_status=(401,), base_url=base_url, timeout=timeout, body=command_body),
        _step(
            name="authenticated_ui_command_accepted",
            method="POST",
            path="/ui/commands/claim-item",
            expected_status=(200,),
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}", "X-Strategy-Validator-Operator": operator_id},
            body=command_body,
            validate_payload="command_receipt",
        ),
    ]
    failed = tuple(step for step in steps if not step.ok)
    return SmokeReport(
        schema_version=_SCHEMA_VERSION,
        ok=not failed,
        base_url=base_url,
        step_count=len(steps),
        failed_step_count=len(failed),
        steps=tuple(steps),
    )


def _error_code_from_value_error(exc: ValueError) -> str | None:
    msg = str(exc)
    for code in (
        _ERROR_TOKEN_SOURCE_ENV_FILE_REQUIRES_ENV_FILE,
        _ERROR_ENV_FILE_IS_SYMLINK,
        _ERROR_ENV_FILE_PARENT_IS_SYMLINK,
        _ERROR_ENV_FILE_NOT_FILE,
        _ERROR_ENV_FILE_MISSING,
    ):
        if msg.startswith(code):
            return code
    return None


def _token_resolution_error_payload(*, base_url: str, exc: ValueError) -> dict[str, object]:
    msg = str(exc)
    payload: dict[str, object] = {
        "schema_version": _SCHEMA_VERSION,
        "ok": False,
        "base_url": base_url,
        "step_count": 0,
        "failed_step_count": 1,
        "error": msg,
    }
    error_code = _error_code_from_value_error(exc)
    if error_code:
        payload["error_code"] = error_code
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run HTTP smoke checks against a booted single-tenant strategy-validator API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Token sources (after optional deprecated --token):\n"
            "  auto      — process env, then --env-file (default). Warns on mismatch (stderr, fingerprints only).\n"
            "  env       — process environment only.\n"
            "  env-file  — deployment env file only; requires --env-file.\n"
            "\n"
            "PowerShell / local Docker (align token with docker run --env-file):\n"
            "  python -m strategy_validator.cli.single_tenant_api_smoke `\n"
            "    --base-url http://127.0.0.1:8000 `\n"
            "    --env-file deployment.env `\n"
            "    --token-source env-file `\n"
            "    --require-pass\n"
        ),
    )
    parser.add_argument("--base-url", default="", help="Base URL for the booted backend API. Defaults to STRATEGY_VALIDATOR_BASE_URL or STRATEGY_VALIDATOR_HOST_PORT from --env-file/environment.")
    parser.add_argument("--token", default="", help="Deprecated compatibility path: mutation API token. Prefer --env-file or --token-env-var so the token is not exposed in argv.")
    parser.add_argument("--token-env-var", default="STRATEGY_VALIDATOR_API_TOKEN", help="Environment variable name containing the mutation API token.")
    parser.add_argument(
        "--token-source",
        default="auto",
        choices=["auto", "env", "env-file"],
        help="How to resolve the mutation API token when --token is not set (default: auto).",
    )
    parser.add_argument("--env-file", default="", help="Optional deployment env file to read the mutation API token from without shell evaluation.")
    parser.add_argument("--operator-id", default="deployment-smoke", help="Operator principal header used for the authenticated command.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout in seconds.")
    parser.add_argument("--wait-seconds", type=float, default=30.0, help="Total time to wait for /healthz before running checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for automation.")
    parser.add_argument("--require-pass", action="store_true", help="Exit non-zero if any smoke step fails.")
    ns = parser.parse_args(argv)

    if ns.env_file:
        try:
            _validate_env_file_path(ns.env_file)
        except ValueError as exc:
            error_payload = {
                "schema_version": _SCHEMA_VERSION,
                "ok": False,
                "base_url": ns.base_url or "",
                "step_count": 0,
                "failed_step_count": 1,
                "error": str(exc),
            }
            error_code = _error_code_from_value_error(exc)
            if error_code:
                error_payload["error_code"] = error_code
            sys.stdout.write(json.dumps(error_payload, indent=2, sort_keys=True) + "\n")
            return 2 if ns.require_pass else 0

    try:
        base_url = resolve_smoke_base_url(base_url=ns.base_url or None, env_file=ns.env_file or None)
    except ValueError as exc:
        error_payload = {
            "schema_version": _SCHEMA_VERSION,
            "ok": False,
            "base_url": ns.base_url or "",
            "step_count": 0,
            "failed_step_count": 1,
            "error": str(exc),
        }
        error_code = _error_code_from_value_error(exc)
        if error_code:
            error_payload["error_code"] = error_code
        sys.stdout.write(json.dumps(error_payload, indent=2, sort_keys=True) + "\n")
        return 2 if ns.require_pass else 0

    try:
        resolution = resolve_smoke_token(
            token=ns.token or None,
            token_env_var=ns.token_env_var,
            env_file=ns.env_file or None,
            token_source=cast(SmokeTokenSource, ns.token_source),
        )
    except ValueError as exc:
        error_payload = _token_resolution_error_payload(base_url=base_url, exc=exc)
        sys.stdout.write(json.dumps(error_payload, indent=2, sort_keys=True) + "\n")
        return 2 if ns.require_pass else 0

    for warning in resolution.warnings:
        print(warning, file=sys.stderr)

    deadline = time.monotonic() + max(ns.wait_seconds, 0.0)
    while True:
        status, _payload, _detail = _request_json(base_url=base_url, method="GET", path="/healthz", timeout=min(ns.timeout, 5.0))
        if status == 200 or time.monotonic() >= deadline:
            break
        time.sleep(1.0)

    report = build_single_tenant_api_smoke(
        base_url=base_url,
        token=resolution.token,
        timeout=ns.timeout,
        operator_id=ns.operator_id,
    )
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_pass and not report.ok else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
