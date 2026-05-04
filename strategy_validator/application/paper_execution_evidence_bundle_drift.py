"""Drift checks for sealed paper execution evidence bundles.

A sealed bundle can verify cryptographically but still become stale when newer
paper-execution artifacts are generated. This module compares the latest sealed
bundle against the current paper execution timeline and records whether the
bundle still represents the current source-artifact set.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root
from strategy_validator.application.paper_execution_evidence_bundle_verification import (
    find_latest_paper_execution_evidence_bundle_artifact,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleDriftArtifact,
    PaperExecutionEvidenceBundleDriftView,
    PaperExecutionTimelineEntry,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _safe_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


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


def _source_key(*, stage: str | None, artifact_path: str | None, artifact_sha256: str | None) -> str | None:
    stage = (stage or "UNKNOWN").strip().upper() or "UNKNOWN"
    artifact_path = (artifact_path or "").strip()
    artifact_sha256 = (artifact_sha256 or "").strip()
    if not artifact_path and not artifact_sha256:
        return None
    return f"{stage}|{artifact_path}|{artifact_sha256}"


def _current_source_keys(timeline: list[PaperExecutionTimelineEntry]) -> list[str]:
    keys: list[str] = []
    for entry in timeline:
        key = _source_key(stage=entry.stage, artifact_path=entry.artifact_path, artifact_sha256=entry.artifact_sha256)
        if key is not None:
            keys.append(key)
    return sorted(set(keys))


def _bundled_source_keys(bundle_raw: dict[str, Any] | None) -> list[str]:
    if not bundle_raw:
        return []
    sources = bundle_raw.get("source_artifacts")
    if not isinstance(sources, list):
        return []
    keys: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        key = _source_key(
            stage=str(source.get("stage") or ""),
            artifact_path=str(source.get("artifact_path") or ""),
            artifact_sha256=str(source.get("artifact_sha256") or ""),
        )
        if key is not None:
            keys.append(key)
    return sorted(set(keys))


def _fingerprint(keys: list[str]) -> str | None:
    if not keys:
        return None
    return canonical_json_sha256({"source_keys": sorted(keys)})


def _stage_set(keys: list[str]) -> set[str]:
    return {key.split("|", 1)[0] for key in keys if key}


def build_paper_execution_evidence_bundle_drift_artifact(
    *,
    current_timeline: list[PaperExecutionTimelineEntry],
    current_timeline_summary: PaperExecutionTimelineSummary,
    bundle_artifact_path: Path | None = None,
    bundle_raw: dict[str, Any] | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleDriftArtifact:
    """Build a drift artifact for the current paper execution timeline."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    current_keys = _current_source_keys(current_timeline)
    bundled_keys = _bundled_source_keys(bundle_raw)
    current_fp = _fingerprint(current_keys)
    bundled_fp = _fingerprint(bundled_keys)
    new_sources = sorted(set(current_keys) - set(bundled_keys))
    removed_sources = sorted(set(bundled_keys) - set(current_keys))
    changed_stages = sorted(_stage_set(new_sources) | _stage_set(removed_sources))

    if bundle_raw is None:
        status = "NO_BUNDLE"
        trust = "UNTRUSTED"
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_MISSING")
    elif not current_timeline:
        status = "NO_TIMELINE"
        trust = "UNTRUSTED"
        blockers.append("PAPER_EXECUTION_TIMELINE_EMPTY")
    elif current_fp != bundled_fp:
        status = "DRIFTED"
        trust = "UNTRUSTED"
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFTED")
        if new_sources:
            blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_HAS_NEW_SOURCES")
        if removed_sources:
            warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_HAS_REMOVED_SOURCES")
    else:
        status = "IN_SYNC"
        trust = "TRUSTED"

    if current_timeline_summary.sequence_status != str((bundle_raw or {}).get("timeline_sequence_status") or current_timeline_summary.sequence_status):
        warnings.append("PAPER_EXECUTION_TIMELINE_STATUS_CHANGED_SINCE_BUNDLE")
    if bundle_raw is not None and not bundled_keys:
        blockers.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_HAS_NO_SOURCE_SET")
        status = "DRIFTED"
        trust = "UNTRUSTED"

    current_tracking_id = next((entry.tracking_id for entry in current_timeline if entry.tracking_id), None)
    artifact = PaperExecutionEvidenceBundleDriftArtifact(
        generated_at_utc=now,
        tracking_id=str((bundle_raw or {}).get("tracking_id") or current_tracking_id or "") or None,
        drift_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_bundle_artifact_path=str(bundle_artifact_path) if bundle_artifact_path else None,
        source_bundle_sha256=str((bundle_raw or {}).get("bundle_sha256") or "") or None,
        source_bundle_generated_at_utc=str((bundle_raw or {}).get("generated_at_utc") or "") or None,
        current_timeline_sequence_status=current_timeline_summary.sequence_status,
        current_timeline_event_count=current_timeline_summary.event_count,
        bundled_timeline_event_count=int((bundle_raw or {}).get("timeline_event_count") or 0),
        current_source_artifact_count=len(current_keys),
        bundled_source_artifact_count=len(bundled_keys),
        current_timeline_fingerprint=current_fp,
        bundled_timeline_fingerprint=bundled_fp,
        new_source_artifacts=new_sources,
        removed_source_artifacts=removed_sources,
        changed_stage_count=len(changed_stages),
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_execution_evidence_bundle_drift_artifact(
    *,
    current_timeline: list[PaperExecutionTimelineEntry],
    current_timeline_summary: PaperExecutionTimelineSummary,
    bundle_artifact_path: Path | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleDriftArtifact]:
    """Write latest + immutable drift-check artifacts."""

    source_path, raw = find_latest_paper_execution_evidence_bundle_artifact(
        bundle_artifact_path=bundle_artifact_path,
        output_root=output_root,
    )
    artifact = build_paper_execution_evidence_bundle_drift_artifact(
        current_timeline=current_timeline,
        current_timeline_summary=current_timeline_summary,
        bundle_artifact_path=source_path,
        bundle_raw=raw,
        generated_at_utc=generated_at_utc,
    )
    current_tracking_id = next((entry.tracking_id for entry in current_timeline if entry.tracking_id), None)
    tracking_id = artifact.tracking_id or current_tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_drifts"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_drift.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleDriftView:
    digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
    return PaperExecutionEvidenceBundleDriftView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=digest,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        drift_status=str(raw.get("drift_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_bundle_artifact_path=str(raw.get("source_bundle_artifact_path") or "") or None,
        source_bundle_sha256=str(raw.get("source_bundle_sha256") or "") or None,
        source_bundle_generated_at_utc=str(raw.get("source_bundle_generated_at_utc") or "") or None,
        current_timeline_sequence_status=str(raw.get("current_timeline_sequence_status") or "") or None,
        current_timeline_event_count=int(raw.get("current_timeline_event_count") or 0),
        bundled_timeline_event_count=int(raw.get("bundled_timeline_event_count") or 0),
        current_source_artifact_count=int(raw.get("current_source_artifact_count") or 0),
        bundled_source_artifact_count=int(raw.get("bundled_source_artifact_count") or 0),
        current_timeline_fingerprint=str(raw.get("current_timeline_fingerprint") or "") or None,
        bundled_timeline_fingerprint=str(raw.get("bundled_timeline_fingerprint") or "") or None,
        new_source_artifact_count=len(raw.get("new_source_artifacts") or []) if isinstance(raw.get("new_source_artifacts"), list) else 0,
        removed_source_artifact_count=len(raw.get("removed_source_artifacts") or []) if isinstance(raw.get("removed_source_artifacts"), list) else 0,
        changed_stage_count=int(raw.get("changed_stage_count") or 0),
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_drift_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleDriftView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_drifts/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_drift.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleDriftView] = []
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
    "build_paper_execution_evidence_bundle_drift_artifact",
    "read_paper_execution_evidence_bundle_drift_views",
    "write_paper_execution_evidence_bundle_drift_artifact",
]
