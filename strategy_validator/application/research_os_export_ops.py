"""Research OS portable evidence export bundle builder.

This module is deliberately offline and read-only. It copies existing evidence artifacts
into a portable bundle, records SHA-256 digests, optionally creates a tar.gz archive,
and exposes a safe read-plane payload. It performs no network access, broker orders,
ledger mutation, deployment approval, or profitability certification.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import (
    artifact_root_directory,
    paper_broker_status_artifact_path,
    provider_historical_snapshot_run_path,
    provider_paper_loop_manifest_path,
    research_os_runtime_manifest_path,
)
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_export import (
    ResearchOsExportFileRef,
    ResearchOsExportFormat,
    ResearchOsExportManifest,
    ResearchOsExportStatus,
    ResearchOsExportVerificationResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_research_os_export/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_export_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_exports").resolve()


def research_os_export_latest_manifest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_export_root(repo_root, artifact_root) / "latest" / "research_os_export_manifest.json").resolve()


def research_os_export_latest_verification_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_export_root(repo_root, artifact_root) / "latest" / "research_os_export_verification.json").resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _strategy_batch_latest_summary(root: Path) -> Path:
    base = root / "strategy_batches"
    if not base.is_dir():
        return base / "latest" / "batch_summary.json"
    candidates = [p for p in base.rglob("batch_summary.json") if p.is_file()]
    if not candidates:
        return base / "latest" / "batch_summary.json"
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def _market_data_integrity_latest(root: Path) -> Path:
    candidates = [p for p in root.rglob("market_data_integrity_result.json") if p.is_file()]
    if not candidates:
        return root / "market_data_integrity" / "latest" / "market_data_integrity_result.json"
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def _export_sources(root: Path) -> list[tuple[str, Path, bool]]:
    return [
        ("research_os_briefing_pack", root / "research_os_briefings" / "latest" / "research_os_briefing_pack.json", True),
        ("research_os_closure_manifest", root / "research_os_closure" / "latest" / "research_os_closure_manifest.json", True),
        ("research_os_closure_verification", root / "research_os_attestation" / "latest" / "closure_verification_result.json", True),
        ("research_os_operator_attestation", root / "research_os_attestation" / "latest" / "operator_attestation.json", True),
        ("provider_paper_loop_manifest", root / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json", False),
        ("provider_historical_snapshot_run", root / "provider_historical_snapshots" / "latest" / "provider_historical_snapshot_run.json", False),
        ("paper_broker_status", root / "paper_broker" / "latest" / "paper_broker_status.json", False),
        ("strategy_batch_summary", _strategy_batch_latest_summary(root), False),
        ("market_data_integrity_result", _market_data_integrity_latest(root), False),
        ("strategy_memory_index", root / "strategy_memory" / "latest" / "memory_index.json", False),
        ("strategy_thesis_evaluation", root / "strategy_theses" / "latest" / "thesis_evaluation.json", False),
        ("shadow_book_manifest", root / "shadow_books" / "latest" / "shadow_book_manifest.json", False),
        ("shadow_book_risk_summary", root / "shadow_books" / "latest" / "latest_risk_summary.json", False),
        ("research_os_runtime_manifest", root / "research_os_runtime" / "latest" / "runtime_demo_manifest.json", False),
    ]


def _secret_warnings(path: Path) -> list[str]:
    try:
        body = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits = [marker for marker in _SECRET_MARKERS if marker in body]
    return [f"SECRET_MARKER_PRESENT:{marker}" for marker in hits]


def _file_ref(label: str, source: Path, bundle_dir: Path, root: Path, *, required: bool) -> ResearchOsExportFileRef:
    warnings: list[str] = []
    blockers: list[str] = []
    bundle_path: str | None = None
    present = source.is_file()
    readable = False
    size_bytes: int | None = None
    digest: str | None = None
    if not present:
        warnings.append("ARTIFACT_NOT_PRESENT")
        if required:
            blockers.append("REQUIRED_ARTIFACT_NOT_PRESENT")
    else:
        try:
            rel = Path("evidence") / _safe_rel(source, root)
            dest = (bundle_dir / rel).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            digest = _sha256_file(dest)
            size_bytes = dest.stat().st_size
            readable = True
            bundle_path = rel.as_posix()
            secret_hits = _secret_warnings(dest)
            warnings.extend(secret_hits)
            if secret_hits:
                blockers.append("SECRET_MARKER_PRESENT")
        except OSError as exc:
            blockers.append(f"ARTIFACT_COPY_FAILED:{type(exc).__name__}")
    return ResearchOsExportFileRef(
        label=label,
        source_path=str(source),
        bundle_path=bundle_path,
        required=required,
        present=present,
        readable=readable,
        size_bytes=size_bytes,
        file_sha256=digest,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )


def _status(files: list[ResearchOsExportFileRef]) -> tuple[ResearchOsExportStatus, ResearchOsTrustBanner, list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    for f in files:
        warnings.extend(f"{f.label}:{w}" for w in f.warnings)
        blockers.extend(f"{f.label}:{b}" for b in f.blockers)
    present = [f for f in files if f.present and f.readable]
    missing_required = [f.label for f in files if f.required and not f.present]
    if not present:
        return ResearchOsExportStatus.EMPTY, ResearchOsTrustBanner.UNTRUSTED, sorted(set(warnings)), sorted(set(blockers + ["NO_EXPORTABLE_ARTIFACTS"]))
    if missing_required or any("SECRET_MARKER_PRESENT" in b for b in blockers):
        return ResearchOsExportStatus.BLOCKED, ResearchOsTrustBanner.UNTRUSTED, sorted(set(warnings)), sorted(set(blockers))
    if warnings or any(not f.present for f in files):
        return ResearchOsExportStatus.RESTRICTED, ResearchOsTrustBanner.TRUST_RESTRICTED, sorted(set(warnings)), sorted(set(blockers))
    return ResearchOsExportStatus.READY, ResearchOsTrustBanner.TRUSTED, [], []


def _spine_sha(files: list[ResearchOsExportFileRef]) -> str:
    rows = [
        {
            "label": f.label,
            "bundle_path": f.bundle_path,
            "file_sha256": f.file_sha256,
            "present": f.present,
            "required": f.required,
        }
        for f in sorted(files, key=lambda x: x.label)
    ]
    return canonical_json_sha256(rows)


def _manifest_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone["manifest_sha256"] = ""
    clone["archive_sha256"] = clone.get("archive_sha256") or None
    return canonical_json_sha256(clone)


def _make_tar(bundle_dir: Path, archive_path: Path) -> str:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(bundle_dir, arcname=bundle_dir.name)
    return _sha256_file(archive_path)


def build_research_os_export_manifest(
    *,
    export_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
    include_archive: bool = True,
) -> ResearchOsExportManifest:
    root = _artifact_root(repo_root, artifact_root)
    export_root = research_os_export_root(repo_root, root)
    export_dir = export_root / "exports" / export_id
    bundle_dir = export_dir / "bundle"
    if bundle_dir.exists():
        if not overwrite:
            raise FileExistsError(f"export bundle already exists: {bundle_dir}")
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    files = [_file_ref(label, path, bundle_dir, root, required=required) for label, path, required in _export_sources(root)]
    status, trust, warnings, blockers = _status(files)
    formats = [ResearchOsExportFormat.DIRECTORY]
    manifest = ResearchOsExportManifest(
        export_id=export_id,
        generated_at_utc=datetime.now(timezone.utc),
        artifact_root=str(root),
        export_root=str(export_root),
        bundle_directory=str(bundle_dir),
        status=status,
        trust_banner=trust,
        formats=formats,
        files=files,
        warnings=warnings,
        blockers=blockers,
        export_spine_sha256=_spine_sha(files),
    )
    payload = manifest.model_dump(mode="json")
    payload["manifest_sha256"] = _manifest_sha(payload)
    _write_json(bundle_dir / "research_os_export_manifest.json", payload)
    _write_json(export_dir / "research_os_export_manifest.json", payload)

    if include_archive:
        archive_path = export_dir / f"{export_id}.tar.gz"
        archive_sha = _make_tar(bundle_dir, archive_path)
        payload["archive_path"] = str(archive_path)
        payload["archive_sha256"] = archive_sha
        payload["formats"] = [ResearchOsExportFormat.DIRECTORY.value, ResearchOsExportFormat.TAR_GZ.value]
        payload["manifest_sha256"] = _manifest_sha(payload)
        _write_json(export_dir / "research_os_export_manifest.json", payload)
        _write_json(bundle_dir / "research_os_export_manifest.json", payload)

    latest = export_root / "latest"
    if latest.exists():
        shutil.rmtree(latest)
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "research_os_export_manifest.json", payload)
    if include_archive:
        shutil.copy2(archive_path, latest / f"{export_id}.tar.gz")
    return ResearchOsExportManifest.model_validate(payload)


def verify_research_os_export(
    *,
    manifest_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    write_latest: bool = True,
) -> ResearchOsExportVerificationResult:
    path = manifest_path or research_os_export_latest_manifest_path(repo_root, artifact_root)
    raw = _read_json(path) if path.is_file() else None
    warnings: list[str] = []
    blockers: list[str] = []
    verified = 0
    missing = 0
    changed = 0
    export_id = "unknown"
    status = ResearchOsExportStatus.BLOCKED
    if raw is None:
        blockers.append("EXPORT_MANIFEST_MISSING_OR_UNREADABLE")
        result = ResearchOsExportVerificationResult(export_id=export_id, status=ResearchOsExportStatus.BLOCKED, blockers=blockers)
    else:
        manifest = ResearchOsExportManifest.model_validate(raw)
        export_id = manifest.export_id
        bundle_dir = Path(manifest.bundle_directory)
        for f in manifest.files:
            if not f.bundle_path or not f.file_sha256:
                if f.required:
                    missing += 1
                    blockers.append(f"{f.label}:BUNDLE_REF_MISSING")
                continue
            p = bundle_dir / f.bundle_path
            if not p.is_file():
                missing += 1
                blockers.append(f"{f.label}:BUNDLE_FILE_MISSING")
                continue
            actual = _sha256_file(p)
            if actual != f.file_sha256:
                changed += 1
                blockers.append(f"{f.label}:BUNDLE_FILE_DIGEST_MISMATCH")
            else:
                verified += 1
        if manifest.archive_path:
            archive = Path(manifest.archive_path)
            if not archive.is_file():
                warnings.append("ARCHIVE_NOT_PRESENT_AT_RECORDED_PATH")
            elif manifest.archive_sha256 and _sha256_file(archive) != manifest.archive_sha256:
                blockers.append("ARCHIVE_DIGEST_MISMATCH")
        if blockers:
            status = ResearchOsExportStatus.BLOCKED
        elif warnings or manifest.status != ResearchOsExportStatus.READY:
            status = ResearchOsExportStatus.RESTRICTED
        else:
            status = ResearchOsExportStatus.READY
        result = ResearchOsExportVerificationResult(
            export_id=export_id,
            status=status,
            verified_file_count=verified,
            missing_file_count=missing,
            changed_file_count=changed,
            warnings=sorted(set(warnings)),
            blockers=sorted(set(blockers)),
        )
    payload = result.model_dump(mode="json")
    payload["result_sha256"] = canonical_json_sha256({**payload, "result_sha256": ""})
    result = ResearchOsExportVerificationResult.model_validate(payload)
    if write_latest:
        out = research_os_export_latest_verification_path(repo_root, artifact_root)
        _write_json(out, result.model_dump(mode="json"))
    return result


def build_ui_research_os_export_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    manifest_path = research_os_export_latest_manifest_path(repo_root, artifact_root)
    verification_path = research_os_export_latest_verification_path(repo_root, artifact_root)
    manifest = _read_json(manifest_path) if manifest_path.is_file() else None
    verification = _read_json(verification_path) if verification_path.is_file() else None
    degraded: list[str] = []
    if manifest is None:
        degraded.append("NO_RESEARCH_OS_EXPORT_MANIFEST")
    if verification is None:
        degraded.append("NO_RESEARCH_OS_EXPORT_VERIFICATION")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "manifest_path": str(manifest_path),
        "verification_path": str(verification_path),
        "latest_export": manifest,
        "latest_verification": verification,
        "degraded": degraded,
    }


__all__ = [
    "build_research_os_export_manifest",
    "build_ui_research_os_export_latest_payload",
    "research_os_export_latest_manifest_path",
    "research_os_export_latest_verification_path",
    "research_os_export_root",
    "verify_research_os_export",
]
