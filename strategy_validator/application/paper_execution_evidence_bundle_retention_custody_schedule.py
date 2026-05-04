"""Read-only schedule for the next verified paper evidence retention custody renewal."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import _declared_matches_computed, _embedded_digest, _int, _mtime, _safe_read_json, _strings
from strategy_validator.contracts.paper_execution import PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact, PaperExecutionEvidenceBundleRetentionCustodyScheduleView
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_latest_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact(*, retention_custody_renewal_verification_artifact_path: Path | None = None, output_root: Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_renewal_verification_artifact_path is not None:
        path = retention_custody_renewal_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_renewal_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_renewal_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_schedule_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    renewal_id = str(raw.get("custody_renewal_id") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_custody_renewal_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256({"tracking_id": tracking_id, "custody_renewal_id": renewal_id, "source_custody_renewal_verification_sha256": source_sha})
    return f"retention-custody-schedule:{tracking_id}:{digest[:16]}"


def _custody_schedule_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    return canonical_json_sha256({
        "schema_version": "paper_execution_evidence_bundle_retention_custody_schedule_statement/v1",
        "custody_schedule_id": str(raw.get("custody_schedule_id") or "").strip() or None,
        "scheduled_by": str(raw.get("scheduled_by") or "operator").strip() or "operator",
        "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
        "schedule_start_at_utc": str(raw.get("schedule_start_at_utc") or "").strip() or None,
        "next_renewal_due_at_utc": str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
        "renewal_interval_days": _int(raw.get("renewal_interval_days")),
        "reminder_days_before_due": _int(raw.get("reminder_days_before_due")),
        "schedule_note": str(raw.get("schedule_note") or "").strip() or None,
        "source_retention_custody_renewal_verification_declared_sha256": str(raw.get("source_retention_custody_renewal_verification_declared_sha256") or "").strip() or None,
        "source_retention_custody_renewal_verification_computed_sha256": str(raw.get("source_retention_custody_renewal_verification_computed_sha256") or "").strip() or None,
        "source_retention_custody_renewal_verification_status": str(raw.get("source_retention_custody_renewal_verification_status") or "UNKNOWN"),
        "source_retention_custody_renewal_verification_trust_banner": str(raw.get("source_retention_custody_renewal_verification_trust_banner") or "TRUST_RESTRICTED"),
        "custody_renewal_id": str(raw.get("custody_renewal_id") or "").strip() or None,
        "source_retention_custody_renewal_status": str(raw.get("source_retention_custody_renewal_status") or "UNKNOWN"),
        "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(raw.get("checklist")),
    })


def build_paper_execution_evidence_bundle_retention_custody_schedule_artifact(*, retention_custody_renewal_verification_artifact_path: Path, retention_custody_renewal_verification_raw: dict[str, Any], scheduled_by: str = "operator", custody_location: str = "local-retention", reminder_days_before_due: int = 7, schedule_note: str | None = None, generated_at_utc: datetime | None = None) -> PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    declared = str(retention_custody_renewal_verification_raw.get("artifact_sha256") or "").strip() or None
    computed = _embedded_digest(retention_custody_renewal_verification_raw)
    source_hash_valid = _declared_matches_computed(declared, computed)
    if not retention_custody_renewal_verification_raw:
        blockers.append("RETENTION_CUSTODY_RENEWAL_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_RENEWAL_VERIFICATION_ARTIFACT_SHA256_MISMATCH")
    source_status = str(retention_custody_renewal_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_custody_renewal_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_RENEWAL_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_RENEWAL_VERIFICATION_TRUST_NOT_TRUSTED")
    renewal_status = str(retention_custody_renewal_verification_raw.get("source_retention_custody_renewal_status") or "UNKNOWN")
    if renewal_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_RENEWAL_STATUS_BLOCKED")
    elif renewal_status not in {"RENEWED", "RENEWAL_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_RENEWAL_STATUS_NOT_RENEWED")
    for field, code in [("retention_custody_renewal_artifact_hash_valid", "RETENTION_CUSTODY_RENEWAL_ARTIFACT_HASH_NOT_VALID"), ("custody_renewal_statement_hash_valid", "RETENTION_CUSTODY_RENEWAL_STATEMENT_HASH_NOT_VALID")]:
        if not bool(retention_custody_renewal_verification_raw.get(field)):
            blockers.append(code)
    entry_count = _int(retention_custody_renewal_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_renewal_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_renewal_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_renewal_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_HAS_DIGEST_MISMATCHES")
    for item in _strings(retention_custody_renewal_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_RENEWAL_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_custody_renewal_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_RENEWAL_VERIFICATION_WARNING:{item}")
    operator = str(scheduled_by or "operator").strip() or "operator"
    location = str(custody_location or retention_custody_renewal_verification_raw.get("custody_location") or "local-retention").strip() or "local-retention"
    interval = max(1, _int(retention_custody_renewal_verification_raw.get("renewal_interval_days")) or 30)
    reminder = max(0, _int(reminder_days_before_due) or 7)
    note = str(schedule_note or "").strip() or None
    schedule_start = _parse_dt(retention_custody_renewal_verification_raw.get("generated_at_utc")) or now
    due = schedule_start + timedelta(days=interval)
    schedule_id = _custody_schedule_id(retention_custody_renewal_verification_raw)
    checklist = ["retention custody renewal verification artifact hash valid", "retention custody renewal verification status PASS", "custody renewal artifact hash valid", "custody renewal statement hash valid", "all retention entries present and digest-matched", "next renewal due date recorded"]
    statement_source = {"custody_schedule_id": schedule_id, "scheduled_by": operator, "custody_location": location, "schedule_start_at_utc": schedule_start.isoformat(), "next_renewal_due_at_utc": due.isoformat(), "renewal_interval_days": interval, "reminder_days_before_due": reminder, "schedule_note": note, "source_retention_custody_renewal_verification_declared_sha256": declared, "source_retention_custody_renewal_verification_computed_sha256": computed, "source_retention_custody_renewal_verification_status": source_status, "source_retention_custody_renewal_verification_trust_banner": source_trust, "custody_renewal_id": str(retention_custody_renewal_verification_raw.get("custody_renewal_id") or "").strip() or None, "source_retention_custody_renewal_status": renewal_status, "source_retention_index_sha256": str(retention_custody_renewal_verification_raw.get("source_retention_index_sha256") or "").strip() or None, "recomputed_retention_entry_count": entry_count, "recomputed_retention_ready_entry_count": ready_count, "checklist": checklist}
    statement_sha = _custody_schedule_statement_digest(statement_source)
    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("SCHEDULE_RESTRICTED" if warnings else "SCHEDULED")
    trust = "TRUSTED" if status == "SCHEDULED" else ("TRUST_RESTRICTED" if status == "SCHEDULE_RESTRICTED" else "UNTRUSTED")
    artifact = PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact(generated_at_utc=now, tracking_id=str(retention_custody_renewal_verification_raw.get("tracking_id") or "").strip() or None, schedule_status=status, trust_banner=trust, custody_schedule_id=schedule_id, scheduled_by=operator, custody_location=location, schedule_start_at_utc=schedule_start.isoformat(), next_renewal_due_at_utc=due.isoformat(), renewal_interval_days=interval, reminder_days_before_due=reminder, schedule_note=note, source_retention_custody_renewal_verification_artifact_path=str(retention_custody_renewal_verification_artifact_path), source_retention_custody_renewal_verification_declared_sha256=declared, source_retention_custody_renewal_verification_computed_sha256=computed, source_retention_custody_renewal_verification_status=source_status, source_retention_custody_renewal_verification_trust_banner=source_trust, retention_custody_renewal_verification_artifact_hash_valid=source_hash_valid, source_retention_custody_renewal_status=renewal_status, retention_custody_renewal_artifact_hash_valid=bool(retention_custody_renewal_verification_raw.get("retention_custody_renewal_artifact_hash_valid")), custody_renewal_id=str(retention_custody_renewal_verification_raw.get("custody_renewal_id") or "").strip() or None, custody_renewal_statement_hash_valid=bool(retention_custody_renewal_verification_raw.get("custody_renewal_statement_hash_valid")), source_retention_index_sha256=str(retention_custody_renewal_verification_raw.get("source_retention_index_sha256") or "").strip() or None, recomputed_retention_entry_count=entry_count, recomputed_retention_ready_entry_count=ready_count, missing_entry_count=missing_count, digest_mismatch_entry_count=mismatch_count, custody_schedule_statement_sha256=statement_sha, checklist=checklist, blockers=blockers, warnings=warnings)
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_schedule_artifact(*, retention_custody_renewal_verification_artifact_path: Path | None = None, output_root: Path | None = None, scheduled_by: str = "operator", custody_location: str = "local-retention", reminder_days_before_due: int = 7, schedule_note: str | None = None, generated_at_utc: datetime | None = None) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact(retention_custody_renewal_verification_artifact_path=retention_custody_renewal_verification_artifact_path, output_root=output_root)
    if source_path is None or raw is None:
        source_path = (retention_custody_renewal_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_renewal_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_schedule_artifact(retention_custody_renewal_verification_artifact_path=source_path, retention_custody_renewal_verification_raw=raw, scheduled_by=scheduled_by, custody_location=custody_location, reminder_days_before_due=reminder_days_before_due, schedule_note=schedule_note, generated_at_utc=generated_at_utc)
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_schedules"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_schedule.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyScheduleView:
    blockers = _strings(raw.get("blockers")); warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyScheduleView(tracking_id=str(raw.get("tracking_id") or "").strip() or None, artifact_path=str(path), artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None, generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None, schedule_status=str(raw.get("schedule_status") or "UNKNOWN"), trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"), custody_schedule_id=str(raw.get("custody_schedule_id") or "").strip() or None, scheduled_by=str(raw.get("scheduled_by") or "").strip() or None, custody_location=str(raw.get("custody_location") or "").strip() or None, schedule_start_at_utc=str(raw.get("schedule_start_at_utc") or "").strip() or None, next_renewal_due_at_utc=str(raw.get("next_renewal_due_at_utc") or "").strip() or None, renewal_interval_days=_int(raw.get("renewal_interval_days")), reminder_days_before_due=_int(raw.get("reminder_days_before_due")), schedule_note=str(raw.get("schedule_note") or "").strip() or None, source_retention_custody_renewal_verification_artifact_path=str(raw.get("source_retention_custody_renewal_verification_artifact_path") or "").strip() or None, source_retention_custody_renewal_verification_status=str(raw.get("source_retention_custody_renewal_verification_status") or "").strip() or None, retention_custody_renewal_verification_artifact_hash_valid=bool(raw.get("retention_custody_renewal_verification_artifact_hash_valid")), source_retention_custody_renewal_status=str(raw.get("source_retention_custody_renewal_status") or "").strip() or None, retention_custody_renewal_artifact_hash_valid=bool(raw.get("retention_custody_renewal_artifact_hash_valid")), custody_renewal_id=str(raw.get("custody_renewal_id") or "").strip() or None, custody_renewal_statement_hash_valid=bool(raw.get("custody_renewal_statement_hash_valid")), source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None, recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")), recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")), missing_entry_count=_int(raw.get("missing_entry_count")), digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")), custody_schedule_statement_sha256=str(raw.get("custody_schedule_statement_sha256") or "").strip() or None, blocker_count=len(blockers), warning_count=len(warnings), blockers=blockers, warnings=warnings)


def read_paper_execution_evidence_bundle_retention_custody_schedule_views(*, repo_root: Path | None = None, output_root: Path | None = None) -> list[PaperExecutionEvidenceBundleRetentionCustodyScheduleView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_schedules/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_schedule.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = ["_custody_schedule_statement_digest", "build_paper_execution_evidence_bundle_retention_custody_schedule_artifact", "find_latest_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact", "read_paper_execution_evidence_bundle_retention_custody_schedule_views", "write_paper_execution_evidence_bundle_retention_custody_schedule_artifact"]
