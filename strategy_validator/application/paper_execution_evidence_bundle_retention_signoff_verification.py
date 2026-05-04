"""Read-only verifier for paper evidence-chain retention signoff certificates.

The verifier replays the retention-signoff certificate's own digest, its
embedded operator signoff statement digest, and the referenced retention
verification artifact digest. It does not copy retained files, submit orders,
promote strategies, or mutate the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionSignoffVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _strings(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw if x not in (None, "")]
    if raw in (None, ""):
        return []
    return [str(raw)]


def _embedded_digest(raw: dict[str, Any], *, digest_key: str = "artifact_sha256") -> str | None:
    if not raw:
        return None
    plain = dict(raw)
    plain.pop(digest_key, None)
    return canonical_json_sha256(plain)


def _declared_matches_computed(declared: str | None, computed: str | None) -> bool:
    declared = (declared or "").strip()
    computed = (computed or "").strip()
    if not declared or not computed:
        return False
    return declared == computed or computed.startswith(declared)


def find_latest_paper_execution_evidence_bundle_retention_signoff_artifact(
    *,
    retention_signoff_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper retention signoff artifact."""

    if retention_signoff_artifact_path is not None:
        path = retention_signoff_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_signoffs/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_signoff.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _signoff_statement_digest(signoff_raw: dict[str, Any]) -> str | None:
    if not signoff_raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_signoff_statement/v1",
        "operator_id": str(signoff_raw.get("operator_id") or "operator").strip() or "operator",
        "decision_note": str(signoff_raw.get("decision_note") or "").strip() or None,
        "source_retention_verification_artifact_sha256": str(signoff_raw.get("source_retention_verification_declared_sha256") or "").strip() or None,
        "source_retention_verification_computed_sha256": str(signoff_raw.get("source_retention_verification_computed_sha256") or "").strip() or None,
        "source_retention_verification_status": str(signoff_raw.get("source_retention_verification_status") or "UNKNOWN"),
        "source_retention_verification_trust_banner": str(signoff_raw.get("source_retention_verification_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_receipt_artifact_path": str(signoff_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(signoff_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(signoff_raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(signoff_raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(signoff_raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
    *,
    retention_signoff_artifact_path: Path,
    retention_signoff_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact:
    """Build a read-only verification artifact for a retention signoff certificate."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_signoff_sha = str(retention_signoff_raw.get("artifact_sha256") or "").strip() or None
    computed_signoff_sha = _embedded_digest(retention_signoff_raw)
    signoff_hash_valid = _declared_matches_computed(declared_signoff_sha, computed_signoff_sha)
    if not retention_signoff_raw:
        blockers.append("RETENTION_SIGNOFF_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not signoff_hash_valid:
        blockers.append("RETENTION_SIGNOFF_ARTIFACT_SHA256_MISMATCH")

    signoff_status = str(retention_signoff_raw.get("signoff_status") or "UNKNOWN")
    signoff_trust = str(retention_signoff_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if signoff_status == "BLOCKED":
        blockers.append("RETENTION_SIGNOFF_STATUS_BLOCKED")
    elif signoff_status != "SIGNED_OFF":
        warnings.append("RETENTION_SIGNOFF_STATUS_NOT_SIGNED_OFF")
    if signoff_trust != "TRUSTED":
        warnings.append("RETENTION_SIGNOFF_TRUST_NOT_TRUSTED")

    declared_statement_sha = str(retention_signoff_raw.get("signoff_statement_sha256") or "").strip() or None
    computed_statement_sha = _signoff_statement_digest(retention_signoff_raw)
    statement_hash_valid = _declared_matches_computed(declared_statement_sha, computed_statement_sha)
    if not statement_hash_valid:
        blockers.append("RETENTION_SIGNOFF_STATEMENT_SHA256_MISMATCH")

    source_verification_path_raw = str(retention_signoff_raw.get("source_retention_verification_artifact_path") or "").strip()
    source_verification_path = Path(source_verification_path_raw).expanduser() if source_verification_path_raw else None
    source_verification_raw = _safe_read_json(source_verification_path) if source_verification_path is not None else None
    if source_verification_path is None or source_verification_raw is None:
        blockers.append("SOURCE_RETENTION_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")

    declared_verification_sha = str(retention_signoff_raw.get("source_retention_verification_declared_sha256") or "").strip() or None
    signoff_computed_verification_sha = str(retention_signoff_raw.get("source_retention_verification_computed_sha256") or "").strip() or None
    recomputed_verification_sha = _embedded_digest(source_verification_raw or {})
    source_declared_sha = str((source_verification_raw or {}).get("artifact_sha256") or "").strip() or None
    verification_hash_valid = False
    if source_verification_raw:
        verification_hash_valid = (
            _declared_matches_computed(source_declared_sha, recomputed_verification_sha)
            and _declared_matches_computed(declared_verification_sha, recomputed_verification_sha)
            and _declared_matches_computed(signoff_computed_verification_sha, recomputed_verification_sha)
        )
    if not verification_hash_valid:
        blockers.append("SOURCE_RETENTION_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_verification_status = str((source_verification_raw or {}).get("verification_status") or retention_signoff_raw.get("source_retention_verification_status") or "UNKNOWN")
    source_verification_trust = str((source_verification_raw or {}).get("trust_banner") or retention_signoff_raw.get("source_retention_verification_trust_banner") or "TRUST_RESTRICTED")
    if source_verification_status != "PASS":
        blockers.append("SOURCE_RETENTION_VERIFICATION_NOT_PASS")
    if source_verification_trust != "TRUSTED":
        warnings.append("SOURCE_RETENTION_VERIFICATION_TRUST_NOT_TRUSTED")

    if not bool(retention_signoff_raw.get("retention_verification_artifact_hash_valid")):
        blockers.append("RETENTION_SIGNOFF_DECLARED_VERIFICATION_HASH_INVALID")

    source_entry_count = _int(retention_signoff_raw.get("source_retention_entry_count"))
    source_ready_count = _int(retention_signoff_raw.get("source_retention_ready_entry_count"))
    signoff_entry_count = _int(retention_signoff_raw.get("recomputed_retention_entry_count"))
    signoff_ready_count = _int(retention_signoff_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_signoff_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_signoff_raw.get("digest_mismatch_entry_count"))

    source_recomputed_entry_count = _int((source_verification_raw or {}).get("recomputed_retention_entry_count"))
    source_recomputed_ready_count = _int((source_verification_raw or {}).get("recomputed_retention_ready_entry_count"))
    source_missing_count = _int((source_verification_raw or {}).get("missing_entry_count"))
    source_mismatch_count = _int((source_verification_raw or {}).get("digest_mismatch_entry_count"))
    if source_verification_raw:
        if source_recomputed_entry_count != signoff_entry_count:
            blockers.append("RETENTION_SIGNOFF_ENTRY_COUNT_SOURCE_MISMATCH")
        if source_recomputed_ready_count != signoff_ready_count:
            blockers.append("RETENTION_SIGNOFF_READY_ENTRY_COUNT_SOURCE_MISMATCH")
        if source_missing_count != missing_count:
            blockers.append("RETENTION_SIGNOFF_MISSING_ENTRY_COUNT_SOURCE_MISMATCH")
        if source_mismatch_count != mismatch_count:
            blockers.append("RETENTION_SIGNOFF_DIGEST_MISMATCH_COUNT_SOURCE_MISMATCH")

    if signoff_entry_count <= 0:
        blockers.append("RETENTION_SIGNOFF_HAS_NO_ENTRIES")
    if source_entry_count and source_entry_count != signoff_entry_count:
        blockers.append("RETENTION_SIGNOFF_ENTRY_COUNT_MISMATCH")
    if source_ready_count and source_ready_count != signoff_ready_count:
        blockers.append("RETENTION_SIGNOFF_READY_ENTRY_COUNT_MISMATCH")
    if signoff_entry_count != signoff_ready_count:
        blockers.append("RETENTION_SIGNOFF_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_SIGNOFF_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_SIGNOFF_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_signoff_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_SIGNOFF_BLOCKER:{item}")
    for item in _strings(retention_signoff_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_SIGNOFF_WARNING:{item}")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_signoff_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_retention_signoff_artifact_path=str(retention_signoff_artifact_path),
        source_retention_signoff_declared_sha256=declared_signoff_sha,
        source_retention_signoff_computed_sha256=computed_signoff_sha,
        source_retention_signoff_status=signoff_status,
        source_retention_signoff_trust_banner=signoff_trust,
        retention_signoff_artifact_hash_valid=signoff_hash_valid,
        operator_id=str(retention_signoff_raw.get("operator_id") or "").strip() or None,
        decision_note=str(retention_signoff_raw.get("decision_note") or "").strip() or None,
        signoff_statement_declared_sha256=declared_statement_sha,
        signoff_statement_computed_sha256=computed_statement_sha,
        signoff_statement_hash_valid=statement_hash_valid,
        source_retention_verification_artifact_path=source_verification_path_raw or None,
        source_retention_verification_declared_sha256=declared_verification_sha,
        source_retention_verification_computed_sha256=signoff_computed_verification_sha,
        source_retention_verification_recomputed_sha256=recomputed_verification_sha,
        source_retention_verification_status=source_verification_status,
        source_retention_verification_trust_banner=source_verification_trust,
        retention_verification_artifact_hash_valid=verification_hash_valid,
        source_retention_receipt_artifact_path=str(retention_signoff_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_signoff_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_signoff_raw.get("source_retention_index_sha256") or "").strip() or None,
        source_retention_entry_count=source_entry_count,
        source_retention_ready_entry_count=source_ready_count,
        recomputed_retention_entry_count=signoff_entry_count,
        recomputed_retention_ready_entry_count=signoff_ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
    *,
    retention_signoff_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact]:
    """Verify latest or explicit retention signoff and write latest + history artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_signoff_artifact(
        retention_signoff_artifact_path=retention_signoff_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_signoff_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_signoff.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
        retention_signoff_artifact_path=source_path,
        retention_signoff_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_signoff_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_signoff_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionSignoffVerificationView:
    return PaperExecutionEvidenceBundleRetentionSignoffVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_retention_signoff_artifact_path=str(raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        source_retention_signoff_declared_sha256=str(raw.get("source_retention_signoff_declared_sha256") or "").strip() or None,
        source_retention_signoff_computed_sha256=str(raw.get("source_retention_signoff_computed_sha256") or "").strip() or None,
        source_retention_signoff_status=str(raw.get("source_retention_signoff_status") or "").strip() or None,
        source_retention_signoff_trust_banner=str(raw.get("source_retention_signoff_trust_banner") or "").strip() or None,
        retention_signoff_artifact_hash_valid=bool(raw.get("retention_signoff_artifact_hash_valid")),
        operator_id=str(raw.get("operator_id") or "").strip() or None,
        decision_note=str(raw.get("decision_note") or "").strip() or None,
        signoff_statement_declared_sha256=str(raw.get("signoff_statement_declared_sha256") or "").strip() or None,
        signoff_statement_computed_sha256=str(raw.get("signoff_statement_computed_sha256") or "").strip() or None,
        signoff_statement_hash_valid=bool(raw.get("signoff_statement_hash_valid")),
        source_retention_verification_artifact_path=str(raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        source_retention_verification_declared_sha256=str(raw.get("source_retention_verification_declared_sha256") or "").strip() or None,
        source_retention_verification_status=str(raw.get("source_retention_verification_status") or "").strip() or None,
        source_retention_verification_trust_banner=str(raw.get("source_retention_verification_trust_banner") or "").strip() or None,
        retention_verification_artifact_hash_valid=bool(raw.get("retention_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_retention_signoff_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionSignoffVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_signoff_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_signoff_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionSignoffVerificationView] = []
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
    "build_paper_execution_evidence_bundle_retention_signoff_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_signoff_artifact",
    "read_paper_execution_evidence_bundle_retention_signoff_verification_views",
    "write_paper_execution_evidence_bundle_retention_signoff_verification_artifact",
]
