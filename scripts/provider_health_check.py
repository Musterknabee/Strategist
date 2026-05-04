#!/usr/bin/env python3
"""Emit a governed provider health snapshot (JSON). Optional keys only; no secret values."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_file

from strategy_validator.providers.health import build_provider_health_snapshot


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
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
            values[key] = value
    return values


def _merged_env(*, env_file: Path | None) -> dict[str, str]:
    merged = dict(os.environ)
    if env_file and env_file.is_file():
        for key, value in _parse_env_file(env_file).items():
            merged[key] = value
    return merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provider health snapshot for operator/evidence surfaces.")
    parser.add_argument("--env-file", default="", help="Merge KEY=VALUE pairs (optional).")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Samples manifest JSON (default: STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST or unset).",
    )
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON.")
    ns = parser.parse_args(argv)
    try:
        env_path = safe_input_file(ns.env_file, label="PROVIDER_HEALTH_ENV_FILE", required=False) if ns.env_file else None
        manifest = safe_input_file(ns.manifest, label="PROVIDER_HEALTH_MANIFEST", required=False) if ns.manifest else None
    except PathIntegrityError as exc:
        sys.stdout.write(json.dumps(path_error_payload(exc), sort_keys=True) + "\n")
        return 2
    env = _merged_env(env_file=env_path if env_path and env_path.is_file() else None)
    snap = build_provider_health_snapshot(
        env=env,
        samples_manifest_path=manifest,
        repo_root=_REPO_ROOT,
    )
    payload: dict[str, Any] = snap.model_dump(mode="json")
    indent = 2 if ns.json else None
    sys.stdout.write(json.dumps(payload, indent=indent, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
