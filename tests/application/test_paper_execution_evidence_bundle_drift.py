from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_drift import (
    build_paper_execution_evidence_bundle_drift_artifact,
    read_paper_execution_evidence_bundle_drift_views,
    write_paper_execution_evidence_bundle_drift_artifact,
)
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary


def _entry(stage: str, sha: str, t: str = "track-drift") -> PaperExecutionTimelineEntry:
    return PaperExecutionTimelineEntry(
        stage=stage,
        stage_order={"SELECTED_INTENT": 10, "DRY_RUN": 20, "SUBMISSION": 30}.get(stage, 99),
        tracking_id=t,
        generated_at_utc="2026-05-03T12:00:00+00:00",
        artifact_path=f"/tmp/{stage.lower()}.json",
        artifact_sha256=sha,
        status="OK",
        ok=True,
        trusted=True,
        summary_line=f"{stage} evidence",
    )


def _summary(entries: list[PaperExecutionTimelineEntry]) -> PaperExecutionTimelineSummary:
    stages = [entry.stage for entry in entries]
    return PaperExecutionTimelineSummary(
        event_count=len(entries),
        stage_count=len(set(stages)),
        trusted_event_count=len(entries),
        blocker_count=0,
        warning_count=0,
        latest_event_at_utc="2026-05-03T12:00:00+00:00",
        sequence_status="PARTIAL",
        completed_stages=stages,
        missing_stages=[],
    )


def test_bundle_drift_detects_current_timeline_source_changes(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    original = [_entry("SELECTED_INTENT", "a" * 64), _entry("DRY_RUN", "b" * 64)]
    bundle_path, _, bundle = write_paper_execution_evidence_bundle_artifact(
        timeline=original,
        timeline_summary=_summary(original),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
    )

    same = build_paper_execution_evidence_bundle_drift_artifact(
        current_timeline=original,
        current_timeline_summary=_summary(original),
        bundle_artifact_path=bundle_path,
        bundle_raw=bundle.model_dump(mode="json"),
        generated_at_utc=datetime(2026, 5, 3, 12, 1, tzinfo=timezone.utc),
    )
    assert same.drift_status == "IN_SYNC"
    assert same.trust_banner == "TRUSTED"
    assert same.blockers == []

    changed = [*original, _entry("SUBMISSION", "c" * 64)]
    drift = build_paper_execution_evidence_bundle_drift_artifact(
        current_timeline=changed,
        current_timeline_summary=_summary(changed),
        bundle_artifact_path=bundle_path,
        bundle_raw=bundle.model_dump(mode="json"),
        generated_at_utc=datetime(2026, 5, 3, 12, 2, tzinfo=timezone.utc),
    )
    assert drift.drift_status == "DRIFTED"
    assert drift.trust_banner == "UNTRUSTED"
    assert "PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFTED" in drift.blockers
    assert drift.new_source_artifacts
    assert drift.changed_stage_count == 1


def test_bundle_drift_writer_surfaces_view(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline = [_entry("SELECTED_INTENT", "d" * 64)]
    bundle_path, _, _ = write_paper_execution_evidence_bundle_artifact(
        timeline=timeline,
        timeline_summary=_summary(timeline),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
    )

    latest, history, artifact = write_paper_execution_evidence_bundle_drift_artifact(
        current_timeline=timeline,
        current_timeline_summary=_summary(timeline),
        bundle_artifact_path=bundle_path,
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 3, tzinfo=timezone.utc),
    )

    assert latest.exists()
    assert history.exists()
    assert artifact.drift_status == "IN_SYNC"
    views = read_paper_execution_evidence_bundle_drift_views(output_root=output_root)
    assert views
    assert views[0].drift_status == "IN_SYNC"
    assert views[0].artifact_sha256 == artifact.artifact_sha256
