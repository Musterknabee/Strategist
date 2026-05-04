"""Export handoff manifest for verified paper evidence-bundle chains.

The export manifest is deliberately read-only. It does not copy files, submit
orders, promote strategies, or mutate the adjudication ledger. It produces a
stable operator handoff index of the closure-verification artifact and every
referenced paper evidence-chain artifact so external retention can preserve the
same digest accountability.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.application.paper_execution_evidence_bundle_closure_verification import (
    find_latest_paper_execution_evidence_bundle_closure_artifact as _find_latest_closure_artifact,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleExportEntry,
    PaperExecutionEvidenceBundleExportManifestArtifact,
    PaperExecutionEvidenceBundleExportManifestView,
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

_EXPECTED_KINDS = [
    "closure_verification",
    "closure",
    "bundle",
    "bundle_verification",
    "bundle_drift",
    "bundle_attestation",
    "bundle_attestation_verification",
]


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


def _resolve_path(reference: str | None, *, base_path: Path) -> Path | None:
    if not reference:
        return None
    path = Path(reference)
    if path.is_absolute():
        return path
    candidate = (Path.cwd() / path).resolve()
    if candidate.exists():
        return candidate
    return (base_path.parent / path).resolve()


def _tracking_id_from(raw: dict[str, Any] | None) -> str | None:
    if not raw:
        return None
    value = str(raw.get("tracking_id") or "").strip()
    return value or None


def _handoff_name(*, tracking_id: str | None, kind: str, path: Path | None) -> str:
    suffix = path.name if path is not None and path.name else f"{kind}.json"
    safe_tracking = (tracking_id or "untracked").replace("/", "_").replace("\\", "_")
    return f"{safe_tracking}/{kind}/{suffix}"


def _entry(
    *,
    kind: str,
    path_value: str | None,
    declared_sha256: str | None,
    base_path: Path,
    tracking_id: str | None,
) -> PaperExecutionEvidenceBundleExportEntry:
    path = _resolve_path(path_value, base_path=base_path)
    present = bool(path is not None and path.exists())
    raw = _safe_read_json(path) if present and path is not None else None
    digest_key = _DIGEST_KEYS_BY_KIND.get(kind, "artifact_sha256")
    computed = _embedded_digest(raw, digest_key=digest_key) if raw is not None and digest_key in raw else (canonical_json_sha256(raw) if raw is not None else None)
    file_digest = _file_sha256(path) if present and path is not None else None
    size = None
    if present and path is not None:
        try:
            size = int(path.stat().st_size)
        except OSError:
            size = None
    return PaperExecutionEvidenceBundleExportEntry(
        kind=kind,
        artifact_path=str(path) if path is not None else None,
        handoff_name=_handoff_name(tracking_id=tracking_id, kind=kind, path=path),
        declared_sha256=(declared_sha256 or "").strip() or None,
        computed_sha256=computed,
        file_sha256=file_digest,
        size_bytes=size,
        present=present,
        digest_valid=_declared_matches_computed(declared_sha256, computed),
    )


def find_latest_paper_execution_evidence_bundle_closure_verification_artifact(
    *,
    closure_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Find and read the latest paper closure-verification artifact."""

    if closure_verification_artifact_path is not None:
        path = closure_verification_artifact_path.expanduser().resolve()
        return path, _safe_read_json(path)
    root = _paper_broker_root(output_root=output_root)
    candidates = list(root.glob("*/evidence_bundle_closure_verifications/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_closure_verification.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    if not candidates:
        return None, None
    path = sorted(candidates, key=_mtime, reverse=True)[0]
    return path, _safe_read_json(path)


def build_paper_execution_evidence_bundle_export_manifest_artifact(
    *,
    closure_verification_artifact_path: Path,
    closure_verification_raw: dict[str, Any],
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleExportManifestArtifact:
    """Build a read-only export handoff manifest for a verified paper chain."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []

    tracking_id = _tracking_id_from(closure_verification_raw)
    closure_verification_declared = str(closure_verification_raw.get("artifact_sha256") or "").strip() or None
    closure_verification_computed = _embedded_digest(closure_verification_raw, digest_key="artifact_sha256") if closure_verification_raw else None
    closure_verification_hash_valid = _declared_matches_computed(closure_verification_declared, closure_verification_computed)

    if not closure_verification_raw:
        blockers.append("CLOSURE_VERIFICATION_ARTIFACT_MISSING_OR_UNREADABLE")
    elif not closure_verification_hash_valid:
        blockers.append("CLOSURE_VERIFICATION_ARTIFACT_SHA256_MISMATCH")

    verification_status = str(closure_verification_raw.get("verification_status") or "UNKNOWN")
    verification_trust = str(closure_verification_raw.get("trust_banner") or "TRUST_RESTRICTED")
    if verification_status != "PASS":
        blockers.append("CLOSURE_VERIFICATION_NOT_PASS")
    if verification_trust != "TRUSTED":
        warnings.append("CLOSURE_VERIFICATION_TRUST_NOT_TRUSTED")

    closure_path_value = str(closure_verification_raw.get("source_closure_artifact_path") or "") or None
    closure_path = _resolve_path(closure_path_value, base_path=closure_verification_artifact_path)
    closure_raw = _safe_read_json(closure_path) if closure_path is not None and closure_path.exists() else None
    if closure_raw is None:
        blockers.append("SOURCE_CLOSURE_ARTIFACT_MISSING_OR_UNREADABLE")
    closure_status = str((closure_raw or {}).get("closure_status") or closure_verification_raw.get("source_closure_status") or "UNKNOWN")
    if closure_status != "READY_FOR_OPERATOR_REVIEW":
        warnings.append("SOURCE_CLOSURE_NOT_READY_FOR_OPERATOR_REVIEW")

    entries = [
        _entry(
            kind="closure_verification",
            path_value=str(closure_verification_artifact_path),
            declared_sha256=closure_verification_declared,
            base_path=closure_verification_artifact_path,
            tracking_id=tracking_id,
        ),
        _entry(
            kind="closure",
            path_value=closure_path_value,
            declared_sha256=str(closure_verification_raw.get("source_closure_declared_sha256") or "") or None,
            base_path=closure_verification_artifact_path,
            tracking_id=tracking_id,
        ),
    ]

    if closure_raw is None:
        for kind in _EXPECTED_KINDS[2:]:
            entries.append(_entry(kind=kind, path_value=None, declared_sha256=None, base_path=closure_verification_artifact_path, tracking_id=tracking_id))
    else:
        entries.extend(
            [
                _entry(
                    kind="bundle",
                    path_value=str(closure_raw.get("source_bundle_artifact_path") or "") or None,
                    declared_sha256=str(closure_raw.get("source_bundle_sha256") or "") or None,
                    base_path=closure_path or closure_verification_artifact_path,
                    tracking_id=tracking_id,
                ),
                _entry(
                    kind="bundle_verification",
                    path_value=str(closure_raw.get("source_verification_artifact_path") or "") or None,
                    declared_sha256=str(closure_raw.get("source_verification_artifact_sha256") or "") or None,
                    base_path=closure_path or closure_verification_artifact_path,
                    tracking_id=tracking_id,
                ),
                _entry(
                    kind="bundle_drift",
                    path_value=str(closure_raw.get("source_drift_artifact_path") or "") or None,
                    declared_sha256=str(closure_raw.get("source_drift_artifact_sha256") or "") or None,
                    base_path=closure_path or closure_verification_artifact_path,
                    tracking_id=tracking_id,
                ),
                _entry(
                    kind="bundle_attestation",
                    path_value=str(closure_raw.get("source_attestation_artifact_path") or "") or None,
                    declared_sha256=str(closure_raw.get("source_attestation_artifact_sha256") or "") or None,
                    base_path=closure_path or closure_verification_artifact_path,
                    tracking_id=tracking_id,
                ),
                _entry(
                    kind="bundle_attestation_verification",
                    path_value=str(closure_raw.get("source_attestation_verification_artifact_path") or "") or None,
                    declared_sha256=str(closure_raw.get("source_attestation_verification_artifact_sha256") or "") or None,
                    base_path=closure_path or closure_verification_artifact_path,
                    tracking_id=tracking_id,
                ),
            ]
        )

    for entry in entries:
        if not entry.present:
            blockers.append(f"EXPORT_ENTRY_MISSING:{entry.kind}")
        elif not entry.digest_valid:
            blockers.append(f"EXPORT_ENTRY_DIGEST_MISMATCH:{entry.kind}")

    valid_count = sum(1 for entry in entries if entry.digest_valid)
    total_size = sum(int(entry.size_bytes or 0) for entry in entries)
    export_index_sha256 = canonical_json_sha256([entry.model_dump(mode="json") for entry in entries])

    blockers = sorted(set(blockers))
    warnings = sorted(set(warnings))
    status = "BLOCKED" if blockers else ("READY_RESTRICTED" if warnings else "READY_FOR_EXPORT")
    trust = "TRUSTED" if status == "READY_FOR_EXPORT" else ("TRUST_RESTRICTED" if status == "READY_RESTRICTED" else "UNTRUSTED")

    artifact = PaperExecutionEvidenceBundleExportManifestArtifact(
        generated_at_utc=now,
        tracking_id=tracking_id,
        export_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_closure_verification_artifact_path=str(closure_verification_artifact_path),
        source_closure_verification_artifact_sha256=closure_verification_declared,
        source_closure_verification_status=verification_status,
        source_closure_verification_trust_banner=verification_trust,
        closure_verification_artifact_hash_valid=closure_verification_hash_valid,
        source_closure_status=closure_status,
        export_entry_count=len(entries),
        export_digest_valid_entry_count=valid_count,
        total_size_bytes=total_size,
        export_index_sha256=export_index_sha256,
        entries=entries,
        blockers=blockers,
        warnings=warnings,
    )
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(artifact.model_dump(mode="json", exclude={"artifact_sha256"}))})


def write_paper_execution_evidence_bundle_export_manifest_artifact(
    *,
    closure_verification_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleExportManifestArtifact]:
    """Write the latest and historical export handoff manifest artifact."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_closure_verification_artifact(
        closure_verification_artifact_path=closure_verification_artifact_path,
        output_root=output_root,
    )
    if source_path is None or raw is None:
        source_path = (closure_verification_artifact_path or (_paper_broker_root(output_root=output_root) / "untracked" / "paper_execution_evidence_bundle_closure_verification.json")).expanduser().resolve()
        raw = {}
    artifact = build_paper_execution_evidence_bundle_export_manifest_artifact(
        closure_verification_artifact_path=source_path,
        closure_verification_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_export_manifests"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_export_manifest.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleExportManifestView:
    entries = raw.get("entries") if isinstance(raw.get("entries"), list) else []
    return PaperExecutionEvidenceBundleExportManifestView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) or None,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        export_status=str(raw.get("export_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_closure_verification_artifact_path=str(raw.get("source_closure_verification_artifact_path") or "") or None,
        source_closure_verification_artifact_sha256=str(raw.get("source_closure_verification_artifact_sha256") or "") or None,
        source_closure_verification_status=str(raw.get("source_closure_verification_status") or "") or None,
        source_closure_status=str(raw.get("source_closure_status") or "") or None,
        closure_verification_artifact_hash_valid=bool(raw.get("closure_verification_artifact_hash_valid")),
        export_entry_count=int(raw.get("export_entry_count") or len(entries)),
        export_digest_valid_entry_count=int(raw.get("export_digest_valid_entry_count") or 0),
        total_size_bytes=int(raw.get("total_size_bytes") or 0),
        export_index_sha256=str(raw.get("export_index_sha256") or "") or None,
        blocker_count=len(raw.get("blockers", [])) if isinstance(raw.get("blockers"), list) else 0,
        warning_count=len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_export_manifest_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleExportManifestView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_export_manifests/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_export_manifest.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleExportManifestView] = []
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
    "build_paper_execution_evidence_bundle_export_manifest_artifact",
    "find_latest_paper_execution_evidence_bundle_closure_verification_artifact",
    "read_paper_execution_evidence_bundle_export_manifest_views",
    "write_paper_execution_evidence_bundle_export_manifest_artifact",
]
