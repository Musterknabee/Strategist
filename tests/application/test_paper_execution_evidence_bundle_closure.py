from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import write_paper_execution_evidence_bundle_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import write_paper_execution_evidence_bundle_attestation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure import (
    read_paper_execution_evidence_bundle_closure_views,
    write_paper_execution_evidence_bundle_closure_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_drift import write_paper_execution_evidence_bundle_drift_artifact
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_STAGES = ["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"]


def _source(path: Path, stage: str) -> str:
    raw = {"schema_version": "test_source/v1", "stage": stage, "ok": True}
    digest = canonical_json_sha256(raw)
    path.write_text(json.dumps({**raw, "artifact_sha256": digest}, sort_keys=True), encoding="utf-8")
    return digest


def _timeline(tmp_path: Path, tracking_id: str = "track-closure") -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    entries: list[PaperExecutionTimelineEntry] = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        entries.append(
            PaperExecutionTimelineEntry(
                stage=stage,  # type: ignore[arg-type]
                stage_order=idx * 10,
                tracking_id=tracking_id,
                generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00",
                artifact_path=str(path),
                artifact_sha256=digest,
                status="OK",
                ok=True,
                trusted=True,
                summary_line=f"{stage} trusted",
            )
        )
    return entries, PaperExecutionTimelineSummary(
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


def _setup_verified_attestation(tmp_path: Path) -> Path:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path)
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 10, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 11, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 12, tzinfo=timezone.utc))
    latest_attestation_path, _, _ = write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 13, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_attestation_verification_artifact(attestation_artifact_path=latest_attestation_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 14, tzinfo=timezone.utc))
    return output_root


def test_evidence_bundle_closure_ready_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root = _setup_verified_attestation(tmp_path)

    latest_path, history_path, closure = write_paper_execution_evidence_bundle_closure_artifact(
        output_root=output_root,
        generated_at_utc=datetime(2026, 5, 3, 12, 15, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert closure.closure_status == "READY_FOR_OPERATOR_REVIEW"
    assert closure.trust_banner == "TRUSTED"
    assert closure.source_attestation_artifact_hash_valid is True
    assert closure.source_attestation_statement_hash_valid is True
    assert closure.source_attestation_envelope_hash_valid is True
    assert closure.source_attestation_keyless_stub_valid is True
    assert closure.source_attestation_bundle_hash_valid is True
    assert closure.source_attestation_bundle_verification_hash_valid is True
    assert closure.source_attestation_drift_hash_valid is True
    assert "READY_FOR_OPERATOR_REVIEW" in closure.closure_reason_codes

    views = read_paper_execution_evidence_bundle_closure_views(output_root=output_root)
    assert views and views[0].closure_status == "READY_FOR_OPERATOR_REVIEW"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_closure_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert cockpit["latest_evidence_bundle_closure"]["trust_banner"] == "TRUSTED"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_closure_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert daily["summary"]["paper_execution_latest_bundle_closure_ready_count"] == 1


def test_evidence_bundle_closure_blocks_without_attestation_verification(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path, tracking_id="track-closure-blocked")
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root)
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root)
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root)
    write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root)

    _, _, closure = write_paper_execution_evidence_bundle_closure_artifact(output_root=output_root)

    assert closure.closure_status == "BLOCKED"
    assert closure.trust_banner == "UNTRUSTED"
    assert "PAPER_EXECUTION_EVIDENCE_BUNDLE_ATTESTATION_VERIFICATION_MISSING" in closure.blockers
    assert "NO_ATTESTATION_VERIFICATION" in closure.closure_reason_codes
