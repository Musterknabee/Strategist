"""Read-only handoff capsule for verified paper evidence-chain retention.

This artifact closes the paper evidence retention chain for custody handoff. It
only references and hashes already-produced evidence; it never copies retained
files, submits orders, promotes strategies, or mutates the adjudication ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionHandoffArtifact,
    PaperExecutionEvidenceBundleRetentionHandoffView,
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


def find_latest_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
    *,
    retention_signoff_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper retention signoff verification artifact."""

    if retention_signoff_verification_artifact_path is not None:
        path = retention_signoff_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_signoff_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_signoff_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def _handoff_statement_digest(handoff_raw: dict[str, Any]) -> str | None:
    if not handoff_raw:
        return None
    statement = {
        "schema_version": "paper_execution_evidence_bundle_retention_handoff_statement/v1",
        "custodian_id": str(handoff_raw.get("custodian_id") or "operator").strip() or "operator",
        "handoff_note": str(handoff_raw.get("handoff_note") or "").strip() or None,
        "source_retention_signoff_verification_artifact_sha256": str(handoff_raw.get("source_retention_signoff_verification_declared_sha256") or "").strip() or None,
        "source_retention_signoff_verification_computed_sha256": str(handoff_raw.get("source_retention_signoff_verification_computed_sha256") or "").strip() or None,
        "source_retention_signoff_verification_status": str(handoff_raw.get("source_retention_signoff_verification_status") or "UNKNOWN"),
        "source_retention_signoff_verification_trust_banner": str(handoff_raw.get("source_retention_signoff_verification_trust_banner") or "TRUST_RESTRICTED"),
        "source_retention_signoff_artifact_path": str(handoff_raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        "source_retention_verification_artifact_path": str(handoff_raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        "source_retention_receipt_artifact_path": str(handoff_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(handoff_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": _int(handoff_raw.get("recomputed_retention_entry_count")),
        "recomputed_retention_ready_entry_count": _int(handoff_raw.get("recomputed_retention_ready_entry_count")),
        "checklist": _strings(handoff_raw.get("checklist")),
    }
    return canonical_json_sha256(statement)


def build_paper_execution_evidence_bundle_retention_handoff_artifact(
    *,
    retention_signoff_verification_artifact_path: Path,
    retention_signoff_verification_raw: dict[str, Any],
    custodian_id: str = "operator",
    handoff_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionHandoffArtifact:
    """Build a terminal read-only handoff capsule from a verified retention signoff."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_sha = str(retention_signoff_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_sha = _embedded_digest(retention_signoff_verification_raw)
    signoff_verification_hash_valid = _declared_matches_computed(declared_sha, computed_sha)
    if not retention_signoff_verification_raw:
        blockers.append("RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not signoff_verification_hash_valid:
        blockers.append("RETENTION_SIGNOFF_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    source_status = str(retention_signoff_verification_raw.get("verification_status") or "UNKNOWN")
    source_trust = str(retention_signoff_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if source_status != "PASS":
        blockers.append("RETENTION_SIGNOFF_VERIFICATION_NOT_PASS")
    if source_trust != "TRUSTED":
        warnings.append("RETENTION_SIGNOFF_VERIFICATION_TRUST_NOT_TRUSTED")

    if not bool(retention_signoff_verification_raw.get("retention_signoff_artifact_hash_valid")):
        blockers.append("RETENTION_SIGNOFF_ARTIFACT_HASH_NOT_VALID")
    if not bool(retention_signoff_verification_raw.get("signoff_statement_hash_valid")):
        blockers.append("RETENTION_SIGNOFF_STATEMENT_HASH_NOT_VALID")
    if not bool(retention_signoff_verification_raw.get("retention_verification_artifact_hash_valid")):
        blockers.append("RETENTION_VERIFICATION_ARTIFACT_HASH_NOT_VALID")

    entry_count = _int(retention_signoff_verification_raw.get("recomputed_retention_entry_count"))
    ready_count = _int(retention_signoff_verification_raw.get("recomputed_retention_ready_entry_count"))
    missing_count = _int(retention_signoff_verification_raw.get("missing_entry_count"))
    mismatch_count = _int(retention_signoff_verification_raw.get("digest_mismatch_entry_count"))
    if entry_count <= 0:
        blockers.append("RETENTION_HANDOFF_HAS_NO_ENTRIES")
    if entry_count != ready_count:
        blockers.append("RETENTION_HANDOFF_NOT_ALL_ENTRIES_READY")
    if missing_count:
        blockers.append("RETENTION_HANDOFF_HAS_MISSING_ENTRIES")
    if mismatch_count:
        blockers.append("RETENTION_HANDOFF_HAS_DIGEST_MISMATCHES")

    for item in _strings(retention_signoff_verification_raw.get("blockers")):
        blockers.append(f"SOURCE_RETENTION_SIGNOFF_VERIFICATION_BLOCKER:{item}")
    for item in _strings(retention_signoff_verification_raw.get("warnings")):
        warnings.append(f"SOURCE_RETENTION_SIGNOFF_VERIFICATION_WARNING:{item}")

    custodian = str(custodian_id or "operator").strip() or "operator"
    note = str(handoff_note or "").strip() or None
    checklist = [
        "retention signoff verification artifact hash valid",
        "retention signoff verification status PASS",
        "retention signoff artifact hash valid",
        "retention signoff statement hash valid",
        "retention verification artifact hash valid",
        "retained artifact files present",
        "retained artifact file digests match",
        "no paper/live order authority granted",
        "no files copied by handoff artifact",
    ]

    statement_source = {
        "custodian_id": custodian,
        "handoff_note": note,
        "source_retention_signoff_verification_declared_sha256": declared_sha,
        "source_retention_signoff_verification_computed_sha256": computed_sha,
        "source_retention_signoff_verification_status": source_status,
        "source_retention_signoff_verification_trust_banner": source_trust,
        "source_retention_signoff_artifact_path": str(retention_signoff_verification_raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        "source_retention_verification_artifact_path": str(retention_signoff_verification_raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        "source_retention_receipt_artifact_path": str(retention_signoff_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        "source_retention_index_sha256": str(retention_signoff_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        "recomputed_retention_entry_count": entry_count,
        "recomputed_retention_ready_entry_count": ready_count,
        "checklist": checklist,
    }
    statement_sha = _handoff_statement_digest(statement_source)

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("READY_RESTRICTED" if warnings else "READY_FOR_HANDOFF")
    trust = "TRUSTED" if status == "READY_FOR_HANDOFF" else ("TRUST_RESTRICTED" if status == "READY_RESTRICTED" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionHandoffArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_signoff_verification_raw.get("tracking_id") or "").strip() or None,
        handoff_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        custodian_id=custodian,
        handoff_note=note,
        source_retention_signoff_verification_artifact_path=str(retention_signoff_verification_artifact_path),
        source_retention_signoff_verification_declared_sha256=declared_sha,
        source_retention_signoff_verification_computed_sha256=computed_sha,
        source_retention_signoff_verification_status=source_status,
        source_retention_signoff_verification_trust_banner=source_trust,
        retention_signoff_verification_artifact_hash_valid=signoff_verification_hash_valid,
        source_retention_signoff_artifact_path=str(retention_signoff_verification_raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        source_retention_signoff_status=str(retention_signoff_verification_raw.get("source_retention_signoff_status") or "").strip() or None,
        source_retention_signoff_trust_banner=str(retention_signoff_verification_raw.get("source_retention_signoff_trust_banner") or "").strip() or None,
        retention_signoff_artifact_hash_valid=bool(retention_signoff_verification_raw.get("retention_signoff_artifact_hash_valid")),
        signoff_statement_hash_valid=bool(retention_signoff_verification_raw.get("signoff_statement_hash_valid")),
        source_retention_verification_artifact_path=str(retention_signoff_verification_raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        source_retention_verification_status=str(retention_signoff_verification_raw.get("source_retention_verification_status") or "").strip() or None,
        retention_verification_artifact_hash_valid=bool(retention_signoff_verification_raw.get("retention_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(retention_signoff_verification_raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(retention_signoff_verification_raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(retention_signoff_verification_raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=entry_count,
        recomputed_retention_ready_entry_count=ready_count,
        missing_entry_count=missing_count,
        digest_mismatch_entry_count=mismatch_count,
        handoff_statement_sha256=statement_sha,
        checklist=checklist,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_handoff_artifact(
    *,
    retention_signoff_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    custodian_id: str = "operator",
    handoff_note: str | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionHandoffArtifact]:
    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
        retention_signoff_verification_artifact_path=retention_signoff_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_signoff_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_signoff_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_handoff_artifact(
        retention_signoff_verification_artifact_path=source_path,
        retention_signoff_verification_raw=raw,
        custodian_id=custodian_id,
        handoff_note=handoff_note,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_handoffs"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_handoff.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionHandoffView:
    blockers = _strings(raw.get("blockers"))
    warnings = _strings(raw.get("warnings"))
    return PaperExecutionEvidenceBundleRetentionHandoffView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        handoff_status=str(raw.get("handoff_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        custodian_id=str(raw.get("custodian_id") or "").strip() or None,
        handoff_note=str(raw.get("handoff_note") or "").strip() or None,
        source_retention_signoff_verification_artifact_path=str(raw.get("source_retention_signoff_verification_artifact_path") or "").strip() or None,
        source_retention_signoff_verification_declared_sha256=str(raw.get("source_retention_signoff_verification_declared_sha256") or "").strip() or None,
        source_retention_signoff_verification_status=str(raw.get("source_retention_signoff_verification_status") or "").strip() or None,
        source_retention_signoff_verification_trust_banner=str(raw.get("source_retention_signoff_verification_trust_banner") or "").strip() or None,
        retention_signoff_verification_artifact_hash_valid=bool(raw.get("retention_signoff_verification_artifact_hash_valid")),
        source_retention_signoff_artifact_path=str(raw.get("source_retention_signoff_artifact_path") or "").strip() or None,
        source_retention_signoff_status=str(raw.get("source_retention_signoff_status") or "").strip() or None,
        source_retention_signoff_trust_banner=str(raw.get("source_retention_signoff_trust_banner") or "").strip() or None,
        retention_signoff_artifact_hash_valid=bool(raw.get("retention_signoff_artifact_hash_valid")),
        signoff_statement_hash_valid=bool(raw.get("signoff_statement_hash_valid")),
        source_retention_verification_artifact_path=str(raw.get("source_retention_verification_artifact_path") or "").strip() or None,
        source_retention_verification_status=str(raw.get("source_retention_verification_status") or "").strip() or None,
        retention_verification_artifact_hash_valid=bool(raw.get("retention_verification_artifact_hash_valid")),
        source_retention_receipt_artifact_path=str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_status=str(raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_index_sha256=str(raw.get("source_retention_index_sha256") or "").strip() or None,
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        handoff_statement_sha256=str(raw.get("handoff_statement_sha256") or "").strip() or None,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
    )


def read_paper_execution_evidence_bundle_retention_handoff_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionHandoffView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_handoffs/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_handoff.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionHandoffView] = []
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
    "build_paper_execution_evidence_bundle_retention_handoff_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_signoff_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_handoff_views",
    "write_paper_execution_evidence_bundle_retention_handoff_artifact",
]
