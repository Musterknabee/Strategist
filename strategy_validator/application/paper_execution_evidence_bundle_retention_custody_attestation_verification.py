"""Read-only verifier for paper evidence retention custody attestation records."""
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
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation import _custody_attestation_statement_digest
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_attestation_artifact(
    *, retention_custody_attestation_artifact_path: Path | None = None, output_root: Path | None = None
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_attestation_artifact_path is not None:
        path = retention_custody_attestation_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_attestations/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_attestation.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
    *,
    retention_custody_attestation_artifact_path: Path,
    retention_custody_attestation_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    declared = str(retention_custody_attestation_raw.get("artifact_sha256") or "").strip() or None
    computed = _embedded_digest(retention_custody_attestation_raw)
    source_hash_valid = _declared_matches_computed(declared, computed)
    if not retention_custody_attestation_raw:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not source_hash_valid:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_ARTIFACT_SHA256_MISMATCH")
    source_status = str(retention_custody_attestation_raw.get("attestation_status") or "UNKNOWN")
    source_trust = str(retention_custody_attestation_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_ATTESTATION_STATUS_BLOCKED")
    elif source_status not in {"ATTESTED", "ATTESTED_RESTRICTED"}:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_STATUS_NOT_RECOGNIZED")
    elif source_status == "ATTESTED_RESTRICTED":
        warnings.append("RETENTION_CUSTODY_ATTESTATION_RESTRICTED")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_ATTESTATION_TRUST_NOT_TRUSTED")
    statement_declared = str(retention_custody_attestation_raw.get("custody_attestation_statement_sha256") or "").strip() or None
    statement_computed = _custody_attestation_statement_digest(retention_custody_attestation_raw)
    statement_hash_valid = _declared_matches_computed(statement_declared, statement_computed)
    if not statement_hash_valid:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_STATEMENT_SHA256_MISMATCH")
    for field, code in [
        ("retention_custody_certification_verification_artifact_hash_valid", "RETENTION_CUSTODY_CERTIFICATION_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_custody_certification_artifact_hash_valid", "RETENTION_CUSTODY_CERTIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("custody_certification_statement_hash_valid", "RETENTION_CUSTODY_CERTIFICATION_STATEMENT_HASH_NOT_VALID"),
        ("retention_custody_reconciliation_verification_artifact_hash_valid", "RETENTION_CUSTODY_RECONCILIATION_VERIFICATION_ARTIFACT_HASH_NOT_VALID"),
        ("retention_custody_reconciliation_artifact_hash_valid", "RETENTION_CUSTODY_RECONCILIATION_ARTIFACT_HASH_NOT_VALID"),
        ("custody_reconciliation_statement_hash_valid", "RETENTION_CUSTODY_RECONCILIATION_STATEMENT_HASH_NOT_VALID"),
    ]:
        if not bool(retention_custody_attestation_raw.get(field)):
            blockers.append(code)
    entry_count = _int(retention_custody_attestation_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_attestation_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_attestation_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_attestation_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_VERIFICATION_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_VERIFICATION_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_VERIFICATION_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_ATTESTATION_VERIFICATION_HAS_DIGEST_MISMATCHES")
    for item in _strings(retention_custody_attestation_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_ATTESTATION_BLOCKER:{item}")
    for item in _strings(retention_custody_attestation_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_ATTESTATION_WARNING:{item}")
    status = "FAIL" if blockers else "PASS"
    trust = "UNTRUSTED" if blockers else ("TRUST_RESTRICTED" if warnings else "TRUSTED")
    artifact = PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_attestation_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,
        trust_banner=trust,
        source_retention_custody_attestation_artifact_path=str(retention_custody_attestation_artifact_path),
        source_retention_custody_attestation_declared_sha256=declared,
        source_retention_custody_attestation_computed_sha256=computed,
        source_retention_custody_attestation_status=source_status,
        source_retention_custody_attestation_trust_banner=source_trust,
        retention_custody_attestation_artifact_hash_valid=source_hash_valid,
        custody_attestation_id=str(retention_custody_attestation_raw.get("custody_attestation_id") or "").strip() or None,
        attested_by=str(retention_custody_attestation_raw.get("attested_by") or "").strip() or None,
        attestation_reason=str(retention_custody_attestation_raw.get("attestation_reason") or "").strip() or None,
        attestation_scope=str(retention_custody_attestation_raw.get("attestation_scope") or "").strip() or None,
        attested_at_utc=str(retention_custody_attestation_raw.get("attested_at_utc") or "").strip() or None,
        attestation_note=str(retention_custody_attestation_raw.get("attestation_note") or "").strip() or None,
        custody_attestation_statement_declared_sha256=statement_declared,
        custody_attestation_statement_computed_sha256=statement_computed,
        custody_attestation_statement_hash_valid=statement_hash_valid,
        source_retention_custody_certification_verification_artifact_path=str(retention_custody_attestation_raw.get("source_retention_custody_certification_verification_artifact_path") or "").strip() or None,
        source_retention_custody_certification_verification_status=str(retention_custody_attestation_raw.get("source_retention_custody_certification_verification_status") or "").strip() or None,
        retention_custody_certification_verification_artifact_hash_valid=bool(retention_custody_attestation_raw.get("retention_custody_certification_verification_artifact_hash_valid")),
        source_retention_custody_certification_status=str(retention_custody_attestation_raw.get("source_retention_custody_certification_status") or "").strip() or None,
        retention_custody_certification_artifact_hash_valid=bool(retention_custody_attestation_raw.get("retention_custody_certification_artifact_hash_valid")),
        custody_certification_id=str(retention_custody_attestation_raw.get("custody_certification_id") or "").strip() or None,
        custody_certification_statement_hash_valid=bool(retention_custody_attestation_raw.get("custody_certification_statement_hash_valid")),
        custody_reconciliation_id=str(retention_custody_attestation_raw.get("custody_reconciliation_id") or "").strip() or None,
        custody_reconciliation_statement_hash_valid=bool(retention_custody_attestation_raw.get("custody_reconciliation_statement_hash_valid")),
        custody_inventory_id=str(retention_custody_attestation_raw.get("custody_inventory_id") or "").strip() or None,
        custody_redeposit_id=str(retention_custody_attestation_raw.get("custody_redeposit_id") or "").strip() or None,
        next_renewal_due_at_utc=str(retention_custody_attestation_raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(retention_custody_attestation_raw.get("days_until_due")),
        source_retention_index_sha256=str(retention_custody_attestation_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
    *, retention_custody_attestation_artifact_path: Path | None = None, output_root: Path | None = None, generated_at_utc: datetime | None = None
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_attestation_artifact(
        retention_custody_attestation_artifact_path=retention_custody_attestation_artifact_path, output_root=output_root
    )
    if source_path is None or raw is None:
        source_path = (retention_custody_attestation_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_attestation.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
        retention_custody_attestation_artifact_path=source_path, retention_custody_attestation_raw=raw, generated_at_utc=generated_at_utc
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_attestation_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_attestation_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),
        source_retention_custody_attestation_artifact_path=str(raw.get("source_retention_custody_attestation_artifact_path") or "").strip() or None,
        source_retention_custody_attestation_status=str(raw.get("source_retention_custody_attestation_status") or "").strip() or None,
        retention_custody_attestation_artifact_hash_valid=bool(raw.get("retention_custody_attestation_artifact_hash_valid")),
        custody_attestation_id=str(raw.get("custody_attestation_id") or "").strip() or None,
        attested_by=str(raw.get("attested_by") or "").strip() or None,
        attestation_reason=str(raw.get("attestation_reason") or "").strip() or None,
        attestation_scope=str(raw.get("attestation_scope") or "").strip() or None,
        attested_at_utc=str(raw.get("attested_at_utc") or "").strip() or None,
        custody_attestation_statement_hash_valid=bool(raw.get("custody_attestation_statement_hash_valid")),
        source_retention_custody_certification_verification_artifact_path=str(raw.get("source_retention_custody_certification_verification_artifact_path") or "").strip() or None,
        source_retention_custody_certification_verification_status=str(raw.get("source_retention_custody_certification_verification_status") or "").strip() or None,
        retention_custody_certification_verification_artifact_hash_valid=bool(raw.get("retention_custody_certification_verification_artifact_hash_valid")),
        source_retention_custody_certification_status=str(raw.get("source_retention_custody_certification_status") or "").strip() or None,
        retention_custody_certification_artifact_hash_valid=bool(raw.get("retention_custody_certification_artifact_hash_valid")),
        custody_certification_id=str(raw.get("custody_certification_id") or "").strip() or None,
        custody_certification_statement_hash_valid=bool(raw.get("custody_certification_statement_hash_valid")),
        custody_reconciliation_id=str(raw.get("custody_reconciliation_id") or "").strip() or None,
        custody_reconciliation_statement_hash_valid=bool(raw.get("custody_reconciliation_statement_hash_valid")),
        custody_inventory_id=str(raw.get("custody_inventory_id") or "").strip() or None,
        custody_redeposit_id=str(raw.get("custody_redeposit_id") or "").strip() or None,
        next_renewal_due_at_utc=str(raw.get("next_renewal_due_at_utc") or "").strip() or None,
        days_until_due=_int(raw.get("days_until_due")),
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


def read_paper_execution_evidence_bundle_retention_custody_attestation_verification_views(*, repo_root: Path | None = None, output_root: Path | None = None) -> list[PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView]:
    root = _paper_broker_root(output_root=output_root)
    if output_root is None and repo_root is not None:
        root = _paper_broker_root(output_root=repo_root / "artifacts" / "paper_broker")
    candidates = list(root.glob("*/evidence_bundle_retention_custody_attestation_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_attestation_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    views = []
    for path in sorted(candidates, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            views.append(_view_from_raw(path, raw))
    return views


__all__ = [
    "build_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_attestation_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_attestation_verification_views",
    "write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact",
]
