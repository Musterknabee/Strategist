#!/usr/bin/env python3
"""Start the FastAPI process with ./deployment.env merged into the child environment.

Binds loopback by default (single-tenant local smoke). Does not print secrets.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


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


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env_path = root / "deployment.env"
    if not env_path.is_file():
        sys.stderr.write(f"missing {env_path}\n")
        return 2
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
