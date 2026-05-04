"""Research OS evidence catalog builder.

Builds an offline, digest-linked index of existing Research OS evidence artifacts.
The catalog is intentionally read-plane only: no network, no broker orders, no ledger
mutation, no deployment approval, and no profitability certification.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_evidence_catalog import (
    ResearchOsEvidenceCatalog,
    ResearchOsEvidenceCatalogCategory,
    ResearchOsEvidenceCatalogEntry,
    ResearchOsEvidenceCatalogStatus,
)

_SCHEMA = "ui_research_os_evidence_catalog/v1"

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

_SCAN_PATTERNS: tuple[tuple[str, ResearchOsEvidenceCatalogCategory, bool], ...] = (
    ("research_os_operator_runs/latest/research_os_operator_run_manifest.json", ResearchOsEvidenceCatalogCategory.OPERATOR_RUN, True),
    ("research_os_drift/latest/research_os_drift_report.json", ResearchOsEvidenceCatalogCategory.DRIFT, True),
    ("research_os_policy_gate/latest/research_os_policy_gate_report.json", ResearchOsEvidenceCatalogCategory.POLICY_GATE, True),
    ("research_os_exceptions/latest/research_os_exception_record.json", ResearchOsEvidenceCatalogCategory.EXCEPTION, True),
    ("research_os_remediation/latest/research_os_remediation_plan.json", ResearchOsEvidenceCatalogCategory.REMEDIATION, True),
    ("research_os_release_readiness/latest/research_os_release_readiness_report.json", ResearchOsEvidenceCatalogCategory.RELEASE_READINESS, True),
    ("research_os_handoff/latest/research_os_handoff_pack.json", ResearchOsEvidenceCatalogCategory.HANDOFF, True),
    ("research_os_handoff_signoff/latest/research_os_handoff_verification_result.json", ResearchOsEvidenceCatalogCategory.HANDOFF_SIGNOFF, True),
    ("research_os_handoff_signoff/latest/research_os_handoff_reviewer_signoff.json", ResearchOsEvidenceCatalogCategory.HANDOFF_SIGNOFF, True),
    ("research_os_review_journal/latest/research_os_review_journal.json", ResearchOsEvidenceCatalogCategory.REVIEW_JOURNAL, True),
    ("research_os_review_journal/journals/*/research_os_review_journal.json", ResearchOsEvidenceCatalogCategory.REVIEW_JOURNAL, False),
    ("research_os_handoff_signoff/verifications/*/research_os_handoff_verification_result.json", ResearchOsEvidenceCatalogCategory.HANDOFF_SIGNOFF, False),
    ("research_os_handoff_signoff/signoffs/*/research_os_handoff_reviewer_signoff.json", ResearchOsEvidenceCatalogCategory.HANDOFF_SIGNOFF, False),
    ("research_os_handoff/packs/*/research_os_handoff_pack.json", ResearchOsEvidenceCatalogCategory.HANDOFF, False),
    ("research_os_release_readiness/reports/*/research_os_release_readiness_report.json", ResearchOsEvidenceCatalogCategory.RELEASE_READINESS, False),
    ("research_os_remediation/plans/*/research_os_remediation_plan.json", ResearchOsEvidenceCatalogCategory.REMEDIATION, False),
    ("research_os_exceptions/exceptions/*/research_os_exception_record.json", ResearchOsEvidenceCatalogCategory.EXCEPTION, False),
    ("research_os_policy_gate/gates/*/research_os_policy_gate_report.json", ResearchOsEvidenceCatalogCategory.POLICY_GATE, False),
    ("research_os_drift/reports/*/research_os_drift_report.json", ResearchOsEvidenceCatalogCategory.DRIFT, False),
    ("research_os_operator_runs/runs/*/research_os_operator_run_manifest.json", ResearchOsEvidenceCatalogCategory.OPERATOR_RUN, False),
    ("research_os_exports/latest/research_os_export_manifest.json", ResearchOsEvidenceCatalogCategory.EXPORT, True),
    ("research_os_exports/latest/research_os_export_verification.json", ResearchOsEvidenceCatalogCategory.EXPORT, True),
    ("research_os_exports/latest/*.tar.gz", ResearchOsEvidenceCatalogCategory.EXPORT, True),
    ("research_os_exports/exports/*/research_os_export_manifest.json", ResearchOsEvidenceCatalogCategory.EXPORT, False),
    ("research_os_exports/exports/*/*.tar.gz", ResearchOsEvidenceCatalogCategory.EXPORT, False),
    ("research_os_briefings/latest/research_os_briefing_pack.json", ResearchOsEvidenceCatalogCategory.BRIEFING, True),
    ("research_os_briefings/briefings/*/research_os_briefing_pack.json", ResearchOsEvidenceCatalogCategory.BRIEFING, False),
    ("research_os_closure/latest/research_os_closure_manifest.json", ResearchOsEvidenceCatalogCategory.CLOSURE, True),
    ("research_os_closure/*/research_os_closure_manifest.json", ResearchOsEvidenceCatalogCategory.CLOSURE, False),
    ("research_os_attestation/latest/closure_verification_result.json", ResearchOsEvidenceCatalogCategory.ATTESTATION, True),
    ("research_os_attestation/latest/operator_attestation.json", ResearchOsEvidenceCatalogCategory.ATTESTATION, True),
    ("research_os_attestation/verifications/*/closure_verification_result.json", ResearchOsEvidenceCatalogCategory.ATTESTATION, False),
    ("research_os_attestation/attestations/*/operator_attestation.json", ResearchOsEvidenceCatalogCategory.ATTESTATION, False),
    ("provider_paper_loop/latest/provider_paper_loop_manifest.json", ResearchOsEvidenceCatalogCategory.PROVIDER_LOOP, True),
    ("provider_historical_snapshots/latest/provider_historical_snapshot_run.json", ResearchOsEvidenceCatalogCategory.PROVIDER_SNAPSHOT, True),
    ("provider_historical_snapshots/**/*.json", ResearchOsEvidenceCatalogCategory.PROVIDER_SNAPSHOT, False),
    ("paper_broker/latest/paper_broker_status.json", ResearchOsEvidenceCatalogCategory.PAPER_BROKER, True),
    ("strategy_batches/*/batch_summary.json", ResearchOsEvidenceCatalogCategory.STRATEGY_BATCH, False),
    ("strategy_batches/**/market_data_integrity_result.json", ResearchOsEvidenceCatalogCategory.MARKET_DATA_INTEGRITY, False),
    ("strategy_memory/latest/memory_index.json", ResearchOsEvidenceCatalogCategory.STRATEGY_MEMORY, True),
    ("strategy_memory/**/*.json", ResearchOsEvidenceCatalogCategory.STRATEGY_MEMORY, False),
    ("strategy_theses/latest/thesis_evaluation.json", ResearchOsEvidenceCatalogCategory.STRATEGY_THESIS, True),
    ("strategy_theses/**/*.json", ResearchOsEvidenceCatalogCategory.STRATEGY_THESIS, False),
    ("shadow_books/latest/shadow_book_manifest.json", ResearchOsEvidenceCatalogCategory.SHADOW_BOOK, True),
    ("shadow_books/latest/latest_risk_summary.json", ResearchOsEvidenceCatalogCategory.SHADOW_BOOK, True),
    ("shadow_books/**/*.json", ResearchOsEvidenceCatalogCategory.SHADOW_BOOK, False),
    ("research_os_runtime/latest/runtime_demo_manifest.json", ResearchOsEvidenceCatalogCategory.RUNTIME, True),
)

_REQUIRED_LATEST = {
    "research_os_operator_runs/latest/research_os_operator_run_manifest.json": "NO_OPERATOR_RUN_MANIFEST",
    "research_os_closure/latest/research_os_closure_manifest.json": "NO_CLOSURE_MANIFEST",
    "research_os_attestation/latest/closure_verification_result.json": "NO_CLOSURE_VERIFICATION",
    "research_os_attestation/latest/operator_attestation.json": "NO_OPERATOR_ATTESTATION",
    "research_os_briefings/latest/research_os_briefing_pack.json": "NO_BRIEFING_PACK",
    "research_os_exports/latest/research_os_export_manifest.json": "NO_EXPORT_MANIFEST",
}


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_evidence_catalog_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_evidence_catalog").resolve()


def research_os_evidence_catalog_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_evidence_catalog_root(repo_root, artifact_root) / "latest" / "research_os_evidence_catalog.json").resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


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
        return path.resolve().as_posix()


def _contains_secret_marker(path: Path) -> bool:
    try:
        if path.stat().st_size > 5_000_000:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    upper = text.upper()
    return any(marker.upper() in upper for marker in _SECRET_MARKERS)


def _iter_candidate_paths(root: Path) -> Iterable[tuple[Path, ResearchOsEvidenceCatalogCategory, bool]]:
    seen: set[Path] = set()
    for pattern, category, latest in _SCAN_PATTERNS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            rp = path.resolve()
            if rp in seen:
                # Preserve strongest latest bit if a later pattern finds the same file.
                continue
            seen.add(rp)
            yield rp, category, latest


def _extract_hints(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    status = raw.get("status") or raw.get("verification_status") or raw.get("policy_status") or raw.get("provider_status")
    generated = raw.get("generated_at_utc") or raw.get("verified_at_utc") or raw.get("attested_at_utc") or raw.get("created_at_utc")
    run_id = raw.get("run_id") or raw.get("export_id") or raw.get("briefing_id") or raw.get("closure_id") or raw.get("attestation_id") or raw.get("book_id") or raw.get("batch_id")
    trust = raw.get("trust_banner")
    ok = raw.get("ok") if isinstance(raw.get("ok"), bool) else None
    warnings = raw.get("warnings") if isinstance(raw.get("warnings"), list) else []
    blockers = raw.get("blockers") if isinstance(raw.get("blockers"), list) else []
    meta: dict[str, Any] = {}
    for key in (
        "manifest_sha256",
        "result_sha256",
        "catalog_spine_sha256",
        "operator_run_spine_sha256",
        "export_spine_sha256",
        "closure_id",
        "decision",
        "provider_id",
        "policy_status",
        "schema_version",
    ):
        if key in raw and raw.get(key) is not None:
            meta[key] = raw.get(key)
    return {
        "schema_version_observed": str(raw.get("schema_version")) if raw.get("schema_version") else None,
        "generated_at_utc": str(generated) if generated else None,
        "status_hint": str(status) if status else None,
        "trust_banner_hint": str(trust) if trust else None,
        "ok_hint": ok,
        "run_id_hint": str(run_id) if run_id else None,
        "warnings": [str(x) for x in warnings if x is not None],
        "blockers": [str(x) for x in blockers if x is not None],
        "metadata": meta,
    }


def _entry_label(path: Path, root: Path, category: ResearchOsEvidenceCatalogCategory) -> str:
    rel = _safe_rel(path, root)
    if "/latest/" in f"/{rel}":
        return f"latest_{category.value.lower()}:{path.name}"
    parent = path.parent.name
    return f"{category.value.lower()}:{parent}:{path.name}"


def _build_entry(path: Path, root: Path, category: ResearchOsEvidenceCatalogCategory, latest_alias: bool) -> ResearchOsEvidenceCatalogEntry:
    warnings: list[str] = []
    blockers: list[str] = []
    raw = _read_json(path) if path.suffix.lower() == ".json" else None
    if path.suffix.lower() == ".json" and raw is None:
        blockers.append("UNREADABLE_JSON")
    if _contains_secret_marker(path):
        blockers.append("SECRET_MARKER_PRESENT")
    hints = _extract_hints(raw)
    warnings.extend(hints.get("warnings") or [])
    blockers.extend(hints.get("blockers") or [])
    return ResearchOsEvidenceCatalogEntry(
        label=_entry_label(path, root, category),
        category=category,
        artifact_path=str(path),
        relative_path=_safe_rel(path, root),
        file_sha256=_sha256_file(path),
        size_bytes=path.stat().st_size,
        schema_version_observed=hints.get("schema_version_observed"),
        generated_at_utc=hints.get("generated_at_utc"),
        status_hint=hints.get("status_hint"),
        trust_banner_hint=hints.get("trust_banner_hint"),
        ok_hint=hints.get("ok_hint"),
        run_id_hint=hints.get("run_id_hint"),
        required=_safe_rel(path, root) in _REQUIRED_LATEST,
        latest_alias=latest_alias or "/latest/" in f"/{_safe_rel(path, root)}",
        warnings=sorted(set(str(x) for x in warnings if x)),
        blockers=sorted(set(str(x) for x in blockers if x)),
        metadata=hints.get("metadata") or {},
    )


def _status_from_entries(entries: list[ResearchOsEvidenceCatalogEntry], root: Path) -> tuple[ResearchOsEvidenceCatalogStatus, ResearchOsTrustBanner, list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    if not entries:
        return ResearchOsEvidenceCatalogStatus.EMPTY, ResearchOsTrustBanner.UNTRUSTED, ["NO_RESEARCH_OS_EVIDENCE_ARTIFACTS"], []
    rels = {e.relative_path for e in entries}
    for rel, warning in _REQUIRED_LATEST.items():
        if rel not in rels:
            warnings.append(warning)
    for entry in entries:
        warnings.extend(f"{entry.relative_path}:{w}" for w in entry.warnings)
        blockers.extend(f"{entry.relative_path}:{b}" for b in entry.blockers)
        if entry.status_hint in {"BLOCKED", "FAILED", "TAMPERED", "MISSING"}:
            warnings.append(f"{entry.relative_path}:STATUS_{entry.status_hint}")
        elif entry.status_hint in {"RESTRICTED", "DEGRADED", "STALE", "PENDING_KEY", "WARNING"}:
            warnings.append(f"{entry.relative_path}:STATUS_{entry.status_hint}")
        if entry.ok_hint is False:
            warnings.append(f"{entry.relative_path}:OK_FALSE")
    warnings = sorted(set(warnings))
    blockers = sorted(set(blockers))
    if len(warnings) > 200:
        total = len(warnings)
        warnings = warnings[:200] + [f"CATALOG_WARNINGS_TRUNCATED:{total}"]
    if len(blockers) > 200:
        total = len(blockers)
        blockers = blockers[:200] + [f"CATALOG_BLOCKERS_TRUNCATED:{total}"]
    if blockers:
        return ResearchOsEvidenceCatalogStatus.BLOCKED, ResearchOsTrustBanner.UNTRUSTED, warnings, blockers
    if warnings:
        return ResearchOsEvidenceCatalogStatus.RESTRICTED, ResearchOsTrustBanner.TRUST_RESTRICTED, warnings, []
    return ResearchOsEvidenceCatalogStatus.READY, ResearchOsTrustBanner.TRUSTED, [], []


def _with_digest(catalog: ResearchOsEvidenceCatalog) -> ResearchOsEvidenceCatalog:
    payload = catalog.model_dump(mode="json", exclude={"manifest_sha256", "catalog_spine_sha256"})
    spine_rows = [
        {
            "relative_path": e["relative_path"],
            "category": e["category"],
            "file_sha256": e.get("file_sha256"),
            "size_bytes": e.get("size_bytes"),
        }
        for e in payload.get("entries", [])
    ]
    payload["catalog_spine_sha256"] = _canonical_sha256(spine_rows)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsEvidenceCatalog.model_validate(payload)


def build_research_os_evidence_catalog(
    *,
    catalog_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsEvidenceCatalog:
    root = _artifact_root(repo_root, artifact_root)
    entries = [_build_entry(path, root, category, latest_alias) for path, category, latest_alias in _iter_candidate_paths(root)]
    entries.sort(key=lambda e: (e.category.value, e.relative_path))
    category_counts: dict[str, int] = {}
    latest_by_category: dict[str, str] = {}
    for entry in entries:
        category_counts[entry.category.value] = category_counts.get(entry.category.value, 0) + 1
        if entry.latest_alias and entry.category.value not in latest_by_category:
            latest_by_category[entry.category.value] = entry.relative_path
    status, banner, warnings, blockers = _status_from_entries(entries, root)
    catalog = ResearchOsEvidenceCatalog(
        catalog_id=catalog_id,
        artifact_root=str(root),
        status=status,
        trust_banner=banner,
        entry_count=len(entries),
        latest_entry_count=sum(1 for e in entries if e.latest_alias),
        category_counts=category_counts,
        latest_by_category=latest_by_category,
        entries=entries,
        warnings=warnings,
        blockers=blockers,
    )
    return _with_digest(catalog)


def write_research_os_evidence_catalog(
    catalog: ResearchOsEvidenceCatalog,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_evidence_catalog_root(repo_root, artifact_root)
    cdir = root / "catalogs" / catalog.catalog_id
    path = cdir / "research_os_evidence_catalog.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"catalog already exists: {path}")
    payload = catalog.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_evidence_catalog.json")
    _write_json(latest / "latest_ref.json", {"catalog_id": catalog.catalog_id, "manifest_path": str(path), "manifest_sha256": catalog.manifest_sha256})
    return path


def build_and_write_research_os_evidence_catalog(
    *,
    catalog_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> tuple[ResearchOsEvidenceCatalog, Path]:
    catalog = build_research_os_evidence_catalog(catalog_id=catalog_id, repo_root=repo_root, artifact_root=artifact_root)
    path = write_research_os_evidence_catalog(catalog, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return catalog, path


def load_latest_research_os_evidence_catalog(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsEvidenceCatalog | None:
    raw = _read_json(research_os_evidence_catalog_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsEvidenceCatalog.model_validate(raw)


def build_ui_research_os_evidence_catalog_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_evidence_catalog_latest_path(repo_root, artifact_root)
    catalog = load_latest_research_os_evidence_catalog(repo_root=repo_root, artifact_root=artifact_root)
    if catalog is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
            "status": "NOT_PRESENT",
            "manifest_path": str(path),
            "latest": None,
            "degraded": ["NO_RESEARCH_OS_EVIDENCE_CATALOG"],
        }
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT",
        "manifest_path": str(path),
        "latest": catalog.model_dump(mode="json"),
        "degraded": [] if catalog.status == ResearchOsEvidenceCatalogStatus.READY else [f"EVIDENCE_CATALOG_{catalog.status.value}"],
    }


__all__ = [
    "build_and_write_research_os_evidence_catalog",
    "build_research_os_evidence_catalog",
    "build_ui_research_os_evidence_catalog_latest_payload",
    "load_latest_research_os_evidence_catalog",
    "research_os_evidence_catalog_latest_path",
    "research_os_evidence_catalog_root",
    "write_research_os_evidence_catalog",
]
