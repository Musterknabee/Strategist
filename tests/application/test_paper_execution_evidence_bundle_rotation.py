from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_rotation import (
    build_paper_execution_evidence_bundle_rotation_artifact,
    read_paper_execution_evidence_bundle_rotation_views,
    write_paper_execution_evidence_bundle_rotation_artifact,
)
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleDriftView,
    PaperExecutionEvidenceBundleVerificationView,
    PaperExecutionEvidenceBundleView,
    PaperExecutionTimelineSummary,
)


def _summary(status: str = "COMPLETE") -> PaperExecutionTimelineSummary:
    return PaperExecutionTimelineSummary(
        event_count=6,
        stage_count=6,
        trusted_event_count=6,
        blocker_count=0,
        warning_count=0,
        latest_event_at_utc="2026-05-03T12:00:00+00:00",
        sequence_status=status,  # type: ignore[arg-type]
        completed_stages=["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"],
        missing_stages=[] if status == "COMPLETE" else ["POSITION_RECONCILIATION"],
    )


def _bundle() -> PaperExecutionEvidenceBundleView:
    return PaperExecutionEvidenceBundleView(
        tracking_id="track-rotation",
        artifact_path="/tmp/paper_execution_evidence_bundle.json",
        bundle_sha256="a" * 64,
        generated_at_utc="2026-05-03T12:01:00+00:00",
        trust_banner="TRUSTED",
        bundle_status="SEALED",
        timeline_sequence_status="COMPLETE",
        timeline_event_count=6,
        source_artifact_count=6,
        missing_stages=[],
        blockers=[],
        warnings=[],
    )


def _verification(status: str = "PASS") -> PaperExecutionEvidenceBundleVerificationView:
    return PaperExecutionEvidenceBundleVerificationView(
        tracking_id="track-rotation",
        artifact_path="/tmp/paper_execution_evidence_bundle_verification.json",
        generated_at_utc="2026-05-03T12:02:00+00:00",
        verification_status=status,  # type: ignore[arg-type]
        trust_banner="TRUSTED" if status == "PASS" else "UNTRUSTED",
        bundle_hash_valid=status == "PASS",
        timeline_source_link_valid=status == "PASS",
        source_artifact_count=6,
        verified_source_artifact_count=6 if status == "PASS" else 0,
        missing_source_artifact_count=0,
        mismatched_source_artifact_count=0 if status == "PASS" else 1,
        blockers=[] if status == "PASS" else ["BUNDLE_HASH_MISMATCH"],
        warnings=[],
    )


def _drift(status: str = "IN_SYNC") -> PaperExecutionEvidenceBundleDriftView:
    return PaperExecutionEvidenceBundleDriftView(
        tracking_id="track-rotation",
        artifact_path="/tmp/paper_execution_evidence_bundle_drift.json",
        generated_at_utc="2026-05-03T12:03:00+00:00",
        drift_status=status,  # type: ignore[arg-type]
        trust_banner="TRUSTED" if status == "IN_SYNC" else "UNTRUSTED",
        source_bundle_sha256="a" * 64,
        current_timeline_sequence_status="COMPLETE",
        current_timeline_event_count=6,
        bundled_timeline_event_count=6,
        current_source_artifact_count=6,
        bundled_source_artifact_count=6,
        new_source_artifact_count=1 if status == "DRIFTED" else 0,
        removed_source_artifact_count=0,
        changed_stage_count=1 if status == "DRIFTED" else 0,
        blockers=["PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFTED"] if status == "DRIFTED" else [],
        warnings=[],
    )


def test_rotation_not_needed_when_bundle_verified_and_in_sync() -> None:
    artifact = build_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=_summary(),
        latest_evidence_bundle=_bundle(),
        latest_evidence_bundle_verification=_verification("PASS"),
        latest_evidence_bundle_drift=_drift("IN_SYNC"),
        generated_at_utc=datetime(2026, 5, 3, 12, 4, tzinfo=timezone.utc),
    )

    assert artifact.rotation_status == "NOT_NEEDED"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.blockers == []
    assert "CURRENT_BUNDLE_VERIFIED_AND_IN_SYNC" in artifact.rotation_reason_codes


def test_rotation_required_for_drifted_bundle() -> None:
    artifact = build_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=_summary(),
        latest_evidence_bundle=_bundle(),
        latest_evidence_bundle_verification=_verification("PASS"),
        latest_evidence_bundle_drift=_drift("DRIFTED"),
        generated_at_utc=datetime(2026, 5, 3, 12, 5, tzinfo=timezone.utc),
    )

    assert artifact.rotation_status == "REQUIRED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "BUNDLE_DRIFTED" in artifact.rotation_reason_codes
    assert any("seal-evidence-bundle" in cmd for cmd in artifact.recommended_operator_sequence)


def test_rotation_writer_surfaces_view(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    latest, history, artifact = write_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=_summary(),
        latest_evidence_bundle=_bundle(),
        latest_evidence_bundle_verification=_verification("PASS"),
        latest_evidence_bundle_drift=_drift("DRIFTED"),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 6, tzinfo=timezone.utc),
    )

    assert latest.exists()
    assert history.exists()
    views = read_paper_execution_evidence_bundle_rotation_views(output_root=output_root)
    assert views
    assert views[0].rotation_status == artifact.rotation_status
    assert views[0].artifact_sha256 == artifact.artifact_sha256
