"""Research OS evidence drift builder.

Compares two evidence catalogs and writes a digest-linked drift report. This is
strictly offline/read-plane infrastructure: no network, no broker orders, no
ledger mutation, no deployment approval, and no profitability certification.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_evidence_catalog_ops import (
    research_os_evidence_catalog_latest_path,
    research_os_evidence_catalog_root,
)
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_drift import (
    ResearchOsEvidenceDriftChangeType,
    ResearchOsEvidenceDriftEntry,
    ResearchOsEvidenceDriftReport,
    ResearchOsEvidenceDriftStatus,
)
from strategy_validator.contracts.research_os_evidence_catalog import ResearchOsEvidenceCatalog

_SCHEMA = "ui_research_os_evidence_drift/v1"


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_evidence_drift_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_drift").resolve()


def research_os_evidence_drift_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_evidence_drift_root(repo_root, artifact_root) / "latest" / "research_os_drift_report.json").resolve()


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


def _catalog_path_candidates(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> list[Path]:
    root = research_os_evidence_catalog_root(repo_root, artifact_root)
    paths: set[Path] = set()
    latest = research_os_evidence_catalog_latest_path(repo_root, artifact_root)
    if latest.is_file():
        paths.add(latest.resolve())
    if root.is_dir():
        for path in root.glob("catalogs/*/research_os_evidence_catalog.json"):
            if path.is_file():
                paths.add(path.resolve())
    return sorted(paths, key=lambda p: (p.stat().st_mtime, p.as_posix()), reverse=True)


def _load_catalog(path: Path | None) -> tuple[ResearchOsEvidenceCatalog | None, Path | None, str | None, list[str], list[str]]:
    if path is None:
        return None, None, None, ["NO_CATALOG_PATH"], []
    if not path.is_file():
        return None, path, None, [f"CATALOG_NOT_PRESENT:{path}"], []
    raw = _read_json(path)
    if raw is None:
        return None, path, None, [], [f"CATALOG_UNREADABLE:{path}"]
    try:
        catalog = ResearchOsEvidenceCatalog.model_validate(raw)
    except Exception as exc:
        return None, path, _sha256_file(path), [], [f"CATALOG_INVALID:{type(exc).__name__}:{path}"]
    return catalog, path, _sha256_file(path), [], []


def _default_catalog_pair(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> tuple[Path | None, Path | None, list[str]]:
    paths = _catalog_path_candidates(repo_root=repo_root, artifact_root=artifact_root)
    if not paths:
        return None, None, ["NO_EVIDENCE_CATALOGS_TO_COMPARE"]
    # Prefer latest as candidate. Baseline is the first distinct catalog file that is not the same path.
    candidate = paths[0]
    baseline = next((p for p in paths[1:] if p.resolve() != candidate.resolve()), None)
    if baseline is None:
        return candidate, candidate, ["NO_DISTINCT_BASELINE_CATALOG;SELF_BASELINE_USED"]
    return baseline, candidate, []


def _entry_key(raw: dict[str, Any]) -> str:
    category = str(raw.get("category") or "OTHER")
    rel = str(raw.get("relative_path") or raw.get("artifact_path") or raw.get("label") or "unknown")
    # Key by category+relative path so latest alias movement and category changes are explicit.
    return f"{category}:{rel}"


def _entry_map(catalog: ResearchOsEvidenceCatalog | None) -> dict[str, dict[str, Any]]:
    if catalog is None:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for entry in catalog.entries:
        raw = entry.model_dump(mode="json")
        rows[_entry_key(raw)] = raw
    return rows


def _diff_entry(key: str, base: dict[str, Any] | None, cand: dict[str, Any] | None) -> ResearchOsEvidenceDriftEntry:
    changed_fields: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    if base is None and cand is not None:
        change = ResearchOsEvidenceDriftChangeType.ADDED
    elif base is not None and cand is None:
        change = ResearchOsEvidenceDriftChangeType.REMOVED
    else:
        assert base is not None and cand is not None
        for field in (
            "file_sha256",
            "size_bytes",
            "status_hint",
            "trust_banner_hint",
            "ok_hint",
            "schema_version_observed",
            "run_id_hint",
        ):
            if base.get(field) != cand.get(field):
                changed_fields.append(field)
        change = ResearchOsEvidenceDriftChangeType.CHANGED if changed_fields else ResearchOsEvidenceDriftChangeType.UNCHANGED
    source = cand or base or {}
    def _limited_marked(values: object, prefix: str, limit: int = 8) -> list[str]:
        if not isinstance(values, list):
            return []
        rows = [f"{prefix}:{x}" for x in values[:limit] if x]
        if len(values) > limit:
            rows.append(f"{prefix}:WARNINGS_TRUNCATED:{len(values)}")
        return rows

    warnings.extend(_limited_marked(base.get("warnings") if base else [], "baseline"))
    warnings.extend(_limited_marked(cand.get("warnings") if cand else [], "candidate"))
    blockers.extend(_limited_marked(base.get("blockers") if base else [], "baseline"))
    blockers.extend(_limited_marked(cand.get("blockers") if cand else [], "candidate"))
    base_size = base.get("size_bytes") if base else None
    cand_size = cand.get("size_bytes") if cand else None
    size_delta = None
    if isinstance(base_size, int) and isinstance(cand_size, int):
        size_delta = cand_size - base_size
    return ResearchOsEvidenceDriftEntry(
        key=key,
        category=str(source.get("category") or "OTHER"),
        change_type=change,
        baseline_relative_path=str(base.get("relative_path")) if base and base.get("relative_path") else None,
        candidate_relative_path=str(cand.get("relative_path")) if cand and cand.get("relative_path") else None,
        baseline_file_sha256=str(base.get("file_sha256")) if base and base.get("file_sha256") else None,
        candidate_file_sha256=str(cand.get("file_sha256")) if cand and cand.get("file_sha256") else None,
        baseline_status_hint=str(base.get("status_hint")) if base and base.get("status_hint") else None,
        candidate_status_hint=str(cand.get("status_hint")) if cand and cand.get("status_hint") else None,
        baseline_trust_banner_hint=str(base.get("trust_banner_hint")) if base and base.get("trust_banner_hint") else None,
        candidate_trust_banner_hint=str(cand.get("trust_banner_hint")) if cand and cand.get("trust_banner_hint") else None,
        baseline_generated_at_utc=str(base.get("generated_at_utc")) if base and base.get("generated_at_utc") else None,
        candidate_generated_at_utc=str(cand.get("generated_at_utc")) if cand and cand.get("generated_at_utc") else None,
        size_delta_bytes=size_delta,
        changed_fields=sorted(changed_fields),
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )


def _with_digest(report: ResearchOsEvidenceDriftReport) -> ResearchOsEvidenceDriftReport:
    payload = report.model_dump(mode="json", exclude={"manifest_sha256", "drift_spine_sha256"})
    spine_rows = [
        {
            "key": e["key"],
            "change_type": e["change_type"],
            "baseline_file_sha256": e.get("baseline_file_sha256"),
            "candidate_file_sha256": e.get("candidate_file_sha256"),
            "changed_fields": e.get("changed_fields") or [],
        }
        for e in payload.get("entries", [])
    ]
    payload["drift_spine_sha256"] = _canonical_sha256(spine_rows)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsEvidenceDriftReport.model_validate(payload)


def build_research_os_evidence_drift_report(
    *,
    drift_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    baseline_catalog_path: Path | None = None,
    candidate_catalog_path: Path | None = None,
) -> ResearchOsEvidenceDriftReport:
    root = _artifact_root(repo_root, artifact_root)
    default_warnings: list[str] = []
    if baseline_catalog_path is None or candidate_catalog_path is None:
        default_baseline, default_candidate, default_warnings = _default_catalog_pair(repo_root=repo_root, artifact_root=artifact_root)
        baseline_catalog_path = baseline_catalog_path or default_baseline
        candidate_catalog_path = candidate_catalog_path or default_candidate

    baseline, baseline_path, baseline_sha, bw, bb = _load_catalog(baseline_catalog_path)
    candidate, candidate_path, candidate_sha, cw, cb = _load_catalog(candidate_catalog_path)
    warnings = list(default_warnings) + bw + cw
    blockers = bb + cb

    base_map = _entry_map(baseline)
    cand_map = _entry_map(candidate)
    entries = [_diff_entry(key, base_map.get(key), cand_map.get(key)) for key in sorted(set(base_map) | set(cand_map))]

    added = sum(1 for e in entries if e.change_type == ResearchOsEvidenceDriftChangeType.ADDED)
    removed = sum(1 for e in entries if e.change_type == ResearchOsEvidenceDriftChangeType.REMOVED)
    changed = sum(1 for e in entries if e.change_type == ResearchOsEvidenceDriftChangeType.CHANGED)
    unchanged = sum(1 for e in entries if e.change_type == ResearchOsEvidenceDriftChangeType.UNCHANGED)

    for catalog, label in ((baseline, "BASELINE"), (candidate, "CANDIDATE")):
        if catalog is None:
            continue
        if catalog.status.value == "BLOCKED":
            blockers.append(f"{label}_CATALOG_BLOCKED")
        elif catalog.status.value in {"RESTRICTED", "EMPTY"}:
            warnings.append(f"{label}_CATALOG_{catalog.status.value}")
        warnings.extend(f"{label}:{x}" for x in catalog.warnings[:80])
        if len(catalog.warnings) > 80:
            warnings.append(f"{label}:CATALOG_WARNINGS_TRUNCATED:{len(catalog.warnings)}")
        blockers.extend(f"{label}:{x}" for x in catalog.blockers[:80])
        if len(catalog.blockers) > 80:
            blockers.append(f"{label}:CATALOG_BLOCKERS_TRUNCATED:{len(catalog.blockers)}")

    for entry in entries:
        warnings.extend(f"{entry.key}:{x}" for x in entry.warnings)
        blockers.extend(f"{entry.key}:{x}" for x in entry.blockers)

    category_counts: dict[str, dict[str, int]] = {}
    for entry in entries:
        bucket = category_counts.setdefault(entry.category, {"ADDED": 0, "REMOVED": 0, "CHANGED": 0, "UNCHANGED": 0})
        bucket[entry.change_type.value] = bucket.get(entry.change_type.value, 0) + 1

    warnings = sorted(set(warnings))
    blockers = sorted(set(blockers))
    if not candidate:
        status = ResearchOsEvidenceDriftStatus.EMPTY
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif blockers:
        status = ResearchOsEvidenceDriftStatus.BLOCKED
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif warnings or added or removed or changed:
        status = ResearchOsEvidenceDriftStatus.RESTRICTED
        banner = ResearchOsTrustBanner.TRUST_RESTRICTED
    else:
        status = ResearchOsEvidenceDriftStatus.READY
        banner = ResearchOsTrustBanner.TRUSTED

    report = ResearchOsEvidenceDriftReport(
        drift_id=drift_id,
        artifact_root=str(root),
        baseline_catalog_id=baseline.catalog_id if baseline else None,
        baseline_catalog_path=str(baseline_path) if baseline_path else None,
        baseline_catalog_sha256=baseline_sha,
        candidate_catalog_id=candidate.catalog_id if candidate else None,
        candidate_catalog_path=str(candidate_path) if candidate_path else None,
        candidate_catalog_sha256=candidate_sha,
        status=status,
        trust_banner=banner,
        added_count=added,
        removed_count=removed,
        changed_count=changed,
        unchanged_count=unchanged,
        total_compared_count=len(entries),
        category_change_counts=category_counts,
        entries=entries,
        warnings=warnings[:240] + ([f"DRIFT_WARNINGS_TRUNCATED:{len(warnings)}"] if len(warnings) > 240 else []),
        blockers=blockers[:240] + ([f"DRIFT_BLOCKERS_TRUNCATED:{len(blockers)}"] if len(blockers) > 240 else []),
    )
    return _with_digest(report)


def write_research_os_evidence_drift_report(
    report: ResearchOsEvidenceDriftReport,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_evidence_drift_root(repo_root, artifact_root)
    rdir = root / "reports" / report.drift_id
    path = rdir / "research_os_drift_report.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"drift report already exists: {path}")
    payload = report.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_drift_report.json")
    _write_json(latest / "latest_ref.json", {"drift_id": report.drift_id, "manifest_path": str(path), "manifest_sha256": report.manifest_sha256})
    return path


def build_and_write_research_os_evidence_drift_report(
    *,
    drift_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    baseline_catalog_path: Path | None = None,
    candidate_catalog_path: Path | None = None,
    overwrite: bool = False,
) -> tuple[ResearchOsEvidenceDriftReport, Path]:
    report = build_research_os_evidence_drift_report(
        drift_id=drift_id,
        repo_root=repo_root,
        artifact_root=artifact_root,
        baseline_catalog_path=baseline_catalog_path,
        candidate_catalog_path=candidate_catalog_path,
    )
    path = write_research_os_evidence_drift_report(report, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return report, path


def load_latest_research_os_evidence_drift_report(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsEvidenceDriftReport | None:
    raw = _read_json(research_os_evidence_drift_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsEvidenceDriftReport.model_validate(raw)


def build_ui_research_os_evidence_drift_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_evidence_drift_latest_path(repo_root, artifact_root)
    report = load_latest_research_os_evidence_drift_report(repo_root=repo_root, artifact_root=artifact_root)
    if report is None:
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
            "degraded": ["NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT"],
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
        "latest": report.model_dump(mode="json"),
        "degraded": [] if report.status == ResearchOsEvidenceDriftStatus.READY else [f"EVIDENCE_DRIFT_{report.status.value}"],
    }


__all__ = [
    "build_and_write_research_os_evidence_drift_report",
    "build_research_os_evidence_drift_report",
    "build_ui_research_os_evidence_drift_latest_payload",
    "load_latest_research_os_evidence_drift_report",
    "research_os_evidence_drift_latest_path",
    "research_os_evidence_drift_root",
    "write_research_os_evidence_drift_report",
]
