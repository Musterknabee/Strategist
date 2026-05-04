"""Load ./deployment.env (simple KEY=VALUE) and exec single_tenant_preflight with the same argv tail."""
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
        env_path = safe_input_file(root / "deployment.env", label="RUN_PREFLIGHT_ENV_FILE")
    except PathIntegrityError as exc:
        _emit_path_error(exc)
        return 2
    assert env_path is not None
    _load_env_file(env_path)
    r = subprocess.run(
        [sys.executable, "-m", "strategy_validator.cli.single_tenant_preflight", *sys.argv[1:]],
        cwd=root,
        env=os.environ.copy(),
    )
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
