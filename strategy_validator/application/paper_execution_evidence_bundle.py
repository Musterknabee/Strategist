"""Paper execution evidence bundle sealing.

The bundle is a durable, digest-anchored review package for the paper-only
execution timeline. It does not submit orders, call broker networks, or mutate
the decision ledger.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleArtifact,
    PaperExecutionEvidenceBundleSource,
    PaperExecutionEvidenceBundleView,
    PaperExecutionTimelineEntry,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_REQUIRED_STAGES = {
    "SELECTED_INTENT",
    "DRY_RUN",
    "SUBMISSION",
    "ORDER_STATUS",
    "POSITION_SNAPSHOT",
    "POSITION_RECONCILIATION",
}


def _paper_broker_root(*, repo_root: Path | None = None, output_root: Path | None = None) -> Path:
    if output_root is not None:
        return output_root.expanduser().resolve()
    return (artifact_root_directory(repo_root) / "paper_broker").resolve()


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


def _tracking_id_from_timeline(timeline: list[PaperExecutionTimelineEntry]) -> str | None:
    for entry in timeline:
        value = (entry.tracking_id or "").strip()
        if value:
            return value
    return None


def _source_from_entry(entry: PaperExecutionTimelineEntry) -> PaperExecutionEvidenceBundleSource:
    return PaperExecutionEvidenceBundleSource(
        stage=entry.stage,
        tracking_id=entry.tracking_id,
        generated_at_utc=entry.generated_at_utc,
        artifact_path=entry.artifact_path,
        artifact_sha256=entry.artifact_sha256,
        status=entry.status,
        trusted=entry.trusted,
        blocker_count=len(entry.blockers),
        warning_count=len(entry.warnings),
    )


def _bundle_posture(
    *,
    timeline: list[PaperExecutionTimelineEntry],
    summary: PaperExecutionTimelineSummary,
) -> tuple[str, str, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    completed = set(summary.completed_stages)
    missing = sorted(_REQUIRED_STAGES - completed)
    if not timeline:
        blockers.append("PAPER_EXECUTION_TIMELINE_EMPTY")
    if summary.sequence_status != "COMPLETE":
        blockers.append(f"PAPER_EXECUTION_TIMELINE_{summary.sequence_status}")
    if summary.blocker_count:
        blockers.append("PAPER_EXECUTION_TIMELINE_HAS_BLOCKERS")
    if missing:
        warnings.append("PAPER_EXECUTION_TIMELINE_MISSING_STAGES:" + ",".join(missing))
    if any(not e.trusted for e in timeline):
        warnings.append("PAPER_EXECUTION_TIMELINE_HAS_UNTRUSTED_EVENTS")
    if any(not (e.artifact_sha256 or "").strip() for e in timeline if e.artifact_path):
        warnings.append("PAPER_EXECUTION_TIMELINE_HAS_PATH_WITHOUT_SHA")

    if blockers:
        return "UNTRUSTED", "SEALED_BLOCKED", sorted(set(blockers)), sorted(set(warnings))
    if warnings or summary.trusted_event_count < len(_REQUIRED_STAGES):
        return "TRUST_RESTRICTED", "SEALED_RESTRICTED", [], sorted(set(warnings))
    return "TRUSTED", "SEALED", [], []


def build_paper_execution_evidence_bundle_artifact(
    *,
    timeline: list[PaperExecutionTimelineEntry],
    timeline_summary: PaperExecutionTimelineSummary,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    trust_banner, bundle_status, blockers, warnings = _bundle_posture(timeline=timeline, summary=timeline_summary)
    sources = [_source_from_entry(entry) for entry in timeline]
    artifact = PaperExecutionEvidenceBundleArtifact(
        generated_at_utc=now,
        tracking_id=_tracking_id_from_timeline(timeline),
        trust_banner=trust_banner,  # type: ignore[arg-type]
        bundle_status=bundle_status,  # type: ignore[arg-type]
        timeline_sequence_status=timeline_summary.sequence_status,
        timeline_event_count=timeline_summary.event_count,
        timeline_trusted_event_count=timeline_summary.trusted_event_count,
        timeline_blocker_count=timeline_summary.blocker_count,
        timeline_warning_count=timeline_summary.warning_count,
        source_artifact_count=sum(1 for source in sources if source.artifact_sha256),
        missing_stages=list(timeline_summary.missing_stages),
        source_artifacts=sources,
        timeline_summary=timeline_summary,
        timeline=timeline,
        blockers=blockers,
        warnings=warnings,
    )
    plain = artifact.model_dump(mode="json", exclude={"bundle_sha256"})
    return artifact.model_copy(update={"bundle_sha256": canonical_json_sha256(plain)})


def write_paper_execution_evidence_bundle_artifact(
    *,
    timeline: list[PaperExecutionTimelineEntry],
    timeline_summary: PaperExecutionTimelineSummary,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleArtifact]:
    artifact = build_paper_execution_evidence_bundle_artifact(
        timeline=timeline,
        timeline_summary=timeline_summary,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundles"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.bundle_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleView:
    digest = str(raw.get("bundle_sha256") or canonical_json_sha256(raw))
    return PaperExecutionEvidenceBundleView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        bundle_sha256=digest,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        bundle_status=str(raw.get("bundle_status") or "UNKNOWN"),  # type: ignore[arg-type]
        timeline_sequence_status=str(raw.get("timeline_sequence_status") or "EMPTY"),
        timeline_event_count=int(raw.get("timeline_event_count") or 0),
        timeline_trusted_event_count=int(raw.get("timeline_trusted_event_count") or 0),
        timeline_blocker_count=int(raw.get("timeline_blocker_count") or 0),
        source_artifact_count=int(raw.get("source_artifact_count") or 0),
        missing_stages=[str(x) for x in raw.get("missing_stages", []) if x not in (None, "")]
        if isinstance(raw.get("missing_stages"), list)
        else [],
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")]
        if isinstance(raw.get("blockers"), list)
        else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")]
        if isinstance(raw.get("warnings"), list)
        else [],
    )


def read_paper_execution_evidence_bundle_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundles/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleView] = []
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
    "build_paper_execution_evidence_bundle_artifact",
    "read_paper_execution_evidence_bundle_views",
    "write_paper_execution_evidence_bundle_artifact",
]
