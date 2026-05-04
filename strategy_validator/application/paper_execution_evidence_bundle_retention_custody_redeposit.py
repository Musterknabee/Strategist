"""Read-only redeposit record for verified retrieved paper evidence retention custody."""
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
    PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyRedepositView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
    *, retention_custody_return_verification_artifact_path: Path | None = None, output_root: Path | None = None
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_return_verification_artifact_path is not None:
        path = retention_custody_return_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_return_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_return_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_redeposit_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    return_id = str(raw.get("custody_return_id") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_custody_return_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256({"tracking_id": tracking_id, "custody_return_id": return_id, "source_custody_return_verification_sha256": source_sha})
    return f"retention-custody-redeposit:{tracking_id}:{digest[:16]}"


def _custody_redeposit_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    return canonical_json_sha256(
        {
            "schema_version": "paper_execution_evidence_bundle_retention_custody_redeposit_statement/v1",
            "custody_redeposit_id": str(raw.get("custody_redeposit_id") or "").strip() or None,
            "redeposited_by": str(raw.get("redeposited_by") or "operator").strip() or "operator",
            "redeposit_reason": str(raw.get("redeposit_reason") or "return verified").strip() or "return verified",
            "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
            "redeposited_at_utc": str(raw.get("redeposited_at_utc") or "").strip() or None,
            "redeposit_status": str(raw.get("redeposit_status") or "UNKNOWN"),
            "redeposit_note": str(raw.get("redeposit_note") or "").strip() or None,
            "source_retention_custody_return_verification_declared_sha256": str(raw.get("source_retention_custody_return_verification_declared_sha256") or "").strip() or None,
            "source_retention_custody_return_verification_computed_sha256": str(raw.get("source_retention_custody_return_verification_computed_sha256") or "").strip() or None,
            "source_retention_custody_return_verification_status": str(raw.get("source_retention_custody_return_verification_status") or "UNKNOWN"),
            "source_retention_custody_return_status": str(raw.get("source_retention_custody_return_status") or "UNKNOWN"),
            "custody_return_id": str(raw.get("custody_return_id") or "").strip() or None,
            "custody_archive_id": str(raw.get("custody_archive_id") or "").strip() or None,
            "custody_closeout_id": str(raw.get("custody_closeout_id") or "").strip() or None,
            "custody_completion_id": str(raw.get("custody_completion_id") or "").strip() or None,
            "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
            "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
            "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
            "checklist": _strings(raw.get("checklist")),
        }
    )


def build_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
    *,
    retention_custody_return_verification_artifact_path: Path,
    retention_custody_return_verification_raw: dict[str, Any],
    redeposited_by: str = "operator",
    redeposit_reason: str = "return verified",
    custody_location: str = "local-retention",
    redeposit_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    declared = str(retention_custody_return_verification_raw.get("artifact_sha256") or "").strip() or None
    computed = _embedded_digest(retention_custody_return_verification_raw)
    source_hash_valid = _declared_matches_computed(declared, computed)
    if not retention_custody_return_verification_raw:
        blockers.append("RETENTION_CUSTODY_RETURN_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_RETURN_VERIFICATION_ARTIFACT_SHA256_MISMATCH")
    source_status = str(retention_custody_return_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_custody_return_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_RETURN_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_RETURN_VERIFICATION_TRUST_NOT_TRUSTED")
    return_status = str(retention_custody_return_verification_raw.get("source_retention_custody_return_status") or "UNKNOWN")
    if return_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_RETURN_STATUS_BLOCKED")
    elif return_status not in {"RETURNED", "RETURNED_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_RETURN_STATUS_NOT_RECOGNIZED")
    elif return_status == "RETURNED_RESTRICTED":
        warnings.append("RETENTION_CUSTODY_RETURN_RESTRICTED")
    for field, code in [
        ("retention_custody_return_artifact_hash_valid", "RETENTION_CUSTODY_RETURN_ARTIFACT_HASH_NOT_VALID"),
        ("custody_return_statement_hash_valid", "RETENTION_CUSTODY_RETURN_STATEMENT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_custody_return_verification_raw.get(field)):
            blockers.append(code)
    entry_count = _int(retention_custody_return_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_return_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_return_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_return_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_REDEPOSIT_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_REDEPOSIT_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_REDEPOSIT_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_REDEPOSIT_HAS_DIGEST_MISMATCHES")
    for item in _strings(retention_custody_return_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_RETURN_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_custody_return_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_RETURN_VERIFICATION_WARNING:{item}")
    operator = str(redeposited_by or "operator").strip() or "operator"
    reason = str(redeposit_reason or "return verified").strip() or "return verified"
    location = str(custody_location or retention_custody_return_verification_raw.get("custody_location") or "local-retention").strip() or "local-retention"
    note = str(redeposit_note or "").strip() or None
    redeposit_id = _custody_redeposit_id(retention_custody_return_verification_raw)
    checklist = [
        "retention custody return verification artifact hash valid",
        "retention custody return verification status PASS",
        "custody return artifact hash valid",
        "custody return statement hash valid",
        "all returned retention entries still digest-matched",
        "operator redeposited the returned retention custody evidence into declared custody location",
    ]
    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("REDEPOSITED_RESTRICTED" if warnings else "REDEPOSITED")
    trust = "TRUSTED" if status == "REDEPOSITED" else ("TRUST_RESTRICTED" if status == "REDEPOSITED_RESTRICTED" else "UNTRUSTED")
    statement_source = {
        "custody_redeposit_id": redeposit_id,
        "redeposited_by": operator,
        "redeposit_reason": reason,
        "custody_location": location,
        "redeposited_at_utc": now.isoformat(),
        "redeposit_status": status,
        "redeposit_note": note,
        "source_retention_custody_return_verification_declared_sha256": declared,
        "source_retention_custody_return_verification_computed_sha256": computed,
        "source_retention_custody_return_verification_status": source_status,
        "source_retention_custody_return_status": return_status,
        "custody_return_id": str(retention_custody_return_verification_raw.get("custody_return_id") or "").strip() or None,
        "custody_archive_id": str(retention_custody_return_verification_raw.get("custody_archive_id") or "").strip() or None,
        "custody_closeout_id": str(retention_custody_return_verification_raw.get("custody_closeout_id") or "").strip() or None,
        "custody_completion_id": str(retention_custody_return_verification_raw.get("custody_completion_id") or "").strip() or None,
        "source_retention_index_sha256": str(retention_custody_return_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    artifact = PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_return_verification_raw.get("tracking_id") or "").strip() or None,
        redeposit_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        custody_redeposit_id=redeposit_id,
        redeposited_by=operator,
        redeposit_reason=reason,
        custody_location=location,
        redeposited_at_utc=now.isoformat(),
        redeposit_note=note,
        source_retention_custody_return_verification_artifact_path=str(retention_custody_return_verification_artifact_path),
        source_retention_custody_return_verification_declared_sha256=declared,
        source_retention_custody_return_verification_computed_sha256=computed,
        source_retention_custody_return_verification_status=source_status,
        source_retention_custody_return_verification_trust_banner=source_trust,
        retention_custody_return_verification_artifact_hash_valid=source_hash_valid,
        source_retention_custody_return_status=return_status,
        retention_custody_return_artifact_hash_valid=bool(retention_custody_return_verification_raw.get("retention_custody_return_artifact_hash_valid")),
        custody_return_id=str(retention_custody_return_verification_raw.get("custody_return_id") or "").strip() or None,
        custody_return_statement_hash_valid=bool(retention_custody_return_verification_raw.get("custody_return_statement_hash_valid")),
        custody_archive_id=str(retention_custody_return_verification_raw.get("custody_archive_id") or "").strip() or None,
        custody_closeout_id=str(retention_custody_return_verification_raw.get("custody_closeout_id") or "").strip() or None,
        custody_completion_id=str(retention_custody_return_verification_raw.get("custody_completion_id") or "").strip() or None,
        next_renewal_due_at_utc=str(retention_custody_return_verification_raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(retention_custody_return_verification_raw.get("days_until_due")),
        source_retention_index_sha256=str(retention_custody_return_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        custody_redeposit_statement_sha256=_custody_redeposit_statement_digest(statement_source),
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
    *,
    retention_custody_return_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    redeposited_by: str = "operator",
    redeposit_reason: str = "return verified",
    custody_location: str = "local-retention",
    redeposit_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
        retention_custody_return_verification_artifact_path=retention_custody_return_verification_artifact_path, output_root=output_root
    )
    if source_path is None or raw is None:
        source_path = (retention_custody_return_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_return_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
        retention_custody_return_verification_artifact_path=source_path,
        retention_custody_return_verification_raw=raw,
        redeposited_by=redeposited_by,
        redeposit_reason=redeposit_reason,
        custody_location=custody_location,
        redeposit_note=redeposit_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_redeposits"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_redeposit.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyRedepositView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyRedepositView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        redeposit_status=str(raw.get("redeposit_status") or "UNKNOWN"),
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),
        custody_redeposit_id=str(raw.get("custody_redeposit_id") or "").strip() or None,
        redeposited_by=str(raw.get("redeposited_by") or "").strip() or None,
        redeposit_reason=str(raw.get("redeposit_reason") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        redeposited_at_utc=str(raw.get("redeposited_at_utc") or "").strip() or None,
        redeposit_note=str(raw.get("redeposit_note") or "").strip() or None,
        source_retention_custody_return_verification_artifact_path=str(raw.get("source_retention_custody_return_verification_artifact_path") or "").strip() or None,
        source_retention_custody_return_verification_status=str(raw.get("source_retention_custody_return_verification_status") or "").strip() or None,
        retention_custody_return_verification_artifact_hash_valid=bool(raw.get("retention_custody_return_verification_artifact_hash_valid")),
        source_retention_custody_return_status=str(raw.get("source_retention_custody_return_status") or "").strip() or None,
        retention_custody_return_artifact_hash_valid=bool(raw.get("retention_custody_return_artifact_hash_valid")),
        custody_return_id=str(raw.get("custody_return_id") or "").strip() or None,
        custody_return_statement_hash_valid=bool(raw.get("custody_return_statement_hash_valid")),
        custody_archive_id=str(raw.get("custody_archive_id") or "").strip() or None,
        custody_closeout_id=str(raw.get("custody_closeout_id") or "").strip() or None,
        custody_completion_id=str(raw.get("custody_completion_id") or "").strip() or None,
        next_renewal_due_at_utc=str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(raw.get("days_until_due")),
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        custody_redeposit_statement_sha256=str(raw.get("custody_redeposit_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_custody_redeposit_views(*, repo_root: Path | None = None, output_root: Path | None = None) -> list[PaperExecutionEvidenceBundleRetentionCustodyRedepositView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_redeposits/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_redeposit.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = [
    "build_paper_execution_evidence_bundle_retention_custody_redeposit_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_return_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_redeposit_views",
    "write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact",
]
