"""Read-only custody seal for verified paper evidence-chain retention custody."""
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
    PaperExecutionEvidenceBundleRetentionCustodySealArtifact,
    PaperExecutionEvidenceBundleRetentionCustodySealView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
    *,
    retention_custody_register_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_register_verification_artifact_path is not None:
        path = retention_custody_register_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_register_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_register_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _custody_seal_id(raw: dict[str, Any]) -> str:
    tracking_id = str(raw.get("tracking_id") or "untracked").strip() or "untracked"
    register_id = str(raw.get("custody_register_id") or "").strip() or None
    source_index = str(raw.get("source_retention_index_sha256") or "").strip() or None
    source_sha = str(raw.get("artifact_sha256") or raw.get("source_retention_custody_register_declared_sha256") or "").strip() or None
    digest = canonical_json_sha256(
        {
            "tracking_id": tracking_id,
            "custody_register_id": register_id,
            "source_retention_index_sha256": source_index,
            "source_custody_register_verification_sha256": source_sha,
        }
    )
    return f"retention-custody-seal:{tracking_id}:{digest[:16]}"


def _custody_seal_statement_digest(raw: dict[str, Any]) -> str | None:
    if not raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_custody_seal_statement/v1",
        "custody_seal_id": str(raw.get("custody_seal_id") or "").strip() or None,
        "sealed_by": str(raw.get("sealed_by") or "operator").strip() or "operator",
        "custody_location": str(raw.get("custody_location") or "local-retention").strip() or "local-retention",
        "seal_note": str(raw.get("seal_note") or "").strip() or None,
        "source_retention_custody_register_verification_declared_sha256": str(raw.get("source_retention_custody_register_verification_declared_sha256") or "").strip() or None,
        "source_retention_custody_register_verification_computed_sha256": str(raw.get("source_retention_custody_register_verification_computed_sha256") or "").strip() or None,
        "source_retention_custody_register_verification_status": str(raw.get("source_retention_custody_register_verification_status") or "UNKNOWN"),
        "source_retention_custody_register_verification_trust_banner": str(raw.get("source_retention_custody_register_verification_trust_banner") or "TRUST_RESTRICTED"),
        "custody_register_id": str(raw.get("custody_register_id") or "").strip() or None,
        "source_retention_custody_register_artifact_path": str(raw.get("source_retention_custody_register_artifact_path") or "").strip() or None,
        "source_retention_custody_register_status": str(raw.get("source_retention_custody_register_status") or "UNKNOWN"),
        "source_retention_custody_register_trust_banner": str(raw.get("source_retention_custody_register_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_receipt_artifact_path": str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_custody_seal_artifact(
    *,
    retention_custody_register_verification_artifact_path: Path,
    retention_custody_register_verification_raw: dict[str, Any],
    sealed_by: str = "operator",
    custody_location: str = "local-retention",
    seal_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodySealArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_sha = str(retention_custody_register_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_sha = _embedded_digest(retention_custody_register_verification_raw)
    source_hash_valid = _declared_matches_computed(declared_sha, computed_sha)
    if not retention_custody_register_verification_raw:
        blockers.append("RETENTION_CUSTODY_REGISTER_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_REGISTER_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str(retention_custody_register_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_custody_register_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_REGISTER_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_REGISTER_VERIFICATION_TRUST_NOT_TRUSTED")

    register_status = str(retention_custody_register_verification_raw.get("source_retention_custody_register_status") or "UNKNOWN")
    register_trust = str(retention_custody_register_verification_raw.get("source_retention_custody_register_trust_banner") or "TRUST_RESTRICTED")
    if register_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_REGISTER_STATUS_BLOCKED")
    elif register_status != "REGISTERED":
        warnings.append("RETENTION_CUSTODY_REGISTER_STATUS_NOT_REGISTERED")
    if register_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_REGISTER_TRUST_NOT_TRUSTED")

    for field, code in [
        ("retention_custody_register_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_ARTIFACT_HASH_NOT_VALID"),
        ("custody_register_statement_hash_valid", "RETENTION_CUSTODY_REGISTER_STATEMENT_HASH_NOT_VALID"),
        ("retention_handoff_acceptance_verification_artifact_hash_valid", "RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_handoff_acceptance_artifact_hash_valid", "RETENTION_HANDOFF_ACCEPTANCE_ARTIFACT_HASH_NOT_VALID"),
        ("acceptance_statement_hash_valid", "RETENTION_HANDOFF_ACCEPTANCE_STATEMENT_HASH_NOT_VALID"),
        ("retention_handoff_verification_artifact_hash_valid", "RETENTION_HANDOFF_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_handoff_artifact_hash_valid", "RETENTION_HANDOFF_ARTIFACT_HASH_NOT_VALID"),
        ("handoff_statement_hash_valid", "RETENTION_HANDOFF_STATEMENT_HASH_NOT_VALID"),
        ("retention_signoff_verification_artifact_hash_valid", "RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_custody_register_verification_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_custody_register_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_register_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_register_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_register_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_SEAL_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_SEAL_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_SEAL_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_SEAL_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_custody_register_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_REGISTER_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_custody_register_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_REGISTER_VERIFICATION_WARNING:{item}")

    operator = str(sealed_by or "operator").strip() or "operator"
    location = str(custody_location or "local-retention").strip() or "local-retention"
    note = str(seal_note or "").strip() or None
    seal_id = _custody_seal_id(retention_custody_register_verification_raw)
    checklist = [
        "retention custody register verification artifact hash valid",
        "retention custody register verification status PASS",
        "retention custody register artifact hash valid",
        "custody register statement hash valid",
        "retention handoff acceptance verification artifact hash valid",
        "retention handoff acceptance statement hash valid",
        "retained artifact files present",
        "retained artifact file digests match",
        "custody seal is read-only",
        "no paper/live order authority granted",
        "no files copied by custody seal artifact",
    ]
    statement_source = {
        "custody_seal_id": seal_id,
        "sealed_by": operator,
        "custody_location": location,
        "seal_note": note,
        "source_retention_custody_register_verification_declared_sha256": declared_sha,
        "source_retention_custody_register_verification_computed_sha256": computed_sha,
        "source_retention_custody_register_verification_status": source_status,
        "source_retention_custody_register_verification_trust_banner": source_trust,
        "custody_register_id": str(retention_custody_register_verification_raw.get("custody_register_id") or "").strip() or None,
        "source_retention_custody_register_artifact_path": str(retention_custody_register_verification_raw.get("source_retention_custody_register_artifact_path") or "").strip() or None,
        "source_retention_custody_register_status": register_status,
        "source_retention_custody_register_trust_banner": register_trust,
        "source_retention_receipt_artifact_path": str(retention_custody_register_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(retention_custody_register_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    statement_sha = canonical_json_sha256({"schema_version": "paper_execution_evidence_bundle_retention_custody_seal_statement/v1", **statement_source})

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("SEALED_RESTRICTED" if warnings else "SEALED")
    trust = "TRUSTED" if status == "SEALED" else ("TRUST_RESTRICTED" if status == "SEALED_RESTRICTED" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionCustodySealArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_register_verification_raw.get("tracking_id") or "").strip() or None,
        seal_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        custody_seal_id=seal_id,
        sealed_by=operator,
        custody_location=location,
        seal_note=note,
        source_retention_custody_register_verification_artifact_path=str(retention_custody_register_verification_artifact_path),
        source_retention_custody_register_verification_declared_sha256=declared_sha,
        source_retention_custody_register_verification_computed_sha256=computed_sha,
        source_retention_custody_register_verification_status=source_status,
        source_retention_custody_register_verification_trust_banner=source_trust,
        retention_custody_register_verification_artifact_hash_valid=source_hash_valid,
        source_retention_custody_register_artifact_path=str(retention_custody_register_verification_raw.get("source_retention_custody_register_artifact_path") or "").strip() or None,
        source_retention_custody_register_status=register_status,
        source_retention_custody_register_trust_banner=register_trust,
        retention_custody_register_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_custody_register_artifact_hash_valid")),
        custody_register_id=str(retention_custody_register_verification_raw.get("custody_register_id") or "").strip() or None,
        custody_register_statement_hash_valid=bool(retention_custody_register_verification_raw.get("custody_register_statement_hash_valid")),
        source_retention_handoff_acceptance_verification_artifact_path=str(retention_custody_register_verification_raw.get("source_retention_handoff_acceptance_verification_artifact_path") or "").strip() or None,
        source_retention_handoff_acceptance_verification_status=str(retention_custody_register_verification_raw.get("source_retention_handoff_acceptance_verification_status") or "").strip() or None,
        retention_handoff_acceptance_verification_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_handoff_acceptance_verification_artifact_hash_valid")),
        retention_handoff_acceptance_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_handoff_acceptance_artifact_hash_valid")),
        acceptance_statement_hash_valid=bool(retention_custody_register_verification_raw.get("acceptance_statement_hash_valid")),
        retention_handoff_verification_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_handoff_verification_artifact_hash_valid")),
        retention_handoff_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(retention_custody_register_verification_raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(retention_custody_register_verification_raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_custody_register_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_custody_register_verification_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_custody_register_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        custody_seal_statement_sha256=statement_sha,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_seal_artifact(
    *,
    retention_custody_register_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    sealed_by: str = "operator",
    custody_location: str = "local-retention",
    seal_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodySealArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
        retention_custody_register_verification_artifact_path=retention_custody_register_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_custody_register_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_register_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_seal_artifact(
        retention_custody_register_verification_artifact_path=source_path,
        retention_custody_register_verification_raw=raw,
        sealed_by=sealed_by,
        custody_location=custody_location,
        seal_note=seal_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_seals"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_seal.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodySealView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodySealView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        seal_status=str(raw.get("seal_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        custody_seal_id=str(raw.get("custody_seal_id") or "").strip() or None,
        sealed_by=str(raw.get("sealed_by") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        seal_note=str(raw.get("seal_note") or "").strip() or None,
        source_retention_custody_register_verification_artifact_path=str(raw.get("source_retention_custody_register_verification_artifact_path") or "").strip() or None,
        source_retention_custody_register_verification_declared_sha256=str(raw.get("source_retention_custody_register_verification_declared_sha256") or "").strip() or None,
        source_retention_custody_register_verification_status=str(raw.get("source_retention_custody_register_verification_status") or "").strip() or None,
        retention_custody_register_verification_artifact_hash_valid=bool(raw.get("retention_custody_register_verification_artifact_hash_valid")),
        source_retention_custody_register_status=str(raw.get("source_retention_custody_register_status") or "").strip() or None,
        retention_custody_register_artifact_hash_valid=bool(raw.get("retention_custody_register_artifact_hash_valid")),
        custody_register_id=str(raw.get("custody_register_id") or "").strip() or None,
        custody_register_statement_hash_valid=bool(raw.get("custody_register_statement_hash_valid")),
        retention_handoff_acceptance_verification_artifact_hash_valid=bool(raw.get("retention_handoff_acceptance_verification_artifact_hash_valid")),
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
        custody_seal_statement_sha256=str(raw.get("custody_seal_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_custody_seal_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
) -> list[PaperExecutionEvidenceBundleRetentionCustodySealView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_seals/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_seal.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views: list[PaperExecutionEvidenceBundleRetentionCustodySealView] = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = [
    "build_paper_execution_evidence_bundle_retention_custody_seal_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_register_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_seal_views",
    "write_paper_execution_evidence_bundle_retention_custody_seal_artifact",
    "_custody_seal_statement_digest",
]
