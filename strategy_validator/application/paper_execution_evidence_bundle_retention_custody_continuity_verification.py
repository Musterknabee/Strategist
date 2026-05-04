"""Read-only verifier for paper evidence-chain retention custody continuity attestations."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity import _custody_continuity_statement_digest
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import (
    _declared_matches_computed,
    _embedded_digest,
    _int,
    _mtime,
    _safe_read_json,
    _strings,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_continuity_artifact(
    *,
    retention_custody_continuity_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_continuity_artifact_path is not None:
        path = retention_custody_continuity_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_continuities/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_continuity.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact(
    *,
    retention_custody_continuity_artifact_path: Path,
    retention_custody_continuity_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_continuity_sha = str(retention_custody_continuity_raw.get("artifact_sha256") or "").strip() or None
    computed_continuity_sha = _embedded_digest(retention_custody_continuity_raw)
    continuity_hash_valid = _declared_matches_computed(declared_continuity_sha, computed_continuity_sha)
    if not retention_custody_continuity_raw:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not continuity_hash_valid:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_ARTIFACT_SHA256_MISMATCH")

    continuity_status = str(retention_custody_continuity_raw.get("continuity_status") or "UNKNOWN")
    continuity_trust = str(retention_custody_continuity_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if continuity_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_CONTINUITY_STATUS_BLOCKED")
    elif continuity_status not in {"CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_STATUS_NOT_ATTESTED")
    if continuity_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_CONTINUITY_TRUST_NOT_TRUSTED")

    declared_statement_sha = str(retention_custody_continuity_raw.get("custody_continuity_statement_sha256") or "").strip() or None
    computed_statement_sha = _custody_continuity_statement_digest(retention_custody_continuity_raw)
    statement_hash_valid = _declared_matches_computed(declared_statement_sha, computed_statement_sha)
    if not statement_hash_valid:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_STATEMENT_SHA256_MISMATCH")

    source_path_raw = str(retention_custody_continuity_raw.get("source_retention_custody_audit_verification_artifact_path") or "").strip()
    source_raw: dict[str, Any] | None = _safe_read_json(Path(source_path_raw)) if source_path_raw else None
    source_declared = str(retention_custody_continuity_raw.get("source_retention_custody_audit_verification_declared_sha256") or "").strip() or None
    source_computed_from_continuity = str(retention_custody_continuity_raw.get("source_retention_custody_audit_verification_computed_sha256") or "").strip() or None
    source_computed_now = _embedded_digest(source_raw) if source_raw else None
    source_hash_valid = bool(retention_custody_continuity_raw.get("retention_custody_audit_verification_artifact_hash_valid")) and _declared_matches_computed(source_declared, source_computed_from_continuity)
    if source_raw is not None and source_declared != source_computed_now:
        source_hash_valid = False
    if not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_AUDIT_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str((source_raw or {}).get("verification_status") or retention_custody_continuity_raw.get("source_retention_custody_audit_verification_status") or "UNKNOWN")
    if source_status != "PASS":
        blockers.append("RETENTION_CUSTODY_AUDIT_VERIFICATION_NOT_PASS")

    for field, code in [
        ("retention_custody_audit_artifact_hash_valid", "RETENTION_CUSTODY_AUDIT_ARTIFACT_HASH_NOT_VALID"),
        ("custody_audit_statement_hash_valid", "RETENTION_CUSTODY_AUDIT_STATEMENT_HASH_NOT_VALID"),
        ("retention_custody_seal_verification_artifact_hash_valid", "RETENTION_CUSTODY_SEAL_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_custody_seal_artifact_hash_valid", "RETENTION_CUSTODY_SEAL_ARTIFACT_HASH_NOT_VALID"),
        ("custody_seal_statement_hash_valid", "RETENTION_CUSTODY_SEAL_STATEMENT_HASH_NOT_VALID"),
        ("retention_custody_register_verification_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
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
        if not bool(retention_custody_continuity_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_custody_continuity_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_continuity_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_continuity_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_continuity_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_CONTINUITY_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_custody_continuity_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_CONTINUITY_BLOCKER:{item}")
    for item in _strings(retention_custody_continuity_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_CONTINUITY_WARNING:{item}")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_continuity_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_retention_custody_continuity_artifact_path=str(retention_custody_continuity_artifact_path),
        source_retention_custody_continuity_declared_sha256=declared_continuity_sha,
        source_retention_custody_continuity_computed_sha256=computed_continuity_sha,
        source_retention_custody_continuity_status=continuity_status,
        source_retention_custody_continuity_trust_banner=continuity_trust,
        retention_custody_continuity_artifact_hash_valid=continuity_hash_valid,
        custody_continuity_id=str(retention_custody_continuity_raw.get("custody_continuity_id") or "").strip() or None,
        attested_by=str(retention_custody_continuity_raw.get("attested_by") or "").strip() or None,
        custody_location=str(retention_custody_continuity_raw.get("custody_location") or "").strip() or None,
        continuity_note=str(retention_custody_continuity_raw.get("continuity_note") or "").strip() or None,
        custody_continuity_statement_declared_sha256=declared_statement_sha,
        custody_continuity_statement_computed_sha256=computed_statement_sha,
        custody_continuity_statement_hash_valid=statement_hash_valid,
        source_retention_custody_audit_verification_artifact_path=source_path_raw or None,
        source_retention_custody_audit_verification_declared_sha256=source_declared,
        source_retention_custody_audit_verification_status=source_status,
        retention_custody_audit_verification_artifact_hash_valid=source_hash_valid,
        source_retention_custody_audit_status=str(retention_custody_continuity_raw.get("source_retention_custody_audit_status") or "").strip() or None,
        retention_custody_audit_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_custody_audit_artifact_hash_valid")),
        custody_audit_id=str(retention_custody_continuity_raw.get("custody_audit_id") or "").strip() or None,
        custody_audit_statement_hash_valid=bool(retention_custody_continuity_raw.get("custody_audit_statement_hash_valid")),
        source_retention_custody_seal_verification_status=str(retention_custody_continuity_raw.get("source_retention_custody_seal_verification_status") or "").strip() or None,
        retention_custody_seal_verification_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_custody_seal_verification_artifact_hash_valid")),
        source_retention_custody_seal_status=str(retention_custody_continuity_raw.get("source_retention_custody_seal_status") or "").strip() or None,
        retention_custody_seal_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_custody_seal_artifact_hash_valid")),
        custody_seal_id=str(retention_custody_continuity_raw.get("custody_seal_id") or "").strip() or None,
        custody_seal_statement_hash_valid=bool(retention_custody_continuity_raw.get("custody_seal_statement_hash_valid")),
        retention_custody_register_verification_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_custody_register_verification_artifact_hash_valid")),
        retention_custody_register_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_custody_register_artifact_hash_valid")),
        custody_register_id=str(retention_custody_continuity_raw.get("custody_register_id") or "").strip() or None,
        custody_register_statement_hash_valid=bool(retention_custody_continuity_raw.get("custody_register_statement_hash_valid")),
        retention_handoff_acceptance_verification_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_handoff_acceptance_verification_artifact_hash_valid")),
        retention_handoff_acceptance_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_handoff_acceptance_artifact_hash_valid")),
        acceptance_statement_hash_valid=bool(retention_custody_continuity_raw.get("acceptance_statement_hash_valid")),
        retention_handoff_verification_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_handoff_verification_artifact_hash_valid")),
        retention_handoff_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(retention_custody_continuity_raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(retention_custody_continuity_raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_custody_continuity_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_custody_continuity_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_custody_continuity_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact(
    *,
    retention_custody_continuity_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_continuity_artifact(
        retention_custody_continuity_artifact_path=retention_custody_continuity_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_custody_continuity_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_continuity.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact(
        retention_custody_continuity_artifact_path=source_path,
        retention_custody_continuity_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_continuity_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_continuity_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_retention_custody_continuity_artifact_path=str(raw.get("source_retention_custody_continuity_artifact_path") or "").strip() or None,
        source_retention_custody_continuity_declared_sha256=str(raw.get("source_retention_custody_continuity_declared_sha256") or "").strip() or None,
        source_retention_custody_continuity_status=str(raw.get("source_retention_custody_continuity_status") or "").strip() or None,
        retention_custody_continuity_artifact_hash_valid=bool(raw.get("retention_custody_continuity_artifact_hash_valid")),
        custody_continuity_id=str(raw.get("custody_continuity_id") or "").strip() or None,
        attested_by=str(raw.get("attested_by") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        continuity_note=str(raw.get("continuity_note") or "").strip() or None,
        custody_continuity_statement_declared_sha256=str(raw.get("custody_continuity_statement_declared_sha256") or "").strip() or None,
        custody_continuity_statement_computed_sha256=str(raw.get("custody_continuity_statement_computed_sha256") or "").strip() or None,
        custody_continuity_statement_hash_valid=bool(raw.get("custody_continuity_statement_hash_valid")),
        source_retention_custody_audit_verification_artifact_path=str(raw.get("source_retention_custody_audit_verification_artifact_path") or "").strip() or None,
        source_retention_custody_audit_verification_declared_sha256=str(raw.get("source_retention_custody_audit_verification_declared_sha256") or "").strip() or None,
        source_retention_custody_audit_verification_status=str(raw.get("source_retention_custody_audit_verification_status") or "").strip() or None,
        retention_custody_audit_verification_artifact_hash_valid=bool(raw.get("retention_custody_audit_verification_artifact_hash_valid")),
        source_retention_custody_audit_status=str(raw.get("source_retention_custody_audit_status") or "").strip() or None,
        retention_custody_audit_artifact_hash_valid=bool(raw.get("retention_custody_audit_artifact_hash_valid")),
        custody_audit_id=str(raw.get("custody_audit_id") or "").strip() or None,
        custody_audit_statement_hash_valid=bool(raw.get("custody_audit_statement_hash_valid")),
        source_retention_custody_seal_verification_status=str(raw.get("source_retention_custody_seal_verification_status") or "").strip() or None,
        retention_custody_seal_verification_artifact_hash_valid=bool(raw.get("retention_custody_seal_verification_artifact_hash_valid")),
        source_retention_custody_seal_status=str(raw.get("source_retention_custody_seal_status") or "").strip() or None,
        retention_custody_seal_artifact_hash_valid=bool(raw.get("retention_custody_seal_artifact_hash_valid")),
        custody_seal_id=str(raw.get("custody_seal_id") or "").strip() or None,
        custody_seal_statement_hash_valid=bool(raw.get("custody_seal_statement_hash_valid")),
        retention_custody_register_verification_artifact_hash_valid=bool(raw.get("retention_custody_register_verification_artifact_hash_valid")),
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
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_custody_continuity_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
) -> list[PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_continuity_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_continuity_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views: list[PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView] = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = [
    "build_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_continuity_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_continuity_verification_views",
    "write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact",
]
