"""Independent verifier for paper evidence-chain retention custody register entries."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import _custody_register_statement_digest
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import (
    _declared_matches_computed,
    _embedded_digest,
    _int,
    _mtime,
    _safe_read_json,
    _strings,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def find_latest_paper_execution_evidence_bundle_retention_custody_register_artifact(
    *,
    retention_custody_register_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if retention_custody_register_artifact_path is not None:
        path = retention_custody_register_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_custody_registers/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_register.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
    *,
    retention_custody_register_artifact_path: Path,
    retention_custody_register_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_register_sha = str(retention_custody_register_raw.get("artifact_sha256") or "").strip() or None
    computed_register_sha = _embedded_digest(retention_custody_register_raw)
    register_hash_valid = _declared_matches_computed(declared_register_sha, computed_register_sha)
    if not retention_custody_register_raw:
        blockers.append("RETENTION_CUSTODY_REGISTER_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not register_hash_valid:
        blockers.append("RETENTION_CUSTODY_REGISTER_ARTIFACT_SHA256_MISMATCH")

    register_status = str(retention_custody_register_raw.get("register_status") or "UNKNOWN")
    register_trust = str(retention_custody_register_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if register_status == "BLOCKED":
        blockers.append("RETENTION_CUSTODY_REGISTER_STATUS_BLOCKED")
    elif register_status != "REGISTERED":
        warnings.append("RETENTION_CUSTODY_REGISTER_STATUS_NOT_REGISTERED")
    if register_trust != "TRUSTED":
        warnings.append("RETENTION_CUSTODY_REGISTER_TRUST_NOT_TRUSTED")

    declared_statement_sha = str(retention_custody_register_raw.get("custody_register_statement_sha256") or "").strip() or None
    computed_statement_sha = _custody_register_statement_digest(retention_custody_register_raw)
    statement_hash_valid = _declared_matches_computed(declared_statement_sha, computed_statement_sha)
    if not statement_hash_valid:
        blockers.append("RETENTION_CUSTODY_REGISTER_STATEMENT_SHA256_MISMATCH")

    source_path_raw = str(retention_custody_register_raw.get("source_retention_handoff_acceptance_verification_artifact_path") or "").strip()
    source_path = Path(source_path_raw).expanduser() if source_path_raw else None
    source_raw = _safe_read_json(source_path) if source_path is not None else None
    if source_path is None or source_raw is None:
        blockers.append("SOURCE_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")

    source_declared = str((source_raw or {}).get("artifact_sha256") or "").strip() or None
    source_recomputed = _embedded_digest(source_raw or {})
    register_declared_source = str(retention_custody_register_raw.get("source_retention_handoff_acceptance_verification_declared_sha256") or "").strip() or None
    register_computed_source = str(retention_custody_register_raw.get("source_retention_handoff_acceptance_verification_computed_sha256") or "").strip() or None
    source_hash_valid = False
    if source_raw:
        source_hash_valid = (
            _declared_matches_computed(source_declared, source_recomputed)
            and _declared_matches_computed(register_declared_source, source_recomputed)
            and _declared_matches_computed(register_computed_source, source_recomputed)
        )
    if not source_hash_valid:
        blockers.append("SOURCE_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str((source_raw or {}).get("verification_status") or retention_custody_register_raw.get("source_retention_handoff_acceptance_verification_status") or "UNKNOWN")
    if source_status != "PASS":
        blockers.append("SOURCE_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION_NOT_PASS")

    for field, code in [
        ("retention_handoff_acceptance_verification_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_ACCEPTANCE_VERIFICATION_HASH_INVALID"),
        ("retention_handoff_acceptance_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_ACCEPTANCE_HASH_INVALID"),
        ("acceptance_statement_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_ACCEPTANCE_STATEMENT_HASH_INVALID"),
        ("retention_handoff_verification_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_HANDOFF_VERIFICATION_HASH_INVALID"),
        ("retention_handoff_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_HANDOFF_HASH_INVALID"),
        ("handoff_statement_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_HANDOFF_STATEMENT_HASH_INVALID"),
        ("retention_signoff_verification_artifact_hash_valid", "RETENTION_CUSTODY_REGISTER_DECLARED_SIGNOFF_VERIFICATION_HASH_INVALID"),
    ]:
        if not bool(retention_custody_register_raw.get(field)):
            blockers.append(code)

    entry_count = _int(retention_custody_register_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_custody_register_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_custody_register_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_custody_register_raw.get("digest_mismatch_entry_count"))
    if source_raw:
        if entry_count != _int(source_raw.get("recomputed_retention_entry_count")):
            blockers.append("RETENTION_CUSTODY_REGISTER_ENTRY_COUNT_SOURCE_MISMATCH")
        if ready_count != _int(source_raw.get("recomputed_retention_ready_entry_count")):
            blockers.append("RETENTION_CUSTODY_REGISTER_READY_ENTRY_COUNT_SOURCE_MISMATCH")
        if missing_count != _int(source_raw.get("missing_entry_count")):
            blockers.append("RETENTION_CUSTODY_REGISTER_MISSING_ENTRY_COUNT_SOURCE_MISMATCH")
        if mismatch_count != _int(source_raw.get("digest_mismatch_entry_count")):
            blockers.append("RETENTION_CUSTODY_REGISTER_DIGEST_MISMATCH_COUNT_SOURCE_MISMATCH")
    if entry_count <= 0:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_CUSTODY_REGISTER_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_custody_register_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_CUSTODY_REGISTER_BLOCKER:{item}")
    for item in _strings(retention_custody_register_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_CUSTODY_REGISTER_WARNING:{item}")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_custody_register_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_retention_custody_register_artifact_path=str(retention_custody_register_artifact_path),
        source_retention_custody_register_declared_sha256=declared_register_sha,
        source_retention_custody_register_computed_sha256=computed_register_sha,
        source_retention_custody_register_status=register_status,
        source_retention_custody_register_trust_banner=register_trust,
        retention_custody_register_artifact_hash_valid=register_hash_valid,
        custody_register_id=str(retention_custody_register_raw.get("custody_register_id") or "").strip() or None,
        registered_by=str(retention_custody_register_raw.get("registered_by") or "").strip() or None,
        custody_location=str(retention_custody_register_raw.get("custody_location") or "").strip() or None,
        register_note=str(retention_custody_register_raw.get("register_note") or "").strip() or None,
        custody_register_statement_declared_sha256=declared_statement_sha,
        custody_register_statement_computed_sha256=computed_statement_sha,
        custody_register_statement_hash_valid=statement_hash_valid,
        source_retention_handoff_acceptance_verification_artifact_path=source_path_raw or None,
        source_retention_handoff_acceptance_verification_declared_sha256=register_declared_source,
        source_retention_handoff_acceptance_verification_status=source_status,
        retention_handoff_acceptance_verification_artifact_hash_valid=source_hash_valid,
        retention_handoff_acceptance_artifact_hash_valid=bool(retention_custody_register_raw.get("retention_handoff_acceptance_artifact_hash_valid")),
        acceptance_statement_hash_valid=bool(retention_custody_register_raw.get("acceptance_statement_hash_valid")),
        retention_handoff_verification_artifact_hash_valid=bool(retention_custody_register_raw.get("retention_handoff_verification_artifact_hash_valid")),
        retention_handoff_artifact_hash_valid=bool(retention_custody_register_raw.get("retention_handoff_artifact_hash_valid")),
        handoff_statement_hash_valid=bool(retention_custody_register_raw.get("handoff_statement_hash_valid")),
        retention_signoff_verification_artifact_hash_valid=bool(retention_custody_register_raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_custody_register_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_custody_register_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_custody_register_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
    *,
    retention_custody_register_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_custody_register_artifact(
        retention_custody_register_artifact_path=retention_custody_register_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_custody_register_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_custody_register.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
        retention_custody_register_artifact_path=source_path,
        retention_custody_register_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_custody_register_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_custody_register_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_retention_custody_register_artifact_path=str(raw.get("source_retention_custody_register_artifact_path") or "").strip() or None,
        source_retention_custody_register_declared_sha256=str(raw.get("source_retention_custody_register_declared_sha256") or "").strip() or None,
        source_retention_custody_register_computed_sha256=str(raw.get("source_retention_custody_register_computed_sha256") or "").strip() or None,
        source_retention_custody_register_status=str(raw.get("source_retention_custody_register_status") or "").strip() or None,
        retention_custody_register_artifact_hash_valid=bool(raw.get("retention_custody_register_artifact_hash_valid")),
        custody_register_id=str(raw.get("custody_register_id") or "").strip() or None,
        registered_by=str(raw.get("registered_by") or "").strip() or None,
        custody_location=str(raw.get("custody_location") or "").strip() or None,
        register_note=str(raw.get("register_note") or "").strip() or None,
        custody_register_statement_declared_sha256=str(raw.get("custody_register_statement_declared_sha256") or "").strip() or None,
        custody_register_statement_computed_sha256=str(raw.get("custody_register_statement_computed_sha256") or "").strip() or None,
        custody_register_statement_hash_valid=bool(raw.get("custody_register_statement_hash_valid")),
        source_retention_handoff_acceptance_verification_artifact_path=str(raw.get("source_retention_handoff_acceptance_verification_artifact_path") or "").strip() or None,
        source_retention_handoff_acceptance_verification_declared_sha256=str(raw.get("source_retention_handoff_acceptance_verification_declared_sha256") or "").strip() or None,
        source_retention_handoff_acceptance_verification_status=str(raw.get("source_retention_handoff_acceptance_verification_status") or "").strip() or None,
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


def read_paper_execution_evidence_bundle_retention_custody_register_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_custody_register_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_custody_register_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView] = []
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
    "build_paper_execution_evidence_bundle_retention_custody_register_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_custody_register_artifact",
    "read_paper_execution_evidence_bundle_retention_custody_register_verification_views",
    "write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact",
]
