"""Single-tenant deployment environment file validator.

This command validates an operator-provided env file before it is used to boot
or preflight the backend-only single-tenant deployment.  It intentionally does
not load secrets into the process-wide environment and does not contact the API.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from strategy_validator.core.token_policy import (
    REQUIRED_MUTATION_SCOPES,
    is_placeholder_token,
    missing_required_mutation_scopes,
    split_token_scopes,
)

_SCHEMA_VERSION = "single_tenant_deployment_env_check/v1"
_REQUIRED_KEYS = (
    "STRATEGY_VALIDATOR_MODE",
    "STRATEGY_VALIDATOR_API_TOKEN",
    "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
    "STRATEGY_VALIDATOR_LEDGER_DB_PATH",
    "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR",
    "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
)
_REQUIRED_SCOPES = REQUIRED_MUTATION_SCOPES
# canonical required scopes:
# operator:command:write
# operator:projection:read
_PATH_KEYS = (
    "STRATEGY_VALIDATOR_LEDGER_DB_PATH",
    "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR",
    "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
)
_OPTIONAL_HOST_PORT_KEY = "STRATEGY_VALIDATOR_HOST_PORT"
# These roots are the writable volumes declared by the generated single-tenant
# Docker Compose/systemd envelope.  Keeping env paths inside this envelope avoids
# a false-positive env check followed by a first-boot failure under the
# read-only container filesystem.
_CONTAINER_LEDGER_ROOT = PurePosixPath("/var/lib/strategy-validator")
_CONTAINER_BACKUP_ROOT = PurePosixPath("/var/backups/strategy-validator")
_CONTAINER_ARTIFACT_ROOT = PurePosixPath("/var/lib/strategy-validator")
_CONTAINER_PATH_POLICY = {
    "STRATEGY_VALIDATOR_LEDGER_DB_PATH": (_CONTAINER_LEDGER_ROOT, "LEDGER_PATH_OUTSIDE_WRITABLE_VOLUME"),
    "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR": (_CONTAINER_BACKUP_ROOT, "BACKUP_DIR_OUTSIDE_WRITABLE_VOLUME"),
    "STRATEGY_VALIDATOR_ARTIFACT_ROOT": (_CONTAINER_ARTIFACT_ROOT, "ARTIFACT_ROOT_OUTSIDE_WRITABLE_VOLUME"),
}
@dataclass(frozen=True)
class EnvIssue:
    key: str
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class EnvCheckReport:
    schema_version: str
    ok: bool
    env_file: str
    checked_key_count: int
    required_key_count: int
    issue_count: int
    warning_count: int
    issues: tuple[EnvIssue, ...]
    values: dict[str, object]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "env_file": self.env_file,
            "checked_key_count": self.checked_key_count,
            "required_key_count": self.required_key_count,
            "issue_count": self.issue_count,
            "warning_count": self.warning_count,
            "issues": [asdict(issue) for issue in self.issues],
            "values": self.values,
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




def absolute_path_preserving_symlink(path: str | Path) -> Path:
    """Return an absolute path without resolving the final symlink target.

    Deployment gates must reject symlinked secret-bearing env files. Calling
    ``Path.resolve()`` before validation follows symlinks and hides the exact
    operator-provided path from ``Path.is_symlink()``. This helper gives callers
    stable absolute paths for reports while preserving symlink observability.
    """

    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate


def symlink_components_preserving_path(path: str | Path) -> tuple[Path, ...]:
    """Return symlink components without resolving through them.

    Operator-facing deployment commands write or read secret/evidence artifacts.
    They need absolute, stable paths for reports, but must not call
    ``Path.resolve()`` before checking because that follows symlinks.  This
    helper detects symlinks in existing parents as well as the final component.
    Missing future leaf paths are allowed; existing symlinked parents are not.
    """

    absolute = absolute_path_preserving_symlink(path)
    candidates = [item for item in reversed(absolute.parents) if item != item.parent]
    candidates.append(absolute)
    return tuple(candidate for candidate in candidates if candidate.is_symlink())


def has_symlink_component(path: str | Path) -> bool:
    """Return True if any existing component of ``path`` is a symlink."""

    return bool(symlink_components_preserving_path(path))


def parse_env_file(path: str | Path) -> tuple[dict[str, str], list[EnvIssue]]:
    """Parse a simple KEY=VALUE env file without shell expansion."""

    target = absolute_path_preserving_symlink(path)
    issues: list[EnvIssue] = []
    values: dict[str, str] = {}
    symlinks = symlink_components_preserving_path(target)
    if target in symlinks:
        return values, [
            EnvIssue(
                "<file>",
                "ENV_FILE_IS_SYMLINK",
                "ERROR",
                f"deployment env file must be a regular file, not a symlink: {target}",
            )
        ]
    if symlinks:
        joined = ", ".join(str(item) for item in symlinks)
        return values, [
            EnvIssue(
                "<file>",
                "ENV_FILE_PARENT_IS_SYMLINK",
                "ERROR",
                f"deployment env file must not be read through symlinked parent directories: {joined}",
            )
        ]
    if not target.exists():
        return values, [EnvIssue("<file>", "ENV_FILE_MISSING", "ERROR", f"env file does not exist: {target}")]
    if not target.is_file():
        return values, [EnvIssue("<file>", "ENV_FILE_NOT_FILE", "ERROR", f"env path is not a file: {target}")]

    for line_number, raw_line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            issues.append(EnvIssue("<line>", "ENV_LINE_INVALID", "ERROR", f"line {line_number} is not KEY=VALUE"))
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value).strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            issues.append(EnvIssue(key or "<empty>", "ENV_KEY_INVALID", "ERROR", f"line {line_number} has invalid env key"))
            continue
        if key in values:
            issues.append(EnvIssue(key, "ENV_KEY_DUPLICATE", "ERROR", f"{key} is declared more than once"))
        values[key] = value
    return values, issues






def _is_under_posix_root(raw_path: str, root: PurePosixPath) -> bool:
    """Return True when a deployment path is inside the generated container volume root."""

    try:
        candidate = PurePosixPath(raw_path)
    except Exception:  # pragma: no cover - PurePath is defensive, keep diagnostics fail-closed.
        return False
    if not candidate.is_absolute():
        return False
    if ".." in candidate.parts:
        return False
    return candidate == root or root in candidate.parents


def _deployment_path_is_absolute_durable(raw: str) -> bool:
    """Return True when a deployment env path is absolute and has no path-traversal segments.

    Container handoff env files use POSIX absolute paths (``/var/lib/...``). On Windows,
    ``Path('/var/...').is_absolute()`` is false, so we treat leading ``/`` as POSIX via
    :class:`PurePosixPath`. Host-native absolute paths (e.g. ``C:\\...`` on Windows) use
    :class:`Path` when the value does not start with ``/``.
    """

    text = raw.strip()
    if not text or ".." in PurePosixPath(text).parts:
        return False
    try:
        if text.startswith("/"):
            return PurePosixPath(text).is_absolute()
        return Path(text).is_absolute()
    except Exception:
        return False

def _env_file_permissions_issue(path: str | Path, *, token: str) -> EnvIssue | None:
    """Return an ERROR when a real secret-bearing env file is group/world readable.

    The deployment env contains bearer tokens. On POSIX targets the operator
    copy should normally be 0600; Windows ACL semantics are intentionally not
    guessed here. Template/placeholder files are already rejected by token policy
    and are not double-reported as permission failures.
    """

    if os.name == "nt" or not token or is_placeholder_token(token):
        return None
    target = Path(path)
    try:
        mode = target.stat().st_mode & 0o777
    except OSError:
        return None
    if mode & 0o077:
        return EnvIssue(
            "<file>",
            "ENV_FILE_PERMISSIONS_TOO_OPEN",
            "ERROR",
            f"deployment env file permissions must not allow group/world access; found {mode:04o}, expected 0600-style private permissions",
        )
    return None



def _validate_optional_host_port(values: dict[str, str]) -> tuple[int | None, EnvIssue | None]:
    """Validate the optional host port shared by Compose, systemd, and smoke.

    The generated runtime binds the API container to loopback on this host-side
    port.  Validating it with the env checker prevents a config that passes
    readiness but later makes Docker Compose/systemd fail at startup or makes
    smoke check a different port than the service actually exposes.
    """

    raw = values.get(_OPTIONAL_HOST_PORT_KEY, "").strip()
    if not raw:
        return None, None
    if not re.fullmatch(r"[0-9]{1,5}", raw):
        return None, EnvIssue(
            _OPTIONAL_HOST_PORT_KEY,
            "HOST_PORT_INVALID",
            "ERROR",
            "STRATEGY_VALIDATOR_HOST_PORT must be a numeric TCP port between 1 and 65535",
        )
    value = int(raw)
    if value < 1 or value > 65535:
        return None, EnvIssue(
            _OPTIONAL_HOST_PORT_KEY,
            "HOST_PORT_INVALID",
            "ERROR",
            "STRATEGY_VALIDATOR_HOST_PORT must be between 1 and 65535",
        )
    return value, None

def build_single_tenant_deployment_env_check(env_file: str | Path) -> EnvCheckReport:
    values, parse_issues = parse_env_file(env_file)
    issues = list(parse_issues)

    for key in _REQUIRED_KEYS:
        if not values.get(key, "").strip():
            issues.append(EnvIssue(key, "REQUIRED_ENV_MISSING", "ERROR", f"{key} is required for single-tenant production deployment"))

    mode = values.get("STRATEGY_VALIDATOR_MODE", "").strip().upper()
    if mode and mode != "PRODUCTION":
        issues.append(EnvIssue("STRATEGY_VALIDATOR_MODE", "MODE_NOT_PRODUCTION", "ERROR", "single-tenant deployment env must set PRODUCTION mode"))

    token = values.get("STRATEGY_VALIDATOR_API_TOKEN", "")
    research_token = values.get("STRATEGY_VALIDATOR_RESEARCH_API_TOKEN", "")
    secret_for_permission_check = ""
    for candidate in (token, research_token):
        if candidate and not is_placeholder_token(candidate):
            secret_for_permission_check = candidate
            break
    permissions_issue = _env_file_permissions_issue(env_file, token=secret_for_permission_check)
    if permissions_issue is not None:
        issues.append(permissions_issue)
    if token and is_placeholder_token(token):
        issues.append(EnvIssue("STRATEGY_VALIDATOR_API_TOKEN", "API_TOKEN_PLACEHOLDER", "ERROR", "API token is missing, too short, low-entropy-looking, or placeholder-like"))

    if research_token:
        if is_placeholder_token(research_token):
            issues.append(EnvIssue("STRATEGY_VALIDATOR_RESEARCH_API_TOKEN", "RESEARCH_TOKEN_PLACEHOLDER", "ERROR", "configured research token is missing, too short, low-entropy-looking, or placeholder-like"))
        if token and research_token == token:
            issues.append(EnvIssue("STRATEGY_VALIDATOR_RESEARCH_API_TOKEN", "RESEARCH_TOKEN_REUSES_MUTATION_TOKEN", "WARNING", "research token should be separate from mutation API token"))
    else:
        issues.append(EnvIssue("STRATEGY_VALIDATOR_RESEARCH_API_TOKEN", "RESEARCH_TOKEN_NOT_CONFIGURED", "WARNING", "research routes will rely on compatibility fallback or stay unusable"))

    scopes = split_token_scopes(values.get("STRATEGY_VALIDATOR_API_TOKEN_SCOPES", ""))
    missing_scopes = list(missing_required_mutation_scopes(scopes))
    if missing_scopes:
        issues.append(EnvIssue("STRATEGY_VALIDATOR_API_TOKEN_SCOPES", "API_TOKEN_SCOPES_MISSING", "ERROR", "missing required scope(s): " + ", ".join(missing_scopes)))

    host_port, host_port_issue = _validate_optional_host_port(values)
    if host_port_issue is not None:
        issues.append(host_port_issue)

    mounted_path_policy_ok = True
    for key in _PATH_KEYS:
        raw = values.get(key, "").strip()
        if raw and not _deployment_path_is_absolute_durable(raw):
            mounted_path_policy_ok = False
            issues.append(EnvIssue(key, "DEPLOYMENT_PATH_NOT_ABSOLUTE", "ERROR", f"{key} must be an absolute durable path"))
            continue
        if raw:
            root, code = _CONTAINER_PATH_POLICY[key]
            if not _is_under_posix_root(raw, root):
                mounted_path_policy_ok = False
                issues.append(
                    EnvIssue(
                        key,
                        code,
                        "ERROR",
                        f"{key} must be inside the generated single-tenant writable container root {root}",
                    )
                )

    error_count = sum(1 for issue in issues if issue.severity == "ERROR")
    warning_count = sum(1 for issue in issues if issue.severity == "WARNING")
    safe_values = {
        "mode": mode or None,
        "api_token_configured": bool(token),
        "api_token_placeholder_like": bool(token and is_placeholder_token(token)),
        "api_token_scope_count": len(scopes),
        "api_token_missing_required_scopes": missing_scopes,
        "research_api_token_configured": bool(research_token),
        "host_port": host_port,
        "host_port_configured": bool(values.get(_OPTIONAL_HOST_PORT_KEY, "").strip()),
        "ledger_database_path": values.get("STRATEGY_VALIDATOR_LEDGER_DB_PATH", ""),
        "ledger_backup_dir": values.get("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", ""),
        "artifact_root": values.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", ""),
        "container_writable_path_policy_ok": mounted_path_policy_ok,
        "container_writable_roots": {
            "ledger": str(_CONTAINER_LEDGER_ROOT),
            "backup": str(_CONTAINER_BACKUP_ROOT),
            "artifact": str(_CONTAINER_ARTIFACT_ROOT),
        },
    }
    return EnvCheckReport(
        schema_version=_SCHEMA_VERSION,
        ok=error_count == 0,
        env_file=str(Path(env_file)),
        checked_key_count=len(values),
        required_key_count=len(_REQUIRED_KEYS),
        issue_count=error_count,
        warning_count=warning_count,
        issues=tuple(issues),
        values=safe_values,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a single-tenant production deployment env file without loading secrets.")
    parser.add_argument("env_file", nargs="?", default="deployment.env", help="Path to the operator deployment env file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for stable automation.")
    parser.add_argument("--require-valid", action="store_true", help="Exit non-zero if any ERROR issue is found.")
    ns = parser.parse_args(argv)
    report = build_single_tenant_deployment_env_check(ns.env_file)
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_valid and not report.ok else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
