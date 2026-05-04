"""Read-only closeout record for verified paper evidence retention custody renewal completions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import (
    _declared_matches_computed,
    _embedded_digest,
    _int,
    _mtime,
    _safe_read_json,
    _strings,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyCloseoutView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact(
    *,
    retention_custody_completion_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_completion_verification_artifact_path is not None:
        path = retention_custody_completion_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_completion_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_completion_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_closeout_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    completion_id = str(raw.get("custody_completion_id") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_custody_completion_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256(
        {
            "tracking_id": tracking_id,
            "custody_completion_id": completion_id,
            "source_custody_completion_verification_sha256": source_sha,
        }
    )
    return f"retention-custody-closeout:{tracking_id}:{digest[:16]}"


def _custody_closeout_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    return canonical_json_sha256(
        {
            "schema_version": "paper_execution_evidence_bundle_retention_custody_closeout_statement/v1",
            "custody_closeout_id": str(raw.get("custody_closeout_id") or "").strip() or None,
            "closed_out_by": str(raw.get("closed_out_by") or "operator").strip() or "operator",
            "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
            "closed_out_at_utc": str(raw.get("closed_out_at_utc") or "").strip() or None,
            "closeout_status": str(raw.get("closeout_status") or "UNKNOWN"),
            "closeout_note": str(raw.get("closeout_note") or "").strip() or None,
            "source_retention_custody_completion_verification_declared_sha256": str(raw.get("source_retention_custody_completion_verification_declared_sha256") or "").strip() or None,
            "source_retention_custody_completion_verification_computed_sha256": str(raw.get("source_retention_custody_completion_verification_computed_sha256") or "").strip() or None,
            "source_retention_custody_completion_verification_status": str(raw.get("source_retention_custody_completion_verification_status") or "UNKNOWN"),
            "source_retention_custody_completion_verification_trust_banner": str(raw.get("source_retention_custody_completion_verification_trust_banner") or "TRUST_RESTRICTED"),
            "source_retention_custody_completion_status": str(raw.get("source_retention_custody_completion_status") or "UNKNOWN"),
            "custody_completion_id": str(raw.get("custody_completion_id") or "").strip() or None,
            "completed_by": str(raw.get("completed_by") or "").strip() or None,
            "completed_at_utc": str(raw.get("completed_at_utc") or "").strip() or None,
            "next_renewal_due_at_utc": str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
            "days_until_due": _int(raw.get("days_until_due")),
            "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
            "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
            "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
            "checklist": _strings(raw.get("checklist")),
        }
    )


def build_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
    *,
    retention_custody_completion_verification_artifact_path: Path,
    retention_custody_completion_verification_raw: dict[str, Any],
    closed_out_by: str = "operator",
    custody_location: str = "local-retention",
    closeout_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared = str(retention_custody_completion_verification_raw.get("artifact_sha256") or "").strip() or None
    computed = _embedded_digest(retention_custody_completion_verification_raw)
    source_hash_valid = _declared_matches_computed(declared, computed)
    if not retention_custody_completion_verification_raw:
        blockers.append("RETENTION_CUSTODY_COMPLETION_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_COMPLETION_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str(retention_custody_completion_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_custody_completion_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_COMPLETION_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_COMPLETION_VERIFICATION_TRUST_NOT_TRUSTED")

    completion_status = str(retention_custody_completion_verification_raw.get("source_retention_custody_completion_status") or "UNKNOWN")
    if completion_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_COMPLETION_STATUS_BLOCKED")
    elif completion_status not in {"COMPLETED", "COMPLETED_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_COMPLETION_STATUS_NOT_RECOGNIZED")

    for field, code in [
        ("retention_custody_completion_artifact_hash_valid", "RETENTION_CUSTODY_COMPLETION_ARTIFACT_HASH_NOT_VALID"),
        ("custody_completion_statement_hash_valid", "RETENTION_CUSTODY_COMPLETION_STATEMENT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_custody_completion_verification_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_custody_completion_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_completion_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_completion_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_completion_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_CLOSEOUT_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_CLOSEOUT_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_CLOSEOUT_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_CLOSEOUT_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_custody_completion_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_COMPLETION_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_custody_completion_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_COMPLETION_VERIFICATION_WARNING:{item}")

    operator = str(closed_out_by or "operator").strip() or "operator"
    location = str(custody_location or retention_custody_completion_verification_raw.get("custody_location") or "local-retention").strip() or "local-retention"
    note = str(closeout_note or "").strip() or None
    closeout_id = _custody_closeout_id(retention_custody_completion_verification_raw)
    checklist = [
        "retention custody completion verification artifact hash valid",
        "retention custody completion verification status PASS",
        "custody completion artifact hash valid",
        "custody completion statement hash valid",
        "all retention entries present and digest-matched",
        "operator closed out the retention custody renewal cycle",
    ]
    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("CLOSED_RESTRICTED" if warnings else "CLOSED")
    trust = "TRUSTED" if status == "CLOSED" else ("TRUST_RESTRICTED" if status == "CLOSED_RESTRICTED" else "UNTRUSTED")

    statement_source = {
        "custody_closeout_id": closeout_id,
        "closed_out_by": operator,
        "custody_location": location,
        "closed_out_at_utc": now.isoformat(),
        "closeout_status": status,
        "closeout_note": note,
        "source_retention_custody_completion_verification_declared_sha256": declared,
        "source_retention_custody_completion_verification_computed_sha256": computed,
        "source_retention_custody_completion_verification_status": source_status,
        "source_retention_custody_completion_verification_trust_banner": source_trust,
        "source_retention_custody_completion_status": completion_status,
        "custody_completion_id": str(retention_custody_completion_verification_raw.get("custody_completion_id") or "").strip() or None,
        "completed_by": str(retention_custody_completion_verification_raw.get("completed_by") or "").strip() or None,
        "completed_at_utc": str(retention_custody_completion_verification_raw.get("completed_at_utc") or "").strip() or None,
        "next_renewal_due_at_utc": str(retention_custody_completion_verification_raw.get("next_renewal_due_at_utc") or "").strip() or None,
        "days_until_due": _int(retention_custody_completion_verification_raw.get("days_until_due")),
        "source_retention_index_sha256": str(retention_custody_completion_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    statement_sha = _custody_closeout_statement_digest(statement_source)
    artifact = PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_completion_verification_raw.get("tracking_id") or "").strip() or None,
        closeout_status=status,
        trust_banner=trust,
        custody_closeout_id=closeout_id,
        closed_out_by=operator,
        custody_location=location,
        closed_out_at_utc=now.isoformat(),
        closeout_note=note,
        source_retention_custody_completion_verification_artifact_path=str(retention_custody_completion_verification_artifact_path),
        source_retention_custody_completion_verification_declared_sha256=declared,
        source_retention_custody_completion_verification_computed_sha256=computed,
        source_retention_custody_completion_verification_status=source_status,
        source_retention_custody_completion_verification_trust_banner=source_trust,
        retention_custody_completion_verification_artifact_hash_valid=source_hash_valid,
        source_retention_custody_completion_status=completion_status,
        retention_custody_completion_artifact_hash_valid=bool(retention_custody_completion_verification_raw.get("retention_custody_completion_artifact_hash_valid")),
        custody_completion_id=str(retention_custody_completion_verification_raw.get("custody_completion_id") or "").strip() or None,
        custody_completion_statement_hash_valid=bool(retention_custody_completion_verification_raw.get("custody_completion_statement_hash_valid")),
        completed_by=str(retention_custody_completion_verification_raw.get("completed_by") or "").strip() or None,
        completed_at_utc=str(retention_custody_completion_verification_raw.get("completed_at_utc") or "").strip() or None,
        next_renewal_due_at_utc=str(retention_custody_completion_verification_raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(retention_custody_completion_verification_raw.get("days_until_due")),
        source_retention_index_sha256=str(retention_custody_completion_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        custody_closeout_statement_sha256=statement_sha,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
    *,
    retention_custody_completion_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    closed_out_by: str = "operator",
    custody_location: str = "local-retention",
    closeout_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact(
        retention_custody_completion_verification_artifact_path=retention_custody_completion_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (
            retention_custody_completion_verification_artifact_path
            or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_completion_verification.json")
        ).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
        retention_custody_completion_verification_artifact_path=source_path,
        retention_custody_completion_verification_raw=raw,
        closed_out_by=closed_out_by,
        custody_location=custody_location,
        closeout_note=closeout_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_closeouts"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_closeout.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyCloseoutView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyCloseoutView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        closeout_status=str(raw.get("closeout_status") or "UNKNOWN"),
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),
        custody_closeout_id=str(raw.get("custody_closeout_id") or "").strip() or None,
        closed_out_by=str(raw.get("closed_out_by") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        closed_out_at_utc=str(raw.get("closed_out_at_utc") or "").strip() or None,
        closeout_note=str(raw.get("closeout_note") or "").strip() or None,
        source_retention_custody_completion_verification_artifact_path=str(raw.get("source_retention_custody_completion_verification_artifact_path") or "").strip() or None,
        source_retention_custody_completion_verification_status=str(raw.get("source_retention_custody_completion_verification_status") or "").strip() or None,
        retention_custody_completion_verification_artifact_hash_valid=bool(raw.get("retention_custody_completion_verification_artifact_hash_valid")),
        source_retention_custody_completion_status=str(raw.get("source_retention_custody_completion_status") or "").strip() or None,
        retention_custody_completion_artifact_hash_valid=bool(raw.get("retention_custody_completion_artifact_hash_valid")),
        custody_completion_id=str(raw.get("custody_completion_id") or "").strip() or None,
        custody_completion_statement_hash_valid=bool(raw.get("custody_completion_statement_hash_valid")),
        next_renewal_due_at_utc=str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(raw.get("days_until_due")),
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        custody_closeout_statement_sha256=str(raw.get("custody_closeout_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_custody_closeout_views(
    *, repo_root: Path | None = None, output_root: Path | None = None
) -> list[PaperExecutionEvidenceBundleRetentionCustodyCloseoutView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_closeouts/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_closeout.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = [
    "_custody_closeout_statement_digest",
    "build_paper_execution_evidence_bundle_retention_custody_closeout_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_closeout_views",
    "write_paper_execution_evidence_bundle_retention_custody_closeout_artifact",
]
