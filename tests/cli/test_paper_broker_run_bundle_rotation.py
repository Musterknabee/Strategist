from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli import paper_broker
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


def _fake_cockpit_payload(tmp_path: Path) -> dict[str, object]:
    timeline = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        timeline.append(
            PaperExecutionTimelineEntry(
                stage=stage,  # type: ignore[arg-type]
                stage_order=idx * 10,
                tracking_id="track-cli-rotation-exec",
                generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00",
                artifact_path=str(path),
                artifact_sha256=digest,
                status="OK",
                ok=True,
                trusted=True,
                summary_line=f"{stage} trusted",
            ).model_dump(mode="json")
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
    rotation = PaperExecutionEvidenceBundleRotationView(
        tracking_id="track-cli-rotation-exec",
        artifact_path="/tmp/paper_execution_evidence_bundle_rotation.json",
        artifact_sha256="r" * 64,
        generated_at_utc="2026-05-03T12:10:00+00:00",
        rotation_status="REQUIRED",
        trust_banner="UNTRUSTED",
        source_bundle_sha256="a" * 64,
        source_bundle_status="SEALED",
        source_verification_status="PASS",
        source_drift_status="DRIFTED",
        timeline_sequence_status="COMPLETE",
        timeline_event_count=6,
        rotation_reason_codes=["BUNDLE_DRIFTED"],
        recommended_operator_sequence=["strategy-validator-paper-broker seal-evidence-bundle"],
        blockers=[],
        warnings=[],
    )
    return {
        "execution_timeline": timeline,
        "execution_timeline_summary": summary.model_dump(mode="json"),
        "latest_evidence_bundle_rotation": rotation.model_dump(mode="json"),
    }


def test_run_evidence_bundle_rotation_cli_writes_execution_manifest(monkeypatch, tmp_path: Path, capsys) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    monkeypatch.setattr(paper_broker, "build_ui_paper_execution_cockpit_payload", lambda: _fake_cockpit_payload(tmp_path))

    rc = paper_broker.main(["run-evidence-bundle-rotation", "--output-root", str(output_root)])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rotation_execution_status"] == "PASS"
    assert payload["verification_status"] == "PASS"
    assert payload["drift_status"] == "IN_SYNC"
    artifact_path = Path(payload["artifact"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle_rotation_execution/v1"
    assert artifact["passed_step_count"] == 3
