"""Retention receipt for verified paper evidence-chain export handoffs.

The retention receipt is deliberately read-only. It does not copy files, submit
orders, promote strategies, or mutate the adjudication ledger. It records the
exact export-verification artifact and verified handoff entries an operator can
retain externally, together with retention names, file digests, and file sizes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRetentionReceiptArtifact,
    PaperExecutionEvidenceBundleRetentionReceiptEntry,
    PaperExecutionEvidenceBundleRetentionReceiptView,
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


def _safe_retention_name(*, tracking_id: str | None, kind: str, handoff_name: str | None, artifact_path: str | None) -> str:
    raw_handoff = (handoff_name or "").strip().replace("\\", "/")
    if raw_handoff and ".." not in raw_handoff.split("/"):
        return raw_handoff.lstrip("/")
    safe_tracking = (tracking_id or "untracked").replace("/", "_").replace("\\", "_")
    suffix = Path(artifact_path or f"{kind}.json").name or f"{kind}.json"
    return f"{safe_tracking}/{kind}/{suffix}"


def _entry_from_export_verification(
    entry_raw: dict[str, Any],
    *,
    tracking_id: str | None,
) -> PaperExecutionEvidenceBundleRetentionReceiptEntry:
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
    expected_file_sha = str(entry_raw.get("recomputed_file_sha256") or entry_raw.get("manifest_file_sha256") or "").strip() or None
    expected_size_raw = entry_raw.get("recomputed_size_bytes") if entry_raw.get("recomputed_size_bytes") is not None else entry_raw.get("manifest_size_bytes")
    expected_size = _int(expected_size_raw) if expected_size_raw is not None else None
    verified = bool(entry_raw.get("verification_digest_valid"))
    file_valid = bool(expected_file_sha and recomputed_file_sha == expected_file_sha)
    size_valid = bool(expected_size is not None and recomputed_size == expected_size)
    ready = present and verified and file_valid and size_valid
    return PaperExecutionEvidenceBundleRetentionReceiptEntry(
        kind=kind,
        artifact_path=str(path) if path is not None else None,
        handoff_name=str(entry_raw.get("handoff_name") or "").strip() or None,
        retention_name=_safe_retention_name(
            tracking_id=tracking_id,
            kind=kind,
            handoff_name=str(entry_raw.get("handoff_name") or "").strip() or None,
            artifact_path=str(path) if path is not None else artifact_value,
        ),
        declared_sha256=str(entry_raw.get("declared_sha256") or "").strip() or None,
        verified_sha256=str(entry_raw.get("recomputed_sha256") or entry_raw.get("manifest_computed_sha256") or "").strip() or None,
        file_sha256=recomputed_file_sha,
        expected_file_sha256=expected_file_sha,
        size_bytes=recomputed_size,
        expected_size_bytes=expected_size,
        present=present,
        source_verification_digest_valid=verified,
        file_digest_valid=file_valid,
        size_valid=size_valid,
        ready_for_retention=ready,
    )


def find_latest_paper_execution_evidence_bundle_export_verification_artifact(
    *,
    export_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper export-verification artifact."""

    if export_verification_artifact_path is not None:
        path = export_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_export_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_export_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_retention_receipt_artifact(
    *,
    export_verification_artifact_path: Path,
    export_verification_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRetentionReceiptArtifact:
    """Build a read-only retention receipt for a verified export handoff."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_export_verification_sha = str(export_verification_raw.get("artifact_sha256") or "").strip() or None
    computed_export_verification_sha = _embedded_digest(export_verification_raw)
    export_verification_hash_valid = _declared_matches_computed(declared_export_verification_sha, computed_export_verification_sha)
    if not export_verification_raw:
        blockers.append("EXPORT_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not export_verification_hash_valid:
        blockers.append("EXPORT_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    verification_status = str(export_verification_raw.get("verification_status") or "UNKNOWN")
    verification_trust = str(export_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if verification_status != "PASS":
        blockers.append("EXPORT_VERIFICATION_NOT_PASS")
    if verification_trust != "TRUSTED":
        warnings.append("EXPORT_VERIFICATION_TRUST_NOT_TRUSTED")

    tracking_id = str(export_verification_raw.get("tracking_id") or "").strip() or None
    entries_raw = export_verification_raw.get("entries") if isinstance(export_verification_raw.get("entries"), list) else []
    entries = [
        _entry_from_export_verification(entry, tracking_id=tracking_id)
        for entry in entries_raw
        if isinstance(entry, dict)
    ]
    if len(entries) != len(entries_raw):
        blockers.append("EXPORT_VERIFICATION_ENTRY_SHAPE_INVALID")
    if not entries:
        blockers.append("EXPORT_VERIFICATION_HAS_NO_RETAINABLE_ENTRIES")

    for entry in entries:
        if not entry.present:
            blockers.append(f"RETENTION_ENTRY_MISSING:{entry.kind}")
        if not entry.source_verification_digest_valid:
            blockers.append(f"RETENTION_ENTRY_SOURCE_NOT_VERIFIED:{entry.kind}")
        if not entry.file_digest_valid:
            blockers.append(f"RETENTION_ENTRY_FILE_DIGEST_MISMATCH:{entry.kind}")
        if not entry.size_valid:
            blockers.append(f"RETENTION_ENTRY_SIZE_MISMATCH:{entry.kind}")

    declared_entry_count = _int(export_verification_raw.get("recomputed_export_entry_count"))
    declared_valid_count = _int(export_verification_raw.get("recomputed_export_digest_valid_entry_count"))
    ready_count = sum(1 for entry in entries if entry.ready_for_retention)
    if declared_entry_count and declared_entry_count != len(entries):
        blockers.append("RETENTION_ENTRY_COUNT_MISMATCH")
    if declared_valid_count and declared_valid_count != ready_count:
        blockers.append("RETENTION_VALID_ENTRY_COUNT_MISMATCH")

    retention_index_sha256 = canonical_json_sha256([entry.model_dump(mode="json") for entry in entries])
    total_size = sum(int(entry.size_bytes or 0) for entry in entries)

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("READY_RESTRICTED" if warnings else "READY_FOR_RETENTION")
    trust = "TRUSTED" if status == "READY_FOR_RETENTION" else ("TRUST_RESTRICTED" if status == "READY_RESTRICTED" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleRetentionReceiptArtifact(
        generated_at_utc=now,
        tracking_id=tracking_id,
        retention_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_export_verification_artifact_path=str(export_verification_artifact_path),
        source_export_verification_artifact_sha256=declared_export_verification_sha,
        source_export_verification_computed_sha256=computed_export_verification_sha,
        source_export_verification_status=verification_status,
        source_export_verification_trust_banner=verification_trust,
        export_verification_artifact_hash_valid=export_verification_hash_valid,
        source_export_manifest_artifact_path=str(export_verification_raw.get("source_export_manifest_artifact_path") or "").strip() or None,
        source_export_manifest_sha256=str(export_verification_raw.get("source_export_manifest_declared_sha256") or "").strip() or None,
        source_export_manifest_status=str(export_verification_raw.get("source_export_manifest_status") or "").strip() or None,
        source_export_index_sha256=str(export_verification_raw.get("source_export_index_declared_sha256") or "").strip() or None,
        retained_entry_count=len(entries),
        retained_ready_entry_count=ready_count,
        total_size_bytes=total_size,
        retention_index_sha256=retention_index_sha256,
        entries=entries,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_retention_receipt_artifact(
    *,
    export_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRetentionReceiptArtifact]:
    """Write latest and history retention receipt artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_export_verification_artifact(
        export_verification_artifact_path=export_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (export_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_export_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_retention_receipt_artifact(
        export_verification_artifact_path=source_path,
        export_verification_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_retention_receipts"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_retention_receipt.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRetentionReceiptView:
    return PaperExecutionEvidenceBundleRetentionReceiptView(
        tracking_id=str(raw.get("tracking_id") or "").strip() or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "").strip() or None,
        retention_status=str(raw.get("retention_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_export_verification_artifact_path=str(raw.get("source_export_verification_artifact_path") or "").strip() or None,
        source_export_verification_artifact_sha256=str(raw.get("source_export_verification_artifact_sha256") or "").strip() or None,
        source_export_verification_status=str(raw.get("source_export_verification_status") or "").strip() or None,
        source_export_manifest_artifact_path=str(raw.get("source_export_manifest_artifact_path") or "").strip() or None,
        source_export_manifest_status=str(raw.get("source_export_manifest_status") or "").strip() or None,
        export_verification_artifact_hash_valid=bool(raw.get("export_verification_artifact_hash_valid")),
        retained_entry_count=_int(raw.get("retained_entry_count")),
        retained_ready_entry_count=_int(raw.get("retained_ready_entry_count")),
        total_size_bytes=_int(raw.get("total_size_bytes")),
        retention_index_sha256=str(raw.get("retention_index_sha256") or "").strip() or None,
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_retention_receipt_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRetentionReceiptView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_retention_receipts/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_retention_receipt.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRetentionReceiptView] = []
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
    "build_paper_execution_evidence_bundle_retention_receipt_artifact",
    "find_latest_paper_execution_evidence_bundle_export_verification_artifact",
    "read_paper_execution_evidence_bundle_retention_receipt_views",
    "write_paper_execution_evidence_bundle_retention_receipt_artifact",
]
