"""Read-only custodian acceptance certificate for verified paper evidence-chain handoff."""
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
    PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact,
    PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
    *,
    retention_handoff_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_handoff_verification_artifact_path is not None:
        path = retention_handoff_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_handoff_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _acceptance_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_handoff_acceptance_statement/v1",
        "accepting_custodian_id": str(raw.get("accepting_custodian_id") or "operator").strip() or "operator",
        "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
        "acceptance_note": str(raw.get("acceptance_note") or "").strip() or None,
        "source_retention_handoff_verification_declared_sha256": str(raw.get("source_retention_handoff_verification_declared_sha256") or "").strip() or None,
        "source_retention_handoff_verification_computed_sha256": str(raw.get("source_retention_handoff_verification_computed_sha256") or "").strip() or None,
        "source_retention_handoff_verification_status": str(raw.get("source_retention_handoff_verification_status") or "UNKNOWN"),
        "source_retention_handoff_verification_trust_banner": str(raw.get("source_retention_handoff_verification_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_handoff_artifact_path": str(raw.get("source_retention_handoff_artifact_path") or "").strip() or None,
        "source_retention_handoff_status": str(raw.get("source_retention_handoff_status") or "UNKNOWN"),
        "source_retention_handoff_trust_banner": str(raw.get("source_retention_handoff_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_receipt_artifact_path": str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
    *,
    retention_handoff_verification_artifact_path: Path,
    retention_handoff_verification_raw: dict[str, Any],
    accepting_custodian_id: str = "operator",
    custody_location: str = "local-retention",
    acceptance_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_sha = str(retention_handoff_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_sha = _embedded_digest(retention_handoff_verification_raw)
    source_hash_valid = _declared_matches_computed(declared_sha, computed_sha)
    if not retention_handoff_verification_raw:
        blockers.append("RETENTION_HANDOFF_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_HANDOFF_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str(retention_handoff_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_handoff_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_HANDOFF_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_HANDOFF_VERIFICATION_TRUST_NOT_TRUSTED")

    handoff_status = str(retention_handoff_verification_raw.get("source_retention_handoff_status") or "UNKNOWN")
    handoff_trust = str(retention_handoff_verification_raw.get("source_retention_handoff_trust_banner") or "TRUST_RESTRICTED")
    if handoff_status == "BLOCKED":
        blockers.append("RETENTION_HANDOFF_STATUS_BLOCKED")
    elif handoff_status != "READY_FOR_HANDOFF":
        warnings.append("RETENTION_HANDOFF_STATUS_NOT_READY_FOR_HANDOFF")
    if handoff_trust != "TRUSTED":
        warnings.append("RETENTION_HANDOFF_TRUST_NOT_TRUSTED")

    for field, code in [
        ("retention_handoff_artifact_hash_valid", "RETENTION_HANDOFF_ARTIFACT_HASH_NOT_VALID"),
        ("handoff_statement_hash_valid", "RETENTION_HANDOFF_STATEMENT_HASH_NOT_VALID"),
        ("retention_signoff_verification_artifact_hash_valid", "RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_handoff_verification_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_handoff_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_handoff_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_handoff_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_handoff_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_handoff_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_HANDOFF_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_handoff_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_HANDOFF_VERIFICATION_WARNING:{item}")

    custodian = str(accepting_custodian_id or "operator").strip() or "operator"
    location = str(custody_location or "local-retention").strip() or "local-retention"
    note = str(acceptance_note or "").strip() or None
    checklist = [
        "retention handoff verification artifact hash valid",
        "retention handoff verification status PASS",
        "retention handoff artifact hash valid",
        "retention handoff statement hash valid",
        "retention signoff verification artifact hash valid",
        "retained artifact files present",
        "retained artifact file digests match",
        "custodian accepted custody read-only",
        "no paper/live order authority granted",
        "no files copied by acceptance artifact",
    ]
    statement_source = {
        "accepting_custodian_id": custodian,
        "custody_location": location,
        "acceptance_note": note,
        "source_retention_handoff_verification_declared_sha256": declared_sha,
        "source_retention_handoff_verification_computed_sha256": computed_sha,
        "source_retention_handoff_verification_status": source_status,
        "source_retention_handoff_verification_trust_banner": source_trust,
        "source_retention_handoff_artifact_path": str(retention_handoff_verification_raw.get("source_retention_handoff_artifact_path") or "").strip() or None,
        "source_retention_handoff_status": handoff_status,
        "source_retention_handoff_trust_banner": handoff_trust,
        "source_retention_receipt_artifact_path": str(retention_handoff_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(retention_handoff_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    acceptance_statement_sha = canonical_json_sha256({"schema_version": "paper_execution_evidence_bundle_retention_handoff_acceptance_statement/v1", **statement_source})

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("ACCEPTED_RESTRICTED" if warnings else "ACCEPTED_FOR_CUSTODY")
    trust = "UNTRUSTED" if blockers else ("TRUST_RESTRICTED" if warnings else "TRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_handoff_verification_raw.get("tracking_id") or "").strip() or None,
        acceptance_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        accepting_custodian_id=custodian,
        custody_location=location,
        acceptance_note=note,
        source_retention_handoff_verification_artifact_path=str(retention_handoff_verification_artifact_path),
        source_retention_handoff_verification_declared_sha256=declared_sha,
        source_retention_handoff_verification_computed_sha256=computed_sha,
        source_retention_handoff_verification_status=source_status,
        source_retention_handoff_verification_trust_banner=source_trust,
        retention_handoff_verification_artifact_hash_valid=source_hash_valid,
        source_retention_handoff_artifact_path=str(retention_handoff_verification_raw.get("source_retention_handoff_artifact_path") or "").strip() or None,
        source_retention_handoff_status=handoff_status,
        source_retention_handoff_trust_banner=handoff_trust,
        retention_handoff_artifact_hash_valid=bool(retention_handoff_verification_raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(retention_handoff_verification_raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(retention_handoff_verification_raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_handoff_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_handoff_verification_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_handoff_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        acceptance_statement_sha256=acceptance_statement_sha,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
    *,
    retention_handoff_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    accepting_custodian_id: str = "operator",
    custody_location: str = "local-retention",
    acceptance_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
        retention_handoff_verification_artifact_path=retention_handoff_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_handoff_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_handoff_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
        retention_handoff_verification_artifact_path=source_path,
        retention_handoff_verification_raw=raw,
        accepting_custodian_id=accepting_custodian_id,
        custody_location=custody_location,
        acceptance_note=acceptance_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_handoff_acceptances"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_handoff_acceptance.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        acceptance_status=str(raw.get("acceptance_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        accepting_custodian_id=str(raw.get("accepting_custodian_id") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        acceptance_note=str(raw.get("acceptance_note") or "").strip() or None,
        source_retention_handoff_verification_artifact_path=str(raw.get("source_retention_handoff_verification_artifact_path") or "").strip() or None,
        source_retention_handoff_verification_declared_sha256=str(raw.get("source_retention_handoff_verification_declared_sha256") or "").strip() or None,
        source_retention_handoff_verification_status=str(raw.get("source_retention_handoff_verification_status") or "").strip() or None,
        source_retention_handoff_verification_trust_banner=str(raw.get("source_retention_handoff_verification_trust_banner") or "").strip() or None,
        retention_handoff_verification_artifact_hash_valid=bool(raw.get("retention_handoff_verification_artifact_hash_valid")),
        source_retention_handoff_artifact_path=str(raw.get("source_retention_handoff_artifact_path") or "").strip() or None,
        source_retention_handoff_status=str(raw.get("source_retention_handoff_status") or "").strip() or None,
        source_retention_handoff_trust_banner=str(raw.get("source_retention_handoff_trust_banner") or "").strip() or None,
        retention_handoff_artifact_hash_valid=bool(raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        acceptance_statement_sha256=str(raw.get("acceptance_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_handoff_acceptance_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_handoff_acceptances/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff_acceptance.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView] = []
    for path in sorted(set(candidates), key=_mtime, reverse=True)[:limit]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        try:
            rows.append(_view_from_raw(path, raw))
        except ValueError:
            continue
    return sorted(rows, key=lambda row: row.generated_at_utc or "", reverse=True)[:limit]


__all__ = [
    "build_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_handoff_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_handoff_acceptance_views",
    "write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact",
    "_acceptance_statement_digest",
]
