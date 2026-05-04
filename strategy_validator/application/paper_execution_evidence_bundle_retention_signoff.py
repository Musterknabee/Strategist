"""Read-only signoff certificate for verified paper evidence-chain retention.

This module writes a durable operator signoff artifact only after a retention
verification artifact exists. It deliberately does not copy retained files,
submit orders, promote strategies, or mutate the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionSignoffArtifact,
    PaperExecutionEvidenceBundleRetentionSignoffView,
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


def find_latest_paper_execution_evidence_bundle_retention_verification_artifact(
    *,
    retention_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper retention verification artifact."""

    if retention_verification_artifact_path is not None:
        path = retention_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_signoff_artifact(
    *,
    retention_verification_artifact_path: Path,
    retention_verification_raw: dict[str, Any],
    operator_id: str = "operator",
    decision_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionSignoffArtifact:
    """Build a read-only signoff certificate from a retention verification artifact."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_verification_sha = str(retention_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_verification_sha = _embedded_digest(retention_verification_raw)
    verification_hash_valid = _declared_matches_computed(declared_verification_sha, computed_verification_sha)
    if not retention_verification_raw:
        blockers.append("RETENTION_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not verification_hash_valid:
        blockers.append("RETENTION_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    verification_status = str(retention_verification_raw.get("verification_status") or "UNKNOWN")
    verification_trust = str(retention_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if verification_status != "PASS":
        blockers.append("RETENTION_VERIFICATION_NOT_PASS")
    if verification_trust != "TRUSTED":
        warnings.append("RETENTION_VERIFICATION_TRUST_NOT_TRUSTED")

    if not bool(retention_verification_raw.get("retention_receipt_hash_valid")):
        blockers.append("RETENTION_RECEIPT_HASH_NOT_VALID")
    if not bool(retention_verification_raw.get("retention_index_hash_valid")):
        blockers.append("RETENTION_INDEX_HASH_NOT_VALID")

    source_entry_count = _int(retention_verification_raw.get("source_retention_entry_count"))
    source_ready_count = _int(retention_verification_raw.get("source_retention_ready_entry_count"))
    recomputed_entry_count = _int(retention_verification_raw.get("recomputed_retention_entry_count"))
    recomputed_ready_count = _int(retention_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_verification_raw.get("digest_mismatch_entry_count"))

    if recomputed_entry_count <= 0:
        blockers.append("RETENTION_VERIFICATION_HAS_NO_ENTRIES")
    if source_entry_count != recomputed_entry_count:
        blockers.append("RETENTION_VERIFICATION_ENTRY_COUNT_MISMATCH")
    if source_ready_count != recomputed_ready_count:
        blockers.append("RETENTION_VERIFICATION_READY_ENTRY_COUNT_MISMATCH")
    if recomputed_entry_count != recomputed_ready_count:
        blockers.append("RETENTION_VERIFICATION_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_VERIFICATION_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_VERIFICATION_HAS_DIGEST_MISMATCHES")

    inherited_blockers = _strings(retention_verification_raw.get("blockers"))
    inherited_warnings = _strings(retention_verification_raw.get("warnings"))
    for item in inherited_blockers:
        blockers.append(f"SOURCE_RETENTION_VERIFICATION_BLOCKER:{item}")
    for item in inherited_warnings:
        warnings.append(f"SOURCE_RETENTION_VERIFICATION_WARNING:{item}")

    operator = str(operator_id or "operator").strip() or "operator"
    note = str(decision_note or "").strip() or None
    checklist = [
        "retention verification artifact hash valid",
        "retention verification status PASS",
        "retention receipt hash valid",
        "retention index hash valid",
        "retained artifact files present",
        "retained artifact file digests match",
        "retained artifact file sizes match",
        "no paper/live order authority granted",
        "no files copied by signoff artifact",
    ]
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_signoff_statement/v1",
        "operator_id": operator,
        "decision_note": note,
        "source_retention_verification_artifact_sha256": declared_verification_sha,
        "source_retention_verification_computed_sha256": computed_verification_sha,
        "source_retention_verification_status": verification_status,
        "source_retention_verification_trust_banner": verification_trust,
        "source_retention_receipt_artifact_path": str(retention_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(retention_verification_raw.get("source_retention_index_declared_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": recomputed_entry_count,
        "recomputed_retention_ready_entry_count": recomputed_ready_count,
        "checklist": checklist,
    }
    statement_sha = canonical_json_sha256(statement)

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("SIGNED_OFF_RESTRICTED" if warnings else "SIGNED_OFF")
    trust = "TRUSTED" if status == "SIGNED_OFF" else ("TRUST_RESTRICTED" if status == "SIGNED_OFF_RESTRICTED" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionSignoffArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_verification_raw.get("tracking_id") or "").strip() or None,
        signoff_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        operator_id=operator,
        decision_note=note,
        source_retention_verification_artifact_path=str(retention_verification_artifact_path),
        source_retention_verification_declared_sha256=declared_verification_sha,
        source_retention_verification_computed_sha256=computed_verification_sha,
        source_retention_verification_status=verification_status,
        source_retention_verification_trust_banner=verification_trust,
        retention_verification_artifact_hash_valid=verification_hash_valid,
        source_retention_receipt_artifact_path=str(retention_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_verification_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_verification_raw.get("source_retention_index_declared_sha256") or "").strip() or None,
        source_retention_entry_count=source_entry_count,
        source_retention_ready_entry_count=source_ready_count,
        recomputed_retention_entry_count=recomputed_entry_count,
        recomputed_retention_ready_entry_count=recomputed_ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        checklist=checklist,
        signoff_statement_sha256=statement_sha,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_signoff_artifact(
    *,
    retention_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    operator_id: str = "operator",
    decision_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionSignoffArtifact]:
    """Write latest and history retention signoff certificates."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_verification_artifact(
        retention_verification_artifact_path=retention_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_signoff_artifact(
        retention_verification_artifact_path=source_path,
        retention_verification_raw=raw,
        operator_id=operator_id,
        decision_note=decision_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_signoffs"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_signoff.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionSignoffView:
    return PaperExecutionEvidenceBundleRetentionSignoffView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        signoff_status=str(raw.get("signoff_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        operator_id=str(raw.get("operator_id") or "").strip() or None,
        decision_note=str(raw.get("decision_note") or "").strip() or None,
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
        signoff_statement_sha256=str(raw.get("signoff_statement_sha256") or "").strip() or None,
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_retention_signoff_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionSignoffView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_signoffs/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_signoff.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionSignoffView] = []
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
    "build_paper_execution_evidence_bundle_retention_signoff_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_signoff_views",
    "write_paper_execution_evidence_bundle_retention_signoff_artifact",
]
