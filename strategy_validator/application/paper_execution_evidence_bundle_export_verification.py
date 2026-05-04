"""Verification for paper evidence-chain export handoff manifests.

The export verifier is deliberately read-only. It recomputes the export manifest
hash, the export index hash, and every retained artifact entry declared by the
manifest. It does not copy files, submit orders, call broker mutation endpoints,
promote strategies, or mutate the adjudication ledger.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleExportVerificationArtifact,
    PaperExecutionEvidenceBundleExportVerificationEntry,
    PaperExecutionEvidenceBundleExportVerificationView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


_DIGEST_KEYS_BY_KIND = {
    "closure_verification": "artifact_sha256",
    "closure": "artifact_sha256",
    "bundle": "bundle_sha256",
    "bundle_verification": "artifact_sha256",
    "bundle_drift": "artifact_sha256",
    "bundle_attestation": "artifact_sha256",
    "bundle_attestation_verification": "artifact_sha256",
}


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


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _embedded_digest(raw: dict[str, Any], *, digest_key: str) -> str:
    plain = dict(raw)
    plain.pop(digest_key, None)
    return canonical_json_sha256(plain)


def _declared_matches_computed(declared: str | None, computed: str | None) -> bool:
    declared = (declared or "").strip()
    computed = (computed or "").strip()
    if not declared or not computed:
        return False
    return declared == computed or computed.startswith(declared)


def _resolve_path(reference: str | None, *, manifest_path: Path) -> Path | None:
    if not reference:
        return None
    path = Path(reference)
    if path.is_absolute():
        return path
    candidate = (Path.cwd() / path).resolve()
    if candidate.exists():
        return candidate
    return (manifest_path.parent / path).resolve()


def _int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _entry_from_manifest(entry_raw: dict[str, Any], *, manifest_path: Path) -> PaperExecutionEvidenceBundleExportVerificationEntry:
    kind = str(entry_raw.get("kind") or "unknown")
    path = _resolve_path(str(entry_raw.get("artifact_path") or "") or None, manifest_path=manifest_path)
    present = bool(path is not None and path.exists())
    raw = _safe_read_json(path) if present and path is not None else None
    digest_key = _DIGEST_KEYS_BY_KIND.get(kind, "artifact_sha256")
    recomputed_sha = _embedded_digest(raw, digest_key=digest_key) if raw is not None and digest_key in raw else (canonical_json_sha256(raw) if raw is not None else None)
    file_digest = _file_sha256(path) if present and path is not None else None
    declared_sha = str(entry_raw.get("declared_sha256") or "").strip() or None
    manifest_computed_sha = str(entry_raw.get("computed_sha256") or "").strip() or None
    manifest_file_sha = str(entry_raw.get("file_sha256") or "").strip() or None
    manifest_size = entry_raw.get("size_bytes")
    size = None
    if present and path is not None:
        try:
            size = int(path.stat().st_size)
        except OSError:
            size = None
    declared_digest_valid = _declared_matches_computed(declared_sha, recomputed_sha)
    manifest_computed_digest_valid = _declared_matches_computed(manifest_computed_sha, recomputed_sha)
    file_digest_valid = _declared_matches_computed(manifest_file_sha, file_digest)
    size_valid = manifest_size is None or size == _int(manifest_size)
    manifest_entry_digest_valid = bool(entry_raw.get("digest_valid"))
    verification_digest_valid = bool(
        present
        and declared_digest_valid
        and manifest_computed_digest_valid
        and file_digest_valid
        and size_valid
        and manifest_entry_digest_valid
    )
    return PaperExecutionEvidenceBundleExportVerificationEntry(
        kind=kind,
        artifact_path=str(path) if path is not None else None,
        handoff_name=str(entry_raw.get("handoff_name") or "") or None,
        declared_sha256=declared_sha,
        manifest_computed_sha256=manifest_computed_sha,
        recomputed_sha256=recomputed_sha,
        manifest_file_sha256=manifest_file_sha,
        recomputed_file_sha256=file_digest,
        manifest_size_bytes=_int(manifest_size) if manifest_size is not None else None,
        recomputed_size_bytes=size,
        present=present,
        manifest_entry_digest_valid=manifest_entry_digest_valid,
        declared_digest_valid=declared_digest_valid,
        manifest_computed_digest_valid=manifest_computed_digest_valid,
        file_digest_valid=file_digest_valid,
        size_valid=size_valid,
        verification_digest_valid=verification_digest_valid,
    )


def find_latest_paper_execution_evidence_bundle_export_manifest_artifact(
    *,
    export_manifest_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper evidence-chain export manifest."""

    if export_manifest_artifact_path is not None:
        path = export_manifest_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_export_manifests/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_export_manifest.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_export_verification_artifact(
    *,
    export_manifest_artifact_path: Path,
    export_manifest_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleExportVerificationArtifact:
    """Build a read-only verifier artifact for a paper export handoff manifest."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    declared_manifest_sha = str(export_manifest_raw.get("artifact_sha256") or "").strip() or None
    computed_manifest_sha = _embedded_digest(export_manifest_raw, digest_key="artifact_sha256") if export_manifest_raw else None
    manifest_hash_valid = _declared_matches_computed(declared_manifest_sha, computed_manifest_sha)
    if not export_manifest_raw:
        blockers.append("EXPORT_MANIFEST_MISSING_OR_UNREADABLE")
    elif not manifest_hash_valid:
        blockers.append("EXPORT_MANIFEST_SHA256_MISMATCH")

    entries_raw = export_manifest_raw.get("entries") if isinstance(export_manifest_raw.get("entries"), list) else []
    recomputed_index_sha = canonical_json_sha256(entries_raw)
    declared_index_sha = str(export_manifest_raw.get("export_index_sha256") or "").strip() or None
    index_hash_valid = _declared_matches_computed(declared_index_sha, recomputed_index_sha)
    if not entries_raw:
        blockers.append("EXPORT_MANIFEST_HAS_NO_ENTRIES")
    if not index_hash_valid:
        blockers.append("EXPORT_INDEX_SHA256_MISMATCH")

    entries = [
        _entry_from_manifest(entry, manifest_path=export_manifest_artifact_path)
        for entry in entries_raw
        if isinstance(entry, dict)
    ]
    if len(entries) != len(entries_raw):
        blockers.append("EXPORT_MANIFEST_ENTRY_SHAPE_INVALID")

    for entry in entries:
        if not entry.present:
            blockers.append(f"EXPORT_VERIFICATION_ENTRY_MISSING:{entry.kind}")
        if not entry.declared_digest_valid:
            blockers.append(f"EXPORT_VERIFICATION_DECLARED_DIGEST_MISMATCH:{entry.kind}")
        if not entry.manifest_computed_digest_valid:
            blockers.append(f"EXPORT_VERIFICATION_COMPUTED_DIGEST_MISMATCH:{entry.kind}")
        if not entry.file_digest_valid:
            blockers.append(f"EXPORT_VERIFICATION_FILE_DIGEST_MISMATCH:{entry.kind}")
        if not entry.size_valid:
            blockers.append(f"EXPORT_VERIFICATION_SIZE_MISMATCH:{entry.kind}")
        if not entry.manifest_entry_digest_valid:
            blockers.append(f"EXPORT_VERIFICATION_SOURCE_ENTRY_NOT_DIGEST_VALID:{entry.kind}")

    manifest_entry_count = _int(export_manifest_raw.get("export_entry_count"))
    manifest_valid_count = _int(export_manifest_raw.get("export_digest_valid_entry_count"))
    recomputed_valid_count = sum(1 for entry in entries if entry.verification_digest_valid)
    if manifest_entry_count != len(entries):
        blockers.append("EXPORT_MANIFEST_ENTRY_COUNT_MISMATCH")
    if manifest_valid_count != recomputed_valid_count:
        blockers.append("EXPORT_MANIFEST_VALID_ENTRY_COUNT_MISMATCH")

    export_status = str(export_manifest_raw.get("export_status") or "UNKNOWN")
    export_trust = str(export_manifest_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if export_status == "BLOCKED":
        blockers.append("EXPORT_MANIFEST_STATUS_BLOCKED")
    elif export_status != "READY_FOR_EXPORT":
        warnings.append("EXPORT_MANIFEST_STATUS_NOT_READY_FOR_EXPORT")
    if export_trust != "TRUSTED":
        warnings.append("EXPORT_MANIFEST_TRUST_NOT_TRUSTED")

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "FAIL" if blockers else "PASS"
    trust = "TRUSTED" if status == "PASS" and not warnings else ("TRUST_RESTRICTED" if status == "PASS" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleExportVerificationArtifact(
        generated_at_utc=now,
        tracking_id=str(export_manifest_raw.get("tracking_id") or "") or None,
        verification_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_export_manifest_artifact_path=str(export_manifest_artifact_path),
        source_export_manifest_declared_sha256=declared_manifest_sha,
        source_export_manifest_computed_sha256=computed_manifest_sha,
        source_export_manifest_status=export_status,
        source_export_manifest_trust_banner=export_trust,
        export_manifest_hash_valid=manifest_hash_valid,
        source_export_index_declared_sha256=declared_index_sha,
        source_export_index_computed_sha256=recomputed_index_sha,
        export_index_hash_valid=index_hash_valid,
        source_export_entry_count=manifest_entry_count,
        source_export_digest_valid_entry_count=manifest_valid_count,
        recomputed_export_entry_count=len(entries),
        recomputed_export_digest_valid_entry_count=recomputed_valid_count,
        missing_entry_count=sum(1 for entry in entries if not entry.present),
        digest_mismatch_entry_count=sum(1 for entry in entries if entry.present and not entry.verification_digest_valid),
        entries=entries,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_export_verification_artifact(
    *,
    export_manifest_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleExportVerificationArtifact]:
    """Verify the latest or explicit export manifest and write latest + history artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_export_manifest_artifact(
        export_manifest_artifact_path=export_manifest_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (export_manifest_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_export_manifest.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_export_verification_artifact(
        export_manifest_artifact_path=source_path,
        export_manifest_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_export_verifications"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_export_verification.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleExportVerificationView:
    return PaperExecutionEvidenceBundleExportVerificationView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        verification_status=str(raw.get("verification_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_export_manifest_artifact_path=str(raw.get("source_export_manifest_artifact_path") or "") or None,
        source_export_manifest_declared_sha256=str(raw.get("source_export_manifest_declared_sha256") or "") or None,
        source_export_manifest_computed_sha256=str(raw.get("source_export_manifest_computed_sha256") or "") or None,
        source_export_manifest_status=str(raw.get("source_export_manifest_status") or "") or None,
        source_export_manifest_trust_banner=str(raw.get("source_export_manifest_trust_banner") or "") or None,
        export_manifest_hash_valid=bool(raw.get("export_manifest_hash_valid")),
        source_export_index_declared_sha256=str(raw.get("source_export_index_declared_sha256") or "") or None,
        source_export_index_computed_sha256=str(raw.get("source_export_index_computed_sha256") or "") or None,
        export_index_hash_valid=bool(raw.get("export_index_hash_valid")),
        source_export_entry_count=_int(raw.get("source_export_entry_count")),
        source_export_digest_valid_entry_count=_int(raw.get("source_export_digest_valid_entry_count")),
        recomputed_export_entry_count=_int(raw.get("recomputed_export_entry_count")),
        recomputed_export_digest_valid_entry_count=_int(raw.get("recomputed_export_digest_valid_entry_count")),
        missing_entry_count=_int(raw.get("missing_entry_count")),
        digest_mismatch_entry_count=_int(raw.get("digest_mismatch_entry_count")),
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_export_verification_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleExportVerificationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_export_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_export_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleExportVerificationView] = []
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
    "build_paper_execution_evidence_bundle_export_verification_artifact",
    "find_latest_paper_execution_evidence_bundle_export_manifest_artifact",
    "read_paper_execution_evidence_bundle_export_verification_views",
    "write_paper_execution_evidence_bundle_export_verification_artifact",
]
