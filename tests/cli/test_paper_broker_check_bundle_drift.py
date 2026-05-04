from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.cli import paper_broker
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary


def _entry(stage: str, sha: str) -> PaperExecutionTimelineEntry:
    return PaperExecutionTimelineEntry(
        stage=stage,
        stage_order={"SELECTED_INTENT": 10, "DRY_RUN": 20, "SUBMISSION": 30}.get(stage, 99),
        tracking_id="track-cli-drift",
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


def test_check_evidence_bundle_drift_cli_writes_drift_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    original = [_entry("SELECTED_INTENT", "a" * 64)]
    bundle_path, _, _ = write_paper_execution_evidence_bundle_artifact(
        timeline=original,
        timeline_summary=_summary(original),
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
    )
    current = [*original, _entry("DRY_RUN", "b" * 64)]

    def _fake_cockpit_payload():
        return {
            "execution_timeline": [entry.model_dump(mode="json") for entry in current],
            "execution_timeline_summary": _summary(current).model_dump(mode="json"),
        }

    monkeypatch.setattr(paper_broker, "build_ui_paper_execution_cockpit_payload", _fake_cockpit_payload)
    rc = paper_broker.main([
        "check-evidence-bundle-drift",
        "--bundle-artifact",
        str(bundle_path),
        "--output-root",
        str(output_root),
    ])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["drift_status"] == "DRIFTED"
    assert payload["new_source_artifact_count"] == 1
    artifact_path = Path(payload["artifact"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle_drift/v1"
    assert artifact["artifact_sha256"] == payload["artifact_sha256"]
