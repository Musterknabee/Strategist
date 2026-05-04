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


def _absolute_path_preserving_symlink(path: str | Path) -> Path:
    """Return an absolute path without resolving symlink components."""

    target = Path(path)
    if target.is_absolute():
        return target
    return Path.cwd() / target


def _symlink_components_preserving_path(path: str | Path) -> list[Path]:
    """Return existing symlink components without following them."""

    target = _absolute_path_preserving_symlink(path)
    parts = target.parts
    if not parts:
        return []
    current = Path(parts[0])
    out: list[Path] = []
    for part in parts[1:]:
        current = current / part
        if current.is_symlink():
            out.append(current)
    return out


def _path_error_payload(*, code: str, path: str | Path, detail: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "operator_deployment_signoff_path_error/v1",
        "ok": False,
        "code": code,
        "path": str(_absolute_path_preserving_symlink(path)),
    }
    if detail:
        payload["detail"] = detail
    return payload


def _symlink_error(path: str | Path, *, label: str) -> dict[str, object] | None:
    target = _absolute_path_preserving_symlink(path)
    symlinks = _symlink_components_preserving_path(target)
    if not symlinks:
        return None
    final_component = target in symlinks
    code = f"{label}_IS_SYMLINK" if final_component else f"{label}_PARENT_IS_SYMLINK"
    return _path_error_payload(
        code=code,
        path=target,
        detail=", ".join(str(item) for item in symlinks),
    )


def _validate_input_file(path: str | Path, *, label: str) -> tuple[Path | None, dict[str, object] | None]:
    target = _absolute_path_preserving_symlink(path)
    issue = _symlink_error(target, label=label)
    if issue is not None:
        return None, issue
    if not target.is_file():
        return None, _path_error_payload(code=f"{label}_NOT_FILE", path=target)
    return target, None


def _validate_output_file(path: str | Path, *, label: str) -> tuple[Path | None, dict[str, object] | None]:
    target = _absolute_path_preserving_symlink(path)
    issue = _symlink_error(target, label=label)
    if issue is not None:
        return None, issue
    if target.exists() and not target.is_file():
        return None, _path_error_payload(code=f"{label}_NOT_FILE", path=target)
    return target, None


def _validate_input_directory(path: str | Path, *, label: str) -> tuple[Path | None, dict[str, object] | None]:
    target = _absolute_path_preserving_symlink(path)
    issue = _symlink_error(target, label=label)
    if issue is not None:
        return None, issue
    if not target.is_dir():
        return None, _path_error_payload(code=f"{label}_NOT_DIRECTORY", path=target)
    return target, None


def _emit_path_error(payload: dict[str, object]) -> int:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 2


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
    repo, repo_error = _validate_input_directory(ns.repo_root, label="SIGNOFF_REPO_ROOT")
    if repo_error is not None:
        return _emit_path_error(repo_error)
    assert repo is not None

    output_path, output_error = _validate_output_file(ns.output, label="SIGNOFF_OUTPUT")
    if output_error is not None:
        return _emit_path_error(output_error)
    assert output_path is not None

    if ns.evidence_dir is not None:
        evidence_dir, evidence_dir_error = _validate_input_directory(ns.evidence_dir, label="SIGNOFF_EVIDENCE_DIR")
        if evidence_dir_error is not None:
            return _emit_path_error(evidence_dir_error)
        assert evidence_dir is not None
        candidate_manifest = evidence_dir / "deployment-evidence.json"
    else:
        candidate_manifest = ns.evidence_manifest

    manifest_path, manifest_error = _validate_input_file(candidate_manifest, label="SIGNOFF_EVIDENCE_MANIFEST")
    if manifest_error is not None:
        return _emit_path_error(manifest_error)
    assert manifest_path is not None
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
    if provider_ev.exists() or provider_ev.is_symlink():
        provider_path, provider_error = _validate_input_file(provider_ev, label="SIGNOFF_PROVIDER_EVIDENCE_MANIFEST")
        if provider_error is not None:
            return _emit_path_error(provider_error)
        assert provider_path is not None
        provider_digest = hashlib.sha256(provider_path.read_bytes()).hexdigest()

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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps({"wrote": str(output_path), "schema_version": payload["schema_version"]}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
