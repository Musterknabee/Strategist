#!/usr/bin/env python3
"""Build governed provider evidence manifest linking samples, optional normalized rows, and health."""
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

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_file, safe_output_file

from strategy_validator.application.paper_research_replay import latest_replay_verification_summary
from strategy_validator.contracts.evidence_manifest import ProviderEvidenceManifest
from strategy_validator.evidence.provider_bundle import build_provider_evidence_manifest_payload
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
    parser = argparse.ArgumentParser(description="Assemble provider_evidence_manifest JSON for deployment bundles.")
    parser.add_argument(
        "--samples",
        type=Path,
        required=True,
        help="Provider samples manifest from retrieve_provider_samples.py",
    )
    parser.add_argument(
        "--normalized",
        type=Path,
        default=None,
        help="Optional normalized observations JSON from normalize_provider_samples.py",
    )
    parser.add_argument("--output", type=Path, required=True, help="Evidence manifest output path.")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional env file merged into health snapshot (same as other provider scripts).",
    )
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON.")
    ns = parser.parse_args(argv)
    try:
        samples = safe_input_file(ns.samples, label="PROVIDER_EVIDENCE_SAMPLES_MANIFEST", required=True)
        env_path = safe_input_file(ns.env_file, label="PROVIDER_EVIDENCE_ENV_FILE", required=False) if ns.env_file else None
        output = safe_output_file(ns.output, label="PROVIDER_EVIDENCE_OUTPUT")
        norm_path = safe_input_file(ns.normalized, label="PROVIDER_EVIDENCE_NORMALIZED", required=False) if ns.normalized else None
    except PathIntegrityError as exc:
        sys.stdout.write(json.dumps(path_error_payload(exc), sort_keys=True) + "\n")
        return 2
    env = _merged_env(env_file=env_path if env_path and env_path.is_file() else None)
    health = build_provider_health_snapshot(
        env=env,
        samples_manifest_path=samples,
        repo_root=_REPO_ROOT,
    )
    model = build_provider_evidence_manifest_payload(
        samples_manifest_path=samples,
        normalized_records_path=norm_path,
        health_snapshot=health,
        command_args_redacted=tuple(
            "<redacted>" if any(t in str(arg).lower() for t in ("key", "secret", "token", "password")) else str(arg)
            for arg in (argv or [])
        ),
        replay_manifest_path=(_REPO_ROOT / "artifacts" / "provider_paper_loop" / "latest" / "replay_manifest.json").as_posix(),
    )
    replay = latest_replay_verification_summary(repo_root=_REPO_ROOT)
    replay_status = str(replay.get("status") or "UNKNOWN").upper()
    replay_missing = int(replay.get("missing_artifact_count") or 0)
    replay_mismatch = int(replay.get("digest_mismatch_count") or 0)
    unavailable = list(model.unavailable_providers or ())
    blockers: list[str] = []
    warnings: list[str] = []
    if replay_mismatch > 0:
        blockers.append("REPLAY_DIGEST_MISMATCH")
    elif replay_status == "DEGRADED":
        blockers.append("REPLAY_EVIDENCE_DEGRADED")
    elif replay_status != "OK" or replay_missing > 0:
        warnings.append("REPLAY_EVIDENCE_MISSING_OR_PENDING")
    if unavailable:
        warnings.append("PROVIDER_UNAVAILABLE_PRESENT")
    evidence_status = "OK"
    if blockers:
        evidence_status = "DEGRADED"
    elif warnings:
        evidence_status = "UNKNOWN"
    payload: dict[str, Any] = model.model_dump(mode="json")
    payload["replay_verification_status"] = "DEGRADED" if blockers else ("OK" if replay_status == "OK" else "UNKNOWN")
    payload["evidence_status"] = evidence_status
    payload["warnings"] = tuple(dict.fromkeys(warnings))
    payload["blockers"] = tuple(dict.fromkeys(blockers))
    payload["trust_summary"] = {
        **(payload.get("trust_summary") or {}),
        "replay_verification_status": payload["replay_verification_status"],
        "evidence_status": payload["evidence_status"],
    }
    payload = ProviderEvidenceManifest.model_validate(payload).model_dump(mode="json")
    indent = 2 if ns.json else None
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=indent, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "schema_version": "build_provider_evidence_manifest_cli/v1",
        "wrote": output.as_posix(),
        "provider_sample_manifest_digest": payload.get("provider_sample_manifest_digest"),
        "provider_health_digest": payload.get("provider_health_digest"),
        "unavailable_providers": list(payload.get("unavailable_providers") or ()),
        "replay_verification_status": payload.get("replay_verification_status"),
        "evidence_status": payload.get("evidence_status"),
        "warnings": list(payload.get("warnings") or ()),
        "blockers": list(payload.get("blockers") or ()),
    }
    sys.stdout.write(json.dumps(summary, indent=2 if ns.json else None, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
