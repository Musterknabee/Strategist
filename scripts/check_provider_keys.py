#!/usr/bin/env python3
"""Report optional provider key configuration without printing secrets."""
from __future__ import annotations

import argparse
import hashlib
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

from strategy_validator.contracts.provider_capabilities import (
    ProviderAccessType,
    all_provider_capabilities,
    capability_by_provider_id,
)


def _truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _sha16(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


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


def _first_configured_key(env: dict[str, str], names: tuple[str, ...]) -> tuple[str | None, str | None]:
    for name in names:
        raw = env.get(name, "").strip()
        if raw and raw.upper() not in {"CHANGEME", "REPLACE_ME", "YOUR_KEY_HERE"}:
            return name, raw
    return None, None


def _alpaca_live_violations(env: dict[str, str]) -> list[str]:
    issues: list[str] = []
    mode = (env.get("ALPACA_TRADING_MODE") or "").strip().lower()
    base = (env.get("ALPACA_BASE_URL") or "").strip().lower()
    personal = _truthy(env.get("PERSONAL_LIVE_APPROVED")) or _truthy(env.get("STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED"))
    if mode == "live" and not personal:
        issues.append("ALPACA_TRADING_MODE=live requires PERSONAL_LIVE_APPROVED or STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED=true")
    if "api.alpaca.markets" in base and "paper" not in base and not personal:
        issues.append("Alpaca live API base URL detected without personal live approval env")
    return issues


def build_report(*, env_file: Path | None) -> dict[str, Any]:
    env = _merged_env(env_file=env_file)
    providers_out: list[dict[str, Any]] = []
    for cap in sorted(all_provider_capabilities(), key=lambda p: p.provider_id):
        name, raw = _first_configured_key(env, cap.env_vars)
        configured = name is not None
        entry: dict[str, Any] = {
            "provider_id": cap.provider_id,
            "access_type": cap.access_type.value,
            "configured": configured,
            "requires_secret": cap.requires_secret,
            "env_vars_declared": list(cap.env_vars),
            "matched_env_var": name,
        }
        if configured and raw is not None:
            entry["secret_sha256_prefix"] = _sha16(raw)
        if cap.access_type != ProviderAccessType.PUBLIC_NO_SIGNUP and not configured and cap.requires_secret:
            entry["status"] = "PENDING_HUMAN_SIGNUP_OR_KEY"
        elif configured:
            entry["status"] = "CONFIGURED"
        else:
            entry["status"] = "NOT_CONFIGURED"
        providers_out.append(entry)

    alpaca = capability_by_provider_id().get("alpaca")
    return {
        "schema_version": "check_provider_keys/v1",
        "env_file": str(env_file) if env_file else None,
        "alpaca_paper_defaults_recommended": {
            "ALPACA_TRADING_MODE": "paper",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "PERSONAL_LIVE_APPROVED": "false",
        },
        "alpaca_live_policy_violations": _alpaca_live_violations(env),
        "providers": providers_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optional provider key presence check (redacted).")
    parser.add_argument("--env-file", default="", help="Merge KEY=VALUE pairs from this file into the report.")
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON.")
    ns = parser.parse_args(argv)
    try:
        env_path = safe_input_file(ns.env_file, label="CHECK_PROVIDER_KEYS_ENV_FILE", required=False) if ns.env_file else None
    except PathIntegrityError as exc:
        sys.stdout.write(json.dumps(path_error_payload(exc), sort_keys=True) + "\n")
        return 2
    report = build_report(env_file=env_path)
    indent = 2 if ns.json else None
    sys.stdout.write(json.dumps(report, indent=indent, sort_keys=True) + "\n")
    return 1 if report["alpaca_live_policy_violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
