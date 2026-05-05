"""Read-only local evidence bundle index discovery."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import resolve_artifact_root

_SCHEMA_VERSION = "evidence_bundle_index/v1"
_DISCLOSURE_DISCLAIMERS = (
    "Evidence discovery only.",
    "Not production deployment approval.",
    "Not operator signoff.",
    "Not live trading authorization.",
    "Not profitability evidence.",
    "Artifact presence is not strategy quality.",
    "verified_integrity is true only when explicit verification evidence is discovered.",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head_sha(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return (proc.stdout or "").strip() or "UNKNOWN"


def _safe_relative(path: Path, *, artifact_root: Path) -> str:
    try:
        return path.resolve().relative_to(artifact_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _entry(
    *,
    kind: str,
    path: Path,
    artifact_root: Path,
    include_digests: bool,
    source_command: str,
    summary: str,
    status: str | None = None,
    verified_integrity: bool = False,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    exists = path.is_file()
    entry: dict[str, Any] = {
        "kind": kind,
        "path": _safe_relative(path, artifact_root=artifact_root),
        "exists": exists,
        "sha256": _sha256_file(path) if include_digests and exists else None,
        "generated_at_utc": None,
        "source_command": source_command,
        "status": status or ("OK" if exists else "PENDING"),
        "summary": summary if exists else f"{summary} not found.",
        "verified_integrity": bool(verified_integrity and exists),
        "notes": notes or [],
    }
    return entry


def build_evidence_bundle_index(
    *,
    repo_root: Path,
    artifact_root: Path | None = None,
    include_digests: bool = False,
) -> dict[str, Any]:
    root = repo_root.resolve()
    governed_root = (artifact_root or resolve_artifact_root(root)).resolve()
    release_root = governed_root / "release_verification" / "latest"
    provider_loop_root = governed_root / "provider_paper_loop" / "latest"

    release_json = release_root / "main-release-verification-pack.json"
    release_md = release_root / "main-release-verification-pack.md"
    branch_audit = release_root / "branch-cleanup-audit.json"
    replay_manifest = provider_loop_root / "replay_manifest.json"
    provider_manifest = provider_loop_root / "provider_evidence_manifest.json"
    operator_doctor_json = release_root / "operator-doctor.json"
    operator_doctor_md = release_root / "operator-doctor.md"
    repo_archive = release_root / "repo-handoff.zip"
    repo_archive_verify = release_root / "repo-handoff.verify.json"
    readiness_snapshot = release_root / "production-smoke-readiness.json"

    entries = [
        _entry(
            kind="release_verification_pack",
            path=release_json,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/main_release_verification_pack.py --output-dir artifacts/release_verification/latest --json",
            summary="Main release verification JSON evidence.",
        ),
        _entry(
            kind="release_verification_markdown",
            path=release_md,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/main_release_verification_pack.py --summary-markdown-output-path artifacts/release_verification/latest/main-release-verification-pack.md",
            summary="Main release verification Markdown summary.",
        ),
        _entry(
            kind="branch_cleanup_audit",
            path=branch_audit,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/branch_cleanup_audit.py --output-json-path artifacts/release_verification/latest/branch-cleanup-audit.json",
            summary="Branch cleanup audit JSON report.",
        ),
        _entry(
            kind="paper_replay_manifest",
            path=replay_manifest,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="strategy-validator-paper-research-replay-verify --replay-manifest artifacts/provider_paper_loop/latest/replay_manifest.json --json",
            summary="Paper replay manifest for offline digest verification.",
            notes=["Replay verification must run separately; discovery alone is not verification."],
        ),
        _entry(
            kind="provider_evidence_manifest",
            path=provider_manifest,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/build_provider_evidence_manifest.py --output-dir artifacts/provider_paper_loop/latest --json",
            summary="Provider evidence manifest linking samples and trust summary.",
        ),
        _entry(
            kind="operator_doctor_report",
            path=operator_doctor_json,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="strategy-validator-operator-doctor --json",
            summary="Operator doctor JSON diagnostic report.",
            notes=["Operator doctor remains diagnostic-only and read-only by default."],
        ),
        _entry(
            kind="operator_doctor_markdown",
            path=operator_doctor_md,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="strategy-validator-operator-doctor --summary-markdown-output-path artifacts/release_verification/latest/operator-doctor.md",
            summary="Operator doctor Markdown summary.",
        ),
        _entry(
            kind="repo_archive",
            path=repo_archive,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/package_repo.py --output artifacts/release_verification/latest/repo-handoff.zip --json",
            summary="Clean repository handoff archive.",
            notes=["Archive presence is not archive verification."],
        ),
        _entry(
            kind="repo_archive_verification",
            path=repo_archive_verify,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/verify_repo_archive.py artifacts/release_verification/latest/repo-handoff.zip --json > artifacts/release_verification/latest/repo-handoff.verify.json",
            summary="Repository archive verification JSON report.",
            verified_integrity=True,
        ),
        _entry(
            kind="readiness_snapshot",
            path=readiness_snapshot,
            artifact_root=governed_root,
            include_digests=include_digests,
            source_command="python scripts/production_smoke_check.py --json > artifacts/release_verification/latest/production-smoke-readiness.json",
            summary="Optional readiness diagnostic snapshot.",
        ),
    ]

    release_payload = _read_json_if_exists(release_json)
    if release_payload:
        for item in entries:
            if item["kind"] == "release_verification_pack":
                item["generated_at_utc"] = release_payload.get("generated_at_utc")
                item["status"] = str(release_payload.get("status") or item["status"]).upper()
                item["summary"] = "Main release verification pack discovered."
                break

    branch_payload = _read_json_if_exists(branch_audit)
    if branch_payload:
        for item in entries:
            if item["kind"] == "branch_cleanup_audit":
                item["generated_at_utc"] = branch_payload.get("generated_at_utc")
                item["status"] = "OK"
                item["summary"] = "Branch cleanup audit discovered."
                break

    replay_payload = _read_json_if_exists(replay_manifest)
    if replay_payload:
        for item in entries:
            if item["kind"] == "paper_replay_manifest":
                item["generated_at_utc"] = replay_payload.get("generated_at_utc")
                item["status"] = "OK"
                item["summary"] = "Replay manifest discovered."
                break

    provider_payload = _read_json_if_exists(provider_manifest)
    if provider_payload:
        for item in entries:
            if item["kind"] == "provider_evidence_manifest":
                item["generated_at_utc"] = provider_payload.get("generated_at_utc")
                item["status"] = str(provider_payload.get("evidence_status") or "OK").upper()
                item["summary"] = "Provider evidence manifest discovered."
                break

    verify_payload = _read_json_if_exists(repo_archive_verify)
    if verify_payload:
        for item in entries:
            if item["kind"] == "repo_archive_verification":
                item["generated_at_utc"] = verify_payload.get("generated_at")
                status = str(verify_payload.get("status") or "UNKNOWN").upper()
                item["status"] = "OK" if status == "PASS" else ("BLOCKED" if status == "FAIL" else status)
                item["verified_integrity"] = status == "PASS"
                item["summary"] = "Repository archive verification report discovered."
                break

    warnings = []
    if not any(entry["exists"] for entry in entries):
        warnings.append("NO_DISCOVERED_EVIDENCE_ARTIFACTS")

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "artifact_root": governed_root.as_posix(),
        "repo_head_sha": _git_head_sha(root),
        "entries": entries,
        "warnings": warnings,
        "blockers": [],
        "disclaimers": list(_DISCLOSURE_DISCLAIMERS),
    }
    return payload


__all__ = [
    "build_evidence_bundle_index",
]
