"""Verification for paper evidence-chain retention receipts.

The retention verifier is deliberately read-only. It does not copy retained
artifacts, submit orders, promote strategies, or mutate the adjudication ledger.
It re-reads a retention receipt, recomputes its embedded digest and retention
index, and checks every retained artifact's current file digest/size against the
receipt.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionVerificationArtifact,
    PaperExecutionEvidenceBundleRetentionVerificationEntry,
    PaperExecutionEvidenceBundleRetentionVerificationView,
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


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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


def _entry_from_receipt(entry_raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionVerificationEntry:
    kind = str(entry_raw.get("kind") or "unknown")
    artifact_value = str(entry_raw.get("artifact_path") or "").strip() or None
    path = Path(artifact_value).expanduser().resolve() if artifact_value else None
    present = bool(path is not None and path.exists())
    recomputed_file_sha = _file_sha256(path) if present and path is not None else None
    recomputed_size: int | None = None
    if present and path is not None:
        try:
            recomputed_size = int(path.stat().st_size)
        except OSError:
            recomputed_size = None

    receipt_file_sha = str(entry_raw.get("file_sha256") or "").strip() or None
    receipt_expected_file_sha = str(entry_raw.get("expected_file_sha256") or "").strip() or None
    receipt_size = _int(entry_raw.get("size_bytes")) if entry_raw.get("size_bytes") is not None else None
    receipt_expected_size = _int(entry_raw.get("expected_size_bytes")) if entry_raw.get("expected_size_bytes") is not None else None
    retention_entry_ready = bool(entry_raw.get("ready_for_retention"))
    source_verification_digest_valid = bool(entry_raw.get("source_verification_digest_valid"))
    file_digest_valid = bool(
        recomputed_file_sha
        and receipt_file_sha
        and receipt_expected_file_sha
        and recomputed_file_sha == receipt_file_sha == receipt_expected_file_sha
    )
    size_valid = bool(
        recomputed_size is not None
        and receipt_size is not None
        and receipt_expected_size is not None
        and recomputed_size == receipt_size == receipt_expected_size
    )
    verification_digest_valid = present and retention_entry_ready and source_verification_digest_valid and file_digest_valid and size_valid
    return PaperExecutionEvidenceBundleRetentionVerificationEntry(
        kind=kind,
        artifact_path=str(path) if path is not None else None,
        retention_name=str(entry_raw.get("retention_name") or "").strip() or None,
        receipt_declared_sha256=str(entry_raw.get("declared_sha256") or "").strip() or None,
        receipt_verified_sha256=str(entry_raw.get("verified_sha256") or "").strip() or None,
        receipt_file_sha256=receipt_file_sha,
        receipt_expected_file_sha256=receipt_expected_file_sha,
        recomputed_file_sha256=recomputed_file_sha,
        receipt_size_bytes=receipt_size,
        receipt_expected_size_bytes=receipt_expected_size,
        recomputed_size_bytes=recomputed_size,
        present=present,
        retention_entry_ready=retention_entry_ready,
        source_verification_digest_valid=source_verification_digest_valid,
        file_digest_valid=file_digest_valid,
        size_valid=size_valid,
        verification_digest_valid=verification_digest_valid,
    )


def find_latest_paper_execution_evidence_bundle_retention_receipt_artifact(
    *,
    retention_receipt_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper retention receipt artifact."""

    if retention_receipt_artifact_path is not None:
        path = retention_receipt_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_retention_receipts/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_receipt.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_verification_artifact(
    *,
    retention_receipt_artifact_path: Path,
    retention_receipt_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionVerificationArtifact:
    """Build a read-only verification artifact for a retention receipt."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_receipt_sha = str(retention_receipt_raw.get("artifact_sha256") or "").strip() or None
    computed_receipt_sha = _embedded_digest(retention_receipt_raw)
    receipt_hash_valid = _declared_matches_computed(declared_receipt_sha, computed_receipt_sha)
    if not retention_receipt_raw:
        blockers.append("RETENTION_RECEIPT_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not receipt_hash_valid:
        blockers.append("RETENTION_RECEIPT_ARTIFACT_SHA256_MISMATCH")

    entries_raw = retention_receipt_raw.get("entries") if isinstance(retention_receipt_raw.get("entries"), list) else []
    recomputed_index_sha = canonical_json_sha256(entries_raw)
    declared_index_sha = str(retention_receipt_raw.get("retention_index_sha256") or "").strip() or None
    index_hash_valid = _declared_matches_computed(declared_index_sha, recomputed_index_sha)
    if not entries_raw:
        blockers.append("RETENTION_RECEIPT_HAS_NO_ENTRIES")
    if not index_hash_valid:
        blockers.append("RETENTION_INDEX_SHA256_MISMATCH")

    entries = [_entry_from_receipt(entry) for entry in entries_raw if isinstance(entry, dict)]
    if len(entries) != len(entries_raw):
        blockers.append("RETENTION_RECEIPT_ENTRY_SHAPE_INVALID")

    for entry in entries:
        if not entry.present:
            blockers.append(f"RETENTION_VERIFICATION_ENTRY_MISSING:{entry.kind}")
        if not entry.retention_entry_ready:
            blockers.append(f"RETENTION_VERIFICATION_ENTRY_NOT_READY:{entry.kind}")
        if not entry.source_verification_digest_valid:
            blockers.append(f"RETENTION_VERIFICATION_SOURCE_NOT_VERIFIED:{entry.kind}")
        if not entry.file_digest_valid:
            blockers.append(f"RETENTION_VERIFICATION_FILE_DIGEST_MISMATCH:{entry.kind}")
        if not entry.size_valid:
            blockers.append(f"RETENTION_VERIFICATION_SIZE_MISMATCH:{entry.kind}")

    source_entry_count = _int(retention_receipt_raw.get("retained_entry_count"))
    source_ready_count = _int(retention_receipt_raw.get("retained_ready_entry_count"))
    recomputed_ready_count = sum(1 for entry in entries if entry.verification_digest_valid)
    if source_entry_count != len(entries):
        blockers.append("RETENTION_RECEIPT_ENTRY_COUNT_MISMATCH")
    if source_ready_count != recomputed_ready_count:
        blockers.append("RETENTION_RECEIPT_READY_ENTRY_COUNT_MISMATCH")

    retention_status = str(retention_receipt_raw.get("retention_status") or "UNKNOWN")
    retention_trust = str(retention_receipt_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if retention_status == "BLOCKED":
        blockers.append("RETENTION_RECEIPT_STATUS_BLOCKED")
    elif retention_status != "READY_FOR_RETENTION":
        warnings.append("RETENTION_RECEIPT_STATUS_NOT_READY_FOR_RETENTION")
    if retention_trust != "TRUSTED":
        warnings.append("RETENTION_RECEIPT_TRUST_NOT_TRUSTED")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(retention_receipt_raw.get("tracking_id") or "").strip() or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_retention_receipt_artifact_path=str(retention_receipt_artifact_path),
        source_retention_receipt_declared_sha256=declared_receipt_sha,
        source_retention_receipt_computed_sha256=computed_receipt_sha,
        source_retention_receipt_status=retention_status,
        source_retention_receipt_trust_banner=retention_trust,
        retention_receipt_hash_valid=receipt_hash_valid,
        source_retention_index_declared_sha256=declared_index_sha,
        source_retention_index_computed_sha256=recomputed_index_sha,
        retention_index_hash_valid=index_hash_valid,
        source_retention_entry_count=source_entry_count,
        source_retention_ready_entry_count=source_ready_count,
        recomputed_retention_entry_count=len(entries),
        recomputed_retention_ready_entry_count=recomputed_ready_count,
        missing_entry_count=sum(1 for entry in entries if not entry.present),
        digest_mismatch_entry_count=sum(1 for entry in entries if entry.present and not entry.verification_digest_valid),
        entries=entries,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_verification_artifact(
    *,
    retention_receipt_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionVerificationArtifact]:
    """Verify the latest or explicit retention receipt and write latest + history artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_retention_receipt_artifact(
        retention_receipt_artifact_path=retention_receipt_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (retention_receipt_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_retention_receipt.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_verification_artifact(
        retention_receipt_artifact_path=source_path,
        retention_receipt_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionVerificationView:
    return PaperExecutionEvidenceBundleRetentionVerificationView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_retention_receipt_artifact_path=str(raw.get("source_retention_receipt_artifact_path") or "").strip() or None,
        source_retention_receipt_declared_sha256=str(raw.get("source_retention_receipt_declared_sha256") or "").strip() or None,
        source_retention_receipt_computed_sha256=str(raw.get("source_retention_receipt_computed_sha256") or "").strip() or None,
        source_retention_receipt_status=str(raw.get("source_retention_receipt_status") or "").strip() or None,
        source_retention_receipt_trust_banner=str(raw.get("source_retention_receipt_trust_banner") or "").strip() or None,
        retention_receipt_hash_valid=bool(raw.get("retention_receipt_hash_valid")),
        source_retention_index_declared_sha256=str(raw.get("source_retention_index_declared_sha256") or "").strip() or None,
        source_retention_index_computed_sha256=str(raw.get("source_retention_index_computed_sha256") or "").strip() or None,
        retention_index_hash_valid=bool(raw.get("retention_index_hash_valid")),
        source_retention_entry_count=_int(raw.get("source_retention_entry_count")),
        source_retention_ready_entry_count=_int(raw.get("source_retention_ready_entry_count")),
        recomputed_retention_entry_count=_int(raw.get("recomputed_retention_entry_count")),
        recomputed_retention_ready_entry_count=_int(raw.get("recomputed_retention_ready_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_retention_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionVerificationView] = []
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
    "build_paper_execution_evidence_bundle_retention_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_retention_receipt_artifact",
    "read_paper_execution_evidence_bundle_retention_verification_views",
    "write_paper_execution_evidence_bundle_retention_verification_artifact",
]
