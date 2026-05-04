#!/usr/bin/env python3
"""Start the FastAPI process with ./deployment.env merged into the child environment.

Binds loopback by default (single-tenant local smoke). Does not print secrets.
"""
from __future__ import annotations

import os
import re
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_file


def _resolve_container_style_paths_for_local_os() -> None:
    """Make /var/... style paths from deployment.env work on Windows dev hosts.

    ``Path('/var/...').resolve()`` maps to the current drive (e.g. ``C:\\var\\...``),
    matching single-tenant preflight ``--prepare`` behavior.
    """
    for key in (
        "STRATEGY_VALIDATOR_LEDGER_DB_PATH",
        "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR",
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
    ):
        raw = os.environ.get(key, "").strip()
        if not raw:
            continue
        os.environ[key] = str(Path(raw).expanduser().resolve())


def _load_env_file(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if "#" in value and not (value.startswith('"') or value.startswith("'")):
            value = value.split("#", 1)[0].rstrip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            os.environ[key] = value


def _emit_path_error(error: PathIntegrityError) -> None:
    sys.stderr.write(json.dumps(path_error_payload(error, schema_version="local_deployment_helper_path_error/v1"), sort_keys=True) + "\n")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        env_path = safe_input_file(root / "deployment.env", label="RUN_LOCAL_API_ENV_FILE")
    except PathIntegrityError as exc:
        _emit_path_error(exc)
        return 2
    assert env_path is not None
    _load_env_file(env_path)
    _resolve_container_style_paths_for_local_os()
    child_env = os.environ.copy()
    child_env["PYTHONPATH"] = str(root)
    host = "127.0.0.1"
    port = "8000"
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = sys.argv[2]
    return int(
        subprocess.call(
            [sys.executable, "-m", "strategy_validator.cli.api", "--host", host, "--port", port],
            cwd=str(root),
            env=child_env,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
