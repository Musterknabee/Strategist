"""Read-only custody register for accepted paper evidence-chain retention."""
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
    PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyRegisterView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact(
    *,
    retention_handoff_acceptance_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_handoff_acceptance_verification_artifact_path is not None:
        path = retention_handoff_acceptance_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_handoff_acceptance_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff_acceptance_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_register_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    source_index = str(raw.get("source_retention_index_sha256") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_handoff_acceptance_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256({"tracking_id": tracking_id, "source_retention_index_sha256": source_index, "source_acceptance_verification_sha256": source_sha})
    return f"retention-custody:{tracking_id}:{digest[:16]}"


def _custody_register_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_custody_register_statement/v1",
        "custody_register_id": str(raw.get("custody_register_id") or "").strip() or None,
        "registered_by": str(raw.get("registered_by") or "operator").strip() or "operator",
        "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
        "register_note": str(raw.get("register_note") or "").strip() or None,
        "source_retention_handoff_acceptance_verification_declared_sha256": str(raw.get("source_retention_handoff_acceptance_verification_declared_sha256") or "").strip() or None,
        "source_retention_handoff_acceptance_verification_computed_sha256": str(raw.get("source_retention_handoff_acceptance_verification_computed_sha256") or "").strip() or None,
        "source_retention_handoff_acceptance_verification_status": str(raw.get("source_retention_handoff_acceptance_verification_status") or "UNKNOWN"),
        "source_retention_handoff_acceptance_verification_trust_banner": str(raw.get("source_retention_handoff_acceptance_verification_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_handoff_acceptance_artifact_path": str(raw.get("source_retention_handoff_acceptance_artifact_path") or "").strip() or None,
        "source_retention_handoff_acceptance_status": str(raw.get("source_retention_handoff_acceptance_status") or "UNKNOWN"),
        "source_retention_handoff_acceptance_trust_banner": str(raw.get("source_retention_handoff_acceptance_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_receipt_artifact_path": str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_custody_register_artifact(
    *,
    retention_handoff_acceptance_verification_artifact_path: Path,
    retention_handoff_acceptance_verification_raw: dict[str, Any],
    registered_by: str = "operator",
    custody_location: str = "local-retention",
    register_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_sha = str(retention_handoff_acceptance_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_sha = _embedded_digest(retention_handoff_acceptance_verification_raw)
    source_hash_valid = _declared_matches_computed(declared_sha, computed_sha)
    if not retention_handoff_acceptance_verification_raw:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str(retention_handoff_acceptance_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_handoff_acceptance_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_TRUST_NOT_TRUSTED")

    acceptance_status = str(retention_handoff_acceptance_verification_raw.get("source_retention_handoff_acceptance_status") or "UNKNOWN")
    acceptance_trust = str(retention_handoff_acceptance_verification_raw.get("source_retention_handoff_acceptance_trust_banner") or "TRUST_RESTRICTED")
    if acceptance_status == "BLOCKED":
        blockers.append("RETENTION_HANDOFF_ACCEPTANCE_STATUS_BLOCKED")
    elif acceptance_status != "ACCEPTED_FOR_CUSTODY":
        warnings.append("RETENTION_HANDOFF_ACCEPTANCE_STATUS_NOT_ACCEPTED_FOR_CUSTODY")
    if acceptance_trust != "TRUSTED":
        warnings.append("RETENTION_HANDOFF_ACCEPTANCE_TRUST_NOT_TRUSTED")

    for field, code in [
        ("retention_handoff_acceptance_artifact_hash_valid", "RETENTION_HANDOFF_ACCEPTANCE_ARTIFACT_HASH_NOT_VALID"),
        ("acceptance_statement_hash_valid", "RETENTION_HANDOFF_ACCEPTANCE_STATEMENT_HASH_NOT_VALID"),
        ("retention_handoff_verification_artifact_hash_valid", "RETENTION_HANDOFF_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_handoff_artifact_hash_valid", "RETENTION_HANDOFF_ARTIFACT_HASH_NOT_VALID"),
        ("handoff_statement_hash_valid", "RETENTION_HANDOFF_STATEMENT_HASH_NOT_VALID"),
        ("retention_signoff_verification_artifact_hash_valid", "RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_handoff_acceptance_verification_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_handoff_acceptance_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_handoff_acceptance_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_handoff_acceptance_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_handoff_acceptance_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_handoff_acceptance_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_handoff_acceptance_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_WARNING:{item}")

    operator = str(registered_by or "operator").strip() or "operator"
    location = str(custody_location or "local-retention").strip() or "local-retention"
    note = str(register_note or "").strip() or None
    register_id = _custody_register_id(retention_handoff_acceptance_verification_raw)
    checklist = [
        "retention handoff acceptance verification artifact hash valid",
        "retention handoff acceptance verification status PASS",
        "retention handoff acceptance artifact hash valid",
        "retention handoff acceptance statement hash valid",
        "retention handoff verification artifact hash valid",
        "retention handoff artifact hash valid",
        "retained artifact files present",
        "retained artifact file digests match",
        "custody register is read-only",
        "no paper/live order authority granted",
        "no files copied by custody register artifact",
    ]
    statement_source = {
        "custody_register_id": register_id,
        "registered_by": operator,
        "custody_location": location,
        "register_note": note,
        "source_retention_handoff_acceptance_verification_declared_sha256": declared_sha,
        "source_retention_handoff_acceptance_verification_computed_sha256": computed_sha,
        "source_retention_handoff_acceptance_verification_status": source_status,
        "source_retention_handoff_acceptance_verification_trust_banner": source_trust,
        "source_retention_handoff_acceptance_artifact_path": str(retention_handoff_acceptance_verification_raw.get("source_retention_handoff_acceptance_artifact_path") or "").strip() or None,
        "source_retention_handoff_acceptance_status": acceptance_status,
        "source_retention_handoff_acceptance_trust_banner": acceptance_trust,
        "source_retention_receipt_artifact_path": str(retention_handoff_acceptance_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(retention_handoff_acceptance_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    statement_sha = canonical_json_sha256({"schema_version": "paper_execution_evidence_bundle_retention_custody_register_statement/v1", **statement_source})

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("REGISTERED_RESTRICTED" if warnings else "REGISTERED")
    trust = "UNTRUSTED" if blockers else ("TRUST_RESTRICTED" if warnings else "TRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_handoff_acceptance_verification_raw.get("tracking_id") or "").strip() or None,
        register_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        custody_register_id=register_id,
        registered_by=operator,
        custody_location=location,
        register_note=note,
        source_retention_handoff_acceptance_verification_artifact_path=str(retention_handoff_acceptance_verification_artifact_path),
        source_retention_handoff_acceptance_verification_declared_sha256=declared_sha,
        source_retention_handoff_acceptance_verification_computed_sha256=computed_sha,
        source_retention_handoff_acceptance_verification_status=source_status,
        source_retention_handoff_acceptance_verification_trust_banner=source_trust,
        retention_handoff_acceptance_verification_artifact_hash_valid=source_hash_valid,
        source_retention_handoff_acceptance_artifact_path=str(retention_handoff_acceptance_verification_raw.get("source_retention_handoff_acceptance_artifact_path") or "").strip() or None,
        source_retention_handoff_acceptance_status=acceptance_status,
        source_retention_handoff_acceptance_trust_banner=acceptance_trust,
        retention_handoff_acceptance_artifact_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("retention_handoff_acceptance_artifact_hash_valid")),
        acceptance_statement_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("acceptance_statement_hash_valid")),
        retention_handoff_verification_artifact_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("retention_handoff_verification_artifact_hash_valid")),
        retention_handoff_artifact_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(retention_handoff_acceptance_verification_raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_handoff_acceptance_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_handoff_acceptance_verification_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_handoff_acceptance_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        custody_register_statement_sha256=statement_sha,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_register_artifact(
    *,
    retention_handoff_acceptance_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    registered_by: str = "operator",
    custody_location: str = "local-retention",
    register_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact(
        retention_handoff_acceptance_verification_artifact_path=retention_handoff_acceptance_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_handoff_acceptance_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_handoff_acceptance_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_handoff_acceptance_verification_artifact_path=source_path,
        retention_handoff_acceptance_verification_raw=raw,
        registered_by=registered_by,
        custody_location=custody_location,
        register_note=register_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_registers"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_register.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyRegisterView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyRegisterView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        register_status=str(raw.get("register_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        custody_register_id=str(raw.get("custody_register_id") or "").strip() or None,
        registered_by=str(raw.get("registered_by") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        register_note=str(raw.get("register_note") or "").strip() or None,
        source_retention_handoff_acceptance_verification_artifact_path=str(raw.get("source_retention_handoff_acceptance_verification_artifact_path") or "").strip() or None,
        source_retention_handoff_acceptance_verification_declared_sha256=str(raw.get("source_retention_handoff_acceptance_verification_declared_sha256") or "").strip() or None,
        source_retention_handoff_acceptance_verification_status=str(raw.get("source_retention_handoff_acceptance_verification_status") or "").strip() or None,
        retention_handoff_acceptance_verification_artifact_hash_valid=bool(raw.get("retention_handoff_acceptance_verification_artifact_hash_valid")),
        source_retention_handoff_acceptance_status=str(raw.get("source_retention_handoff_acceptance_status") or "").strip() or None,
        retention_handoff_acceptance_artifact_hash_valid=bool(raw.get("retention_handoff_acceptance_artifact_hash_valid")),
        acceptance_statement_hash_valid=bool(raw.get("acceptance_statement_hash_valid")),
        retention_handoff_verification_artifact_hash_valid=bool(raw.get("retention_handoff_verification_artifact_hash_valid")),
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
        custody_register_statement_sha256=str(raw.get("custody_register_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_custody_register_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionCustodyRegisterView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_custody_registers/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_register.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterView] = []
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
    "build_paper_execution_evidence_bundle_retention_custody_register_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_register_views",
    "write_paper_execution_evidence_bundle_retention_custody_register_artifact",
    "_custody_register_statement_digest",
]
