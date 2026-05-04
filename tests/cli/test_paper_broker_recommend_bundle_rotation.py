from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli import paper_broker
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineSummary


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


def test_recommend_evidence_bundle_rotation_cli_writes_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"

    def _fake_cockpit_payload():
        return {
            "execution_timeline_summary": _summary().model_dump(mode="json"),
            "latest_evidence_bundle": {
                "schema_version": "paper_execution_evidence_bundle_view/v1",
                "tracking_id": "track-cli-rotation",
                "artifact_path": "/tmp/paper_execution_evidence_bundle.json",
                "generated_at_utc": "2026-05-03T12:01:00+00:00",
                "trust_banner": "TRUSTED",
                "bundle_status": "SEALED",
                "bundle_sha256": "a" * 64,
                "timeline_sequence_status": "COMPLETE",
                "timeline_event_count": 6,
                "source_artifact_count": 6,
                "missing_stages": [],
                "blockers": [],
                "warnings": [],
            },
            "latest_evidence_bundle_verification": {
                "schema_version": "paper_execution_evidence_bundle_verification_view/v1",
                "tracking_id": "track-cli-rotation",
                "artifact_path": "/tmp/paper_execution_evidence_bundle_verification.json",
                "generated_at_utc": "2026-05-03T12:02:00+00:00",
                "verification_status": "PASS",
                "trust_banner": "TRUSTED",
                "bundle_hash_valid": True,
                "timeline_source_link_valid": True,
                "source_artifact_count": 6,
                "verified_source_artifact_count": 6,
                "missing_source_artifact_count": 0,
                "mismatched_source_artifact_count": 0,
                "blockers": [],
                "warnings": [],
            },
            "latest_evidence_bundle_drift": {
                "schema_version": "paper_execution_evidence_bundle_drift_view/v1",
                "tracking_id": "track-cli-rotation",
                "artifact_path": "/tmp/paper_execution_evidence_bundle_drift.json",
                "generated_at_utc": "2026-05-03T12:03:00+00:00",
                "drift_status": "DRIFTED",
                "trust_banner": "UNTRUSTED",
                "source_bundle_sha256": "a" * 64,
                "current_timeline_sequence_status": "COMPLETE",
                "current_timeline_event_count": 6,
                "bundled_timeline_event_count": 6,
                "current_source_artifact_count": 7,
                "bundled_source_artifact_count": 6,
                "new_source_artifact_count": 1,
                "removed_source_artifact_count": 0,
                "changed_stage_count": 1,
                "blockers": ["PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFTED"],
                "warnings": [],
            },
        }

    monkeypatch.setattr(paper_broker, "build_ui_paper_execution_cockpit_payload", _fake_cockpit_payload)
    rc = paper_broker.main(["recommend-evidence-bundle-rotation", "--output-root", str(output_root)])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["rotation_status"] == "REQUIRED"
    assert "BUNDLE_DRIFTED" in payload["rotation_reason_codes"]
    artifact_path = Path(payload["artifact"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle_rotation/v1"
