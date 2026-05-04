from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import (
    read_paper_execution_evidence_bundle_attestation_views,
    write_paper_execution_evidence_bundle_attestation_artifact,
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


def _timeline(tmp_path: Path, tracking_id: str = "track-attest") -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
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


def _sealed_verified_in_sync(tmp_path: Path) -> Path:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path)
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 10, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 11, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 12, tzinfo=timezone.utc))
    return output_root


def test_keyless_attestation_writes_trusted_envelope(tmp_path: Path) -> None:
    output_root = _sealed_verified_in_sync(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_attestation_artifact(
        output_root=output_root,
        signer_identity="local-test-signer",
        generated_at_utc=datetime(2026, 5, 3, 12, 13, tzinfo=timezone.utc),
    )

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.attestation_status == "ATTESTED"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.signature_status == "UNSIGNED_KEYLESS_STUB"
    assert artifact.envelope["payload_type"] == "application/vnd.in-toto+json"
    assert artifact.envelope["signatures"][0]["sig"] == "KEYLESS_STUB_NO_PRIVATE_KEY"
    assert artifact.source_verification_status == "PASS"
    assert artifact.source_drift_status == "IN_SYNC"
    assert artifact.statement_payload_sha256

    views = read_paper_execution_evidence_bundle_attestation_views(output_root=output_root)
    assert views
    assert views[0].attestation_status == "ATTESTED"
    assert views[0].signer_identity == "local-test-signer"


def test_cockpit_and_daily_run_surface_attestation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root = _sealed_verified_in_sync(tmp_path)
    write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root)

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["evidence_bundle_attestation_count"] >= 1
    assert cockpit["latest_evidence_bundle_attestation"]["attestation_status"] == "ATTESTED"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_attestation_status"] == "ATTESTED"
    assert daily["summary"]["paper_execution_latest_bundle_attested_count"] == 1


def test_attestation_blocks_without_verification_and_drift(tmp_path: Path) -> None:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path, tracking_id="track-blocked-attest")
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root)

    _, _, artifact = write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root)

    assert artifact.attestation_status == "BLOCKED"
    assert "PAPER_EXECUTION_EVIDENCE_BUNDLE_VERIFICATION_MISSING" in artifact.blockers
    assert "PAPER_EXECUTION_EVIDENCE_BUNDLE_DRIFT_CHECK_MISSING" in artifact.blockers
