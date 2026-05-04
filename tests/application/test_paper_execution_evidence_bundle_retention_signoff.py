from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import write_paper_execution_evidence_bundle_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import write_paper_execution_evidence_bundle_attestation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure import write_paper_execution_evidence_bundle_closure_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure_verification import write_paper_execution_evidence_bundle_closure_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_drift import write_paper_execution_evidence_bundle_drift_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export import write_paper_execution_evidence_bundle_export_manifest_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export_verification import write_paper_execution_evidence_bundle_export_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention import write_paper_execution_evidence_bundle_retention_receipt_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff import (
    read_paper_execution_evidence_bundle_retention_signoff_views,
    write_paper_execution_evidence_bundle_retention_signoff_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_verification import write_paper_execution_evidence_bundle_retention_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_STAGES = ["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"]


def _source(path: Path, stage: str) -> str:
    raw = {"schema_version": "test_source/v1", "stage": stage, "ok": True}
    digest = canonical_json_sha256(raw)
    path.write_text(json.dumps({**raw, "artifact_sha256": digest}, sort_keys=True), encoding="utf-8")
    return digest


def _timeline(tmp_path: Path, tracking_id: str = "track-retention-signoff") -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    entries: list[PaperExecutionTimelineEntry] = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        entries.append(PaperExecutionTimelineEntry(stage=stage, stage_order=idx * 10, tracking_id=tracking_id, generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00", artifact_path=str(path), artifact_sha256=digest, status="OK", ok=True, trusted=True, summary_line=f"{stage} trusted"))  # type: ignore[arg-type]
    return entries, PaperExecutionTimelineSummary(event_count=6, stage_count=6, trusted_event_count=6, blocker_count=0, warning_count=0, latest_event_at_utc="2026-05-03T12:06:00+00:00", sequence_status="COMPLETE", completed_stages=list(_STAGES), missing_stages=[])


def _setup_retention_verification(tmp_path: Path) -> tuple[Path, Path]:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline, summary = _timeline(tmp_path)
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 10, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 11, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 12, tzinfo=timezone.utc))
    latest_attestation_path, _, _ = write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 13, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_attestation_verification_artifact(attestation_artifact_path=latest_attestation_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 14, tzinfo=timezone.utc))
    latest_closure_path, _, _ = write_paper_execution_evidence_bundle_closure_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 15, tzinfo=timezone.utc))
    latest_closure_verification_path, _, _ = write_paper_execution_evidence_bundle_closure_verification_artifact(closure_artifact_path=latest_closure_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 16, tzinfo=timezone.utc))
    latest_export_manifest_path, _, _ = write_paper_execution_evidence_bundle_export_manifest_artifact(closure_verification_artifact_path=latest_closure_verification_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 17, tzinfo=timezone.utc))
    latest_export_verification_path, _, _ = write_paper_execution_evidence_bundle_export_verification_artifact(export_manifest_artifact_path=latest_export_manifest_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 18, tzinfo=timezone.utc))
    latest_retention_receipt_path, _, _ = write_paper_execution_evidence_bundle_retention_receipt_artifact(export_verification_artifact_path=latest_export_verification_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 19, tzinfo=timezone.utc))
    latest_retention_verification_path, _, _ = write_paper_execution_evidence_bundle_retention_verification_artifact(retention_receipt_artifact_path=latest_retention_receipt_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 20, tzinfo=timezone.utc))
    return output_root, latest_retention_verification_path


def test_retention_signoff_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_retention_verification_path = _setup_retention_verification(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_signoff_artifact(retention_verification_artifact_path=latest_retention_verification_path, output_root=output_root, operator_id="jp", decision_note="external retention approved", generated_at_utc=datetime(2026, 5, 3, 12, 21, tzinfo=timezone.utc))

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.signoff_status == "SIGNED_OFF"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.operator_id == "jp"
    assert artifact.retention_verification_artifact_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.recomputed_retention_ready_entry_count == 7
    assert artifact.signoff_statement_sha256
    assert artifact.no_files_copied is True
    assert artifact.execution_authority == "NONE"

    views = read_paper_execution_evidence_bundle_retention_signoff_views(output_root=output_root)
    assert views and views[0].signoff_status == "SIGNED_OFF"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_signoff_status"] == "SIGNED_OFF"
    assert cockpit["latest_evidence_bundle_retention_signoff"]["operator_id"] == "jp"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_retention_signoff_status"] == "SIGNED_OFF"
    assert daily["summary"]["paper_execution_latest_bundle_retention_signed_off_count"] == 1


def test_retention_signoff_blocks_when_verification_failed(tmp_path: Path) -> None:
    output_root, latest_retention_verification_path = _setup_retention_verification(tmp_path)
    raw = json.loads(latest_retention_verification_path.read_text(encoding="utf-8"))
    raw["verification_status"] = "FAIL"
    raw["blockers"] = ["RETENTION_VERIFICATION_FILE_DIGEST_MISMATCH:bundle"]
    raw["artifact_sha256"] = canonical_json_sha256({k: v for k, v in raw.items() if k != "artifact_sha256"})
    latest_retention_verification_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_signoff_artifact(retention_verification_artifact_path=latest_retention_verification_path, output_root=output_root)

    assert artifact.signoff_status == "BLOCKED"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_VERIFICATION_NOT_PASS" in artifact.blockers
    assert "SOURCE_RETENTION_VERIFICATION_BLOCKER:RETENTION_VERIFICATION_FILE_DIGEST_MISMATCH:bundle" in artifact.blockers
