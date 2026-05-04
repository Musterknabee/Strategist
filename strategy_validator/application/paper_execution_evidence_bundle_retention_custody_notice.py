"""Read-only operator notice for scheduled paper evidence retention custody renewal."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import _declared_matches_computed, _embedded_digest, _int, _mtime, _safe_read_json, _strings
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule import _parse_dt
from strategy_validator.contracts.paper_execution import PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact, PaperExecutionEvidenceBundleRetentionCustodyNoticeView
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(*, retention_custody_schedule_verification_artifact_path: Path | None = None, output_root: Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_schedule_verification_artifact_path is not None:
        path = retention_custody_schedule_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_schedule_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_schedule_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_notice_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    schedule_id = str(raw.get("custody_schedule_id") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_custody_schedule_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256({"tracking_id": tracking_id, "custody_schedule_id": schedule_id, "source_custody_schedule_verification_sha256": source_sha})
    return f"retention-custody-notice:{tracking_id}:{digest[:16]}"


def _custody_notice_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    return canonical_json_sha256({
        "schema_version": "paper_execution_evidence_bundle_retention_custody_notice_statement/v1",
        "custody_notice_id": str(raw.get("custody_notice_id") or "").strip() or None,
        "notified_by": str(raw.get("notified_by") or "operator").strip() or "operator",
        "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
        "notice_status": str(raw.get("notice_status") or "UNKNOWN"),
        "notice_generated_for_utc": str(raw.get("notice_generated_for_utc") or "").strip() or None,
        "next_renewal_due_at_utc": str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
        "reminder_window_starts_at_utc": str(raw.get("reminder_window_starts_at_utc") or "").strip() or None,
        "days_until_due": _int(raw.get("days_until_due")),
        "renewal_interval_days": _int(raw.get("renewal_interval_days")),
        "reminder_days_before_due": _int(raw.get("reminder_days_before_due")),
        "notice_message": str(raw.get("notice_message") or "").strip() or None,
        "notice_note": str(raw.get("notice_note") or "").strip() or None,
        "source_retention_custody_schedule_verification_declared_sha256": str(raw.get("source_retention_custody_schedule_verification_declared_sha256") or "").strip() or None,
        "source_retention_custody_schedule_verification_computed_sha256": str(raw.get("source_retention_custody_schedule_verification_computed_sha256") or "").strip() or None,
        "source_retention_custody_schedule_verification_status": str(raw.get("source_retention_custody_schedule_verification_status") or "UNKNOWN"),
        "source_retention_custody_schedule_verification_trust_banner": str(raw.get("source_retention_custody_schedule_verification_trust_banner") or "TRUST_RESTRICTED"),
        "custody_schedule_id": str(raw.get("custody_schedule_id") or "").strip() or None,
        "source_retention_custody_schedule_status": str(raw.get("source_retention_custody_schedule_status") or "UNKNOWN"),
        "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(raw.get("checklist")),
    })


def _days_until_due(now: datetime, due: datetime | None) -> int:
    if due is None:
        return 0
    return math.ceil((due - now).total_seconds() / 86400)


def build_paper_execution_evidence_bundle_retention_custody_notice_artifact(*, retention_custody_schedule_verification_artifact_path: Path, retention_custody_schedule_verification_raw: dict[str, Any], notified_by: str = "operator", custody_location: str = "local-retention", notice_note: str | None = None, generated_at_utc: datetime | None = None) -> PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    declared = str(retention_custody_schedule_verification_raw.get("artifact_sha256") or "").strip() or None
    computed = _embedded_digest(retention_custody_schedule_verification_raw)
    source_hash_valid = _declared_matches_computed(declared, computed)
    if not retention_custody_schedule_verification_raw:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_VERIFICATION_ARTIFACT_SHA256_MISMATCH")
    source_status = str(retention_custody_schedule_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_custody_schedule_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_SCHEDULE_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_SCHEDULE_VERIFICATION_TRUST_NOT_TRUSTED")
    schedule_status = str(retention_custody_schedule_verification_raw.get("source_retention_custody_schedule_status") or "UNKNOWN")
    if schedule_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_SCHEDULE_STATUS_BLOCKED")
    elif schedule_status not in {"SCHEDULED", "SCHEDULE_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_SCHEDULE_STATUS_NOT_SCHEDULED")
    for field, code in [("retention_custody_schedule_artifact_hash_valid", "RETENTION_CUSTODY_SCHEDULE_ARTIFACT_HASH_NOT_VALID"), ("custody_schedule_statement_hash_valid", "RETENTION_CUSTODY_SCHEDULE_STATEMENT_HASH_NOT_VALID")]:
        if not bool(retention_custody_schedule_verification_raw.get(field)):
            blockers.append(code)
    entry_count = _int(retention_custody_schedule_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_schedule_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_schedule_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_schedule_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_NOTICE_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_NOTICE_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_NOTICE_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_NOTICE_HAS_DIGEST_MISMATCHES")
    for item in _strings(retention_custody_schedule_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_SCHEDULE_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_custody_schedule_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_SCHEDULE_VERIFICATION_WARNING:{item}")

    operator = str(notified_by or "operator").strip() or "operator"
    location = str(custody_location or retention_custody_schedule_verification_raw.get("custody_location") or "local-retention").strip() or "local-retention"
    note = str(notice_note or "").strip() or None
    due = _parse_dt(retention_custody_schedule_verification_raw.get("next_renewal_due_at_utc"))
    reminder_days = max(0, _int(retention_custody_schedule_verification_raw.get("reminder_days_before_due")) or 7)
    reminder_start = due - timedelta(days=reminder_days) if due is not None else None
    days = _days_until_due(now, due)
    if due is None:
        blockers.append("RETENTION_CUSTODY_NOTICE_MISSING_DUE_DATE")
    due_in_window = bool(due is not None and reminder_start is not None and now >= reminder_start)
    notice_id = _custody_notice_id(retention_custody_schedule_verification_raw)
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "NOTICE_RESTRICTED"
    else:
        status = "NOTICE_DUE" if due_in_window else "NOTICE_PENDING"
    message = "Paper evidence-chain retention custody renewal is due for operator action." if status == "NOTICE_DUE" else "Paper evidence-chain retention custody renewal is scheduled; no renewal action is due yet."
    if status == "BLOCKED":
        message = "Paper evidence-chain retention custody renewal notice is blocked; inspect upstream schedule verification."
    elif status == "NOTICE_RESTRICTED":
        message = "Paper evidence-chain retention custody renewal notice is trust-restricted; inspect warnings before action."
    checklist = ["retention custody schedule verification artifact hash valid", "retention custody schedule verification status PASS", "custody schedule artifact hash valid", "custody schedule statement hash valid", "next renewal due date preserved", "operator notice status computed"]
    statement_source = {"custody_notice_id": notice_id, "notified_by": operator, "custody_location": location, "notice_status": status, "notice_generated_for_utc": now.isoformat(), "next_renewal_due_at_utc": due.isoformat() if due else None, "reminder_window_starts_at_utc": reminder_start.isoformat() if reminder_start else None, "days_until_due": days, "renewal_interval_days": _int(retention_custody_schedule_verification_raw.get("renewal_interval_days")), "reminder_days_before_due": reminder_days, "notice_message": message, "notice_note": note, "source_retention_custody_schedule_verification_declared_sha256": declared, "source_retention_custody_schedule_verification_computed_sha256": computed, "source_retention_custody_schedule_verification_status": source_status, "source_retention_custody_schedule_verification_trust_banner": source_trust, "custody_schedule_id": str(retention_custody_schedule_verification_raw.get("custody_schedule_id") or "").strip() or None, "source_retention_custody_schedule_status": schedule_status, "source_retention_index_sha256": str(retention_custody_schedule_verification_raw.get("source_retention_index_sha256") or "").strip() or None, "recomputed_retention_entry_count": entry_count, "recomputed_retention_ready_entry_count": ready_count, "checklist": checklist}
    statement_sha = _custody_notice_statement_digest(statement_source)
    blockers = sorted(set(blockers)); warnings = sorted(set(warnings))
    trust = "TRUSTED" if status in {"NOTICE_DUE", "NOTICE_PENDING"} else ("TRUST_RESTRICTED" if status == "NOTICE_RESTRICTED" else "UNTRUSTED")
    artifact = PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact(generated_at_utc=now, tracking_id=str(retention_custody_schedule_verification_raw.get("tracking_id") or "").strip() or None, notice_status=status, trust_banner=trust, custody_notice_id=notice_id, notified_by=operator, custody_location=location, notice_generated_for_utc=now.isoformat(), next_renewal_due_at_utc=due.isoformat() if due else None, reminder_window_starts_at_utc=reminder_start.isoformat() if reminder_start else None, days_until_due=days, renewal_interval_days=_int(retention_custody_schedule_verification_raw.get("renewal_interval_days")), reminder_days_before_due=reminder_days, notice_message=message, notice_note=note, source_retention_custody_schedule_verification_artifact_path=str(retention_custody_schedule_verification_artifact_path), source_retention_custody_schedule_verification_declared_sha256=declared, source_retention_custody_schedule_verification_computed_sha256=computed, source_retention_custody_schedule_verification_status=source_status, source_retention_custody_schedule_verification_trust_banner=source_trust, retention_custody_schedule_verification_artifact_hash_valid=source_hash_valid, source_retention_custody_schedule_status=schedule_status, retention_custody_schedule_artifact_hash_valid=bool(retention_custody_schedule_verification_raw.get("retention_custody_schedule_artifact_hash_valid")), custody_schedule_id=str(retention_custody_schedule_verification_raw.get("custody_schedule_id") or "").strip() or None, custody_schedule_statement_hash_valid=bool(retention_custody_schedule_verification_raw.get("custody_schedule_statement_hash_valid")), source_retention_index_sha256=str(retention_custody_schedule_verification_raw.get("source_retention_index_sha256") or "").strip() or None, recomputed_retention_entry_count=entry_count, recomputed_retention_ready_entry_count=ready_count, missing_entry_count=missing_count, digest_mismatch_entry_count=mismatch_count, custody_notice_statement_sha256=statement_sha, checklist=checklist, blockers=blockers, warnings=warnings)
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_notice_artifact(*, retention_custody_schedule_verification_artifact_path: Path | None = None, output_root: Path | None = None, notified_by: str = "operator", custody_location: str = "local-retention", notice_note: str | None = None, generated_at_utc: datetime | None = None) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(retention_custody_schedule_verification_artifact_path=retention_custody_schedule_verification_artifact_path, output_root=output_root)
    if source_path is None or raw is None:
        source_path = (retention_custody_schedule_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_schedule_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_notice_artifact(retention_custody_schedule_verification_artifact_path=source_path, retention_custody_schedule_verification_raw=raw, notified_by=notified_by, custody_location=custody_location, notice_note=notice_note, generated_at_utc=generated_at_utc)
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_notices"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_notice.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyNoticeView:
    blockers = _strings(raw.get("blockers")); warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyNoticeView(tracking_id=str(raw.get("tracking_id") or "").strip() or None, artifact_path=str(path), artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None, generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None, notice_status=str(raw.get("notice_status") or "UNKNOWN"), trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"), custody_notice_id=str(raw.get("custody_notice_id") or "").strip() or None, notified_by=str(raw.get("notified_by") or "").strip() or None, custody_location=str(raw.get("custody_location") or "").strip() or None, notice_generated_for_utc=str(raw.get("notice_generated_for_utc") or "").strip() or None, next_renewal_due_at_utc=str(raw.get("next_renewal_due_at_utc") or "").strip() or None, reminder_window_starts_at_utc=str(raw.get("reminder_window_starts_at_utc") or "").strip() or None, days_until_due=_int(raw.get("days_until_due")), renewal_interval_days=_int(raw.get("renewal_interval_days")), reminder_days_before_due=_int(raw.get("reminder_days_before_due")), notice_message=str(raw.get("notice_message") or "").strip() or None, notice_note=str(raw.get("notice_note") or "").strip() or None, source_retention_custody_schedule_verification_artifact_path=str(raw.get("source_retention_custody_schedule_verification_artifact_path") or "").strip() or None, source_retention_custody_schedule_verification_status=str(raw.get("source_retention_custody_schedule_verification_status") or "").strip() or None, retention_custody_schedule_verification_artifact_hash_valid=bool(raw.get("retention_custody_schedule_verification_artifact_hash_valid")), source_retention_custody_schedule_status=str(raw.get("source_retention_custody_schedule_status") or "").strip() or None, retention_custody_schedule_artifact_hash_valid=bool(raw.get("retention_custody_schedule_artifact_hash_valid")), custody_schedule_id=str(raw.get("custody_schedule_id") or "").strip() or None, custody_schedule_statement_hash_valid=bool(raw.get("custody_schedule_statement_hash_valid")), source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None, recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")), recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")), missing_entry_count=_int(raw.get("missing_entry_count")), digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")), custody_notice_statement_sha256=str(raw.get("custody_notice_statement_sha256") or "").strip() or None, blocker_count=len(blockers), warning_count=len(warnings), blockers=blockers, warnings=warnings)


def read_paper_execution_evidence_bundle_retention_custody_notice_views(*, repo_root: Path | None = None, output_root: Path | None = None) -> list[PaperExecutionEvidenceBundleRetentionCustodyNoticeView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_notices/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_notice.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = ["_custody_notice_statement_digest", "build_paper_execution_evidence_bundle_retention_custody_notice_artifact", "find_latest_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact", "read_paper_execution_evidence_bundle_retention_custody_notice_views", "write_paper_execution_evidence_bundle_retention_custody_notice_artifact"]
