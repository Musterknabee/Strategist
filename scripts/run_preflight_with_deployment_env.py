"""Load ./deployment.env (simple KEY=VALUE) and exec single_tenant_preflight with the same argv tail."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


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
    r = subprocess.run(
        [sys.executable, "-m", "strategy_validator.cli.single_tenant_preflight", *sys.argv[1:]],
        cwd=root,
        env=os.environ.copy(),
    )
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
