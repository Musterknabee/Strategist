from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_rotation_execution import (
    read_paper_execution_evidence_bundle_rotation_execution_views,
    write_paper_execution_evidence_bundle_rotation_execution_artifact,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleRotationView,
    PaperExecutionTimelineEntry,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_STAGES = ["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"]


def _source(path: Path, stage: str) -> str:
    raw = {"schema_version": "test_source/v1", "stage": stage, "ok": True}
    digest = canonical_json_sha256(raw)
    path.write_text(json.dumps({**raw, "artifact_sha256": digest}, sort_keys=True), encoding="utf-8")
    return digest


def _timeline(tmp_path: Path) -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    entries: list[PaperExecutionTimelineEntry] = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        entries.append(
            PaperExecutionTimelineEntry(
                stage=stage,  # type: ignore[arg-type]
                stage_order=idx * 10,
                tracking_id="track-rotation-exec",
                generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00",
                artifact_path=str(path),
                artifact_sha256=digest,
                status="OK",
                ok=True,
                trusted=True,
                summary_line=f"{stage} trusted",
            )
        )
    summary = PaperExecutionTimelineSummary(
        event_count=6,
        stage_count=6,
        trusted_event_count=6,
        blocker_count=0,
        warning_count=0,
        latest_event_at_utc="2026-05-03T12:06:00+00:00",
        sequence_status="COMPLETE",
        completed_stages=list(_STAGES),
        missing_stages=[],
    )
    return entries, summary


def _rotation(status: str = "REQUIRED") -> PaperExecutionEvidenceBundleRotationView:
    return PaperExecutionEvidenceBundleRotationView(
        tracking_id="track-rotation-exec",
        artifact_path="/tmp/paper_execution_evidence_bundle_rotation.json",
        artifact_sha256="r" * 64,
        generated_at_utc="2026-05-03T12:10:00+00:00",
        rotation_status=status,  # type: ignore[arg-type]
        trust_banner="UNTRUSTED" if status == "REQUIRED" else "TRUSTED",
        source_bundle_sha256="a" * 64,
        source_bundle_status="SEALED",
        source_verification_status="PASS",
        source_drift_status="DRIFTED" if status == "REQUIRED" else "IN_SYNC",
        timeline_sequence_status="COMPLETE",
        timeline_event_count=6,
        rotation_reason_codes=["BUNDLE_DRIFTED"] if status == "REQUIRED" else ["CURRENT_BUNDLE_VERIFIED_AND_IN_SYNC"],
        recommended_operator_sequence=["strategy-validator-paper-broker seal-evidence-bundle"],
        blockers=[],
        warnings=[],
    )


def test_rotation_execution_runs_seal_verify_and_drift(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path)

    latest, history, artifact = write_paper_execution_evidence_bundle_rotation_execution_artifact(
        timeline=timeline,
        timeline_summary=summary,
        latest_rotation=_rotation("REQUIRED"),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 20, tzinfo=timezone.utc),
    )

    assert latest.exists()
    assert history.exists()
    assert artifact.rotation_execution_status == "PASS"
    assert artifact.trust_banner == "TRUSTED"
    assert [step.step_name for step in artifact.steps] == ["SEAL", "VERIFY", "DRIFT_CHECK"]
    assert artifact.verification_status == "PASS"
    assert artifact.drift_status == "IN_SYNC"

    views = read_paper_execution_evidence_bundle_rotation_execution_views(output_root=output_root)
    assert views
    assert views[0].rotation_execution_status == "PASS"
    assert views[0].passed_step_count == 3


def test_rotation_execution_skips_when_not_needed(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path)

    _, _, artifact = write_paper_execution_evidence_bundle_rotation_execution_artifact(
        timeline=timeline,
        timeline_summary=summary,
        latest_rotation=_rotation("NOT_NEEDED"),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 21, tzinfo=timezone.utc),
    )

    assert artifact.rotation_execution_status == "SKIPPED"
    assert artifact.skipped_step_count == 1
    assert "SOURCE_ROTATION_RECOMMENDATION_NOT_NEEDED" in artifact.warnings
