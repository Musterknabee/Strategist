#!/usr/bin/env python3
"""Emit a secret-free operator sign-off record referencing deployment evidence digests."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PENDING_MANUAL_SIGNOFF = "<PENDING_HUMAN_SIGNOFF>"
_GENERIC_HUMAN_CONFIRM_WARNING = (
    "Human must confirm APPROVED_FOR_SINGLE_TENANT_BACKEND after reviewing artifacts/deployment/release-evidence/."
)
_EVIDENCE_PACK_FAILED_WARNING = "Evidence pack reported ok=false"


def _named_manual_signoff(manual_signoff: str) -> bool:
    manual = (manual_signoff or "").strip()
    return bool(manual) and manual != PENDING_MANUAL_SIGNOFF


def compute_known_warnings(
    *,
    operator_decision: str,
    manual_signoff: str,
    evidence_pack_ok: bool,
) -> list[str]:
    """Warnings for operator_signoff.json (secret-free)."""
    named = _named_manual_signoff(manual_signoff)
    omit_generic_human_confirm = (
        named
        and operator_decision == "APPROVED_FOR_SINGLE_TENANT_BACKEND"
        and evidence_pack_ok
    )
    out: list[str] = []
    if not evidence_pack_ok:
        out.append(_EVIDENCE_PACK_FAILED_WARNING)
    elif not omit_generic_human_confirm:
        out.append(_GENERIC_HUMAN_CONFIRM_WARNING)
    return out


def _git_head(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    meg = parser.add_mutually_exclusive_group(required=True)
    meg.add_argument(
        "--evidence-manifest",
        type=Path,
        default=None,
        help="Path to deployment-evidence.json from single_tenant_deployment_evidence",
    )
    meg.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Directory containing deployment-evidence.json (same as --evidence-manifest <dir>/deployment-evidence.json).",
    )
    parser.add_argument("--output", type=Path, required=True, help="Write operator_signoff.json here.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--deployment-id", default="", help="Optional operator-supplied deployment id.")
    parser.add_argument(
        "--decision",
        default="APPROVED_WITH_WARNINGS",
        choices=("APPROVED_FOR_SINGLE_TENANT_BACKEND", "APPROVED_WITH_WARNINGS", "BLOCKED"),
        help="Operator decision (default: APPROVED_WITH_WARNINGS until human confirms).",
    )
    parser.add_argument(
        "--manual-signoff",
        default="",
        help="Required human sign-off string (name/id); leave empty to record pending human sign-off.",
    )
    ns = parser.parse_args(argv)
    repo = ns.repo_root.resolve()
    if ns.evidence_dir is not None:
        manifest_path = (ns.evidence_dir / "deployment-evidence.json").resolve()
    else:
        manifest_path = ns.evidence_manifest.resolve()
    manifest_bytes = manifest_path.read_bytes()
    evidence_manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    raw = json.loads(manifest_bytes.decode("utf-8"))
    files = raw.get("files") if isinstance(raw.get("files"), list) else []
    digests = {
        str(item.get("name")): item.get("sha256")
        for item in files
        if isinstance(item, dict) and item.get("name") and item.get("sha256")
    }
    when = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    provider_ev = manifest_path.parent / "provider-evidence-manifest.json"
    provider_digest = None
    if provider_ev.is_file():
        provider_digest = hashlib.sha256(provider_ev.read_bytes()).hexdigest()

    evidence_ok = bool(raw.get("ok"))
    named = _named_manual_signoff(ns.manual_signoff)
    fully_approved_backend = named and ns.decision == "APPROVED_FOR_SINGLE_TENANT_BACKEND" and evidence_ok
    known_warnings = compute_known_warnings(
        operator_decision=ns.decision,
        manual_signoff=ns.manual_signoff,
        evidence_pack_ok=evidence_ok,
    )
    if fully_approved_backend:
        recommended_action = (
            "Retain artifacts/deployment/release-evidence/; re-run deployment gates after material host or configuration changes."
        )
    else:
        recommended_action = (
            "Record manual_operator_signoff and set operator_decision to APPROVED_FOR_SINGLE_TENANT_BACKEND when satisfied."
        )

    payload = {
        "schema_version": "operator_deployment_signoff/v1",
        "deployment_id": ns.deployment_id or f"local-{when[:10]}",
        "generated_at_utc": when,
        "git_commit": _git_head(repo),
        "host_os": sys.platform,
        "mode": "PRODUCTION",
        "api_bind": "127.0.0.1:8000 (local dev script; use reverse proxy in real deploy)",
        "ledger_path_class": "resolved_from_deployment_env",
        "artifact_root_class": "resolved_from_deployment_env",
        "backup_root_class": "resolved_from_deployment_env",
        "evidence_manifest_path": str(manifest_path),
        "deployment_evidence_manifest_sha256": evidence_manifest_sha256,
        "digest_by_report": digests,
        "provider_evidence_manifest_sha256": provider_digest,
        "frontend_readiness_status": "NOT_CLAIMED",
        "evidence_pack_ok": evidence_ok,
        "known_warnings": known_warnings,
        "operator_decision": ns.decision,
        "manual_operator_signoff": ns.manual_signoff or PENDING_MANUAL_SIGNOFF,
        "recommended_action": recommended_action,
    }
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps({"wrote": str(ns.output.resolve()), "schema_version": payload["schema_version"]}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
