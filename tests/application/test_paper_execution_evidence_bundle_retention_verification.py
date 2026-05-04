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
from strategy_validator.application.paper_execution_evidence_bundle_retention_verification import (
    read_paper_execution_evidence_bundle_retention_verification_views,
    write_paper_execution_evidence_bundle_retention_verification_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_STAGES = ["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"]


def _source(path: Path, stage: str) -> str:
    raw = {"schema_version": "test_source/v1", "stage": stage, "ok": True}
    digest = canonical_json_sha256(raw)
    path.write_text(json.dumps({**raw, "artifact_sha256": digest}, sort_keys=True), encoding="utf-8")
    return digest


def _timeline(tmp_path: Path, tracking_id: str = "track-retention-verify") -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    entries: list[PaperExecutionTimelineEntry] = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        entries.append(PaperExecutionTimelineEntry(stage=stage, stage_order=idx * 10, tracking_id=tracking_id, generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00", artifact_path=str(path), artifact_sha256=digest, status="OK", ok=True, trusted=True, summary_line=f"{stage} trusted"))  # type: ignore[arg-type]
    return entries, PaperExecutionTimelineSummary(event_count=6, stage_count=6, trusted_event_count=6, blocker_count=0, warning_count=0, latest_event_at_utc="2026-05-03T12:06:00+00:00", sequence_status="COMPLETE", completed_stages=list(_STAGES), missing_stages=[])


def _setup_retention_receipt(tmp_path: Path) -> tuple[Path, Path]:
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
    return output_root, latest_retention_receipt_path


def test_retention_verification_passes_and_surfaces(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB", str(tmp_path / "ledger.sqlite3"))
    output_root, latest_retention_receipt_path = _setup_retention_receipt(tmp_path)

    latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_verification_artifact(retention_receipt_artifact_path=latest_retention_receipt_path, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 20, tzinfo=timezone.utc))

    assert latest_path.exists()
    assert history_path.exists()
    assert artifact.verification_status == "PASS"
    assert artifact.trust_banner == "TRUSTED"
    assert artifact.retention_receipt_hash_valid is True
    assert artifact.retention_index_hash_valid is True
    assert artifact.recomputed_retention_entry_count == 7
    assert artifact.recomputed_retention_ready_entry_count == 7
    assert artifact.missing_entry_count == 0
    assert artifact.digest_mismatch_entry_count == 0
    assert all(entry.verification_digest_valid for entry in artifact.entries)

    views = read_paper_execution_evidence_bundle_retention_verification_views(output_root=output_root)
    assert views and views[0].verification_status == "PASS"

    cockpit = build_ui_paper_execution_cockpit_payload(repo_root=tmp_path)
    assert cockpit["summary"]["latest_evidence_bundle_retention_verification_status"] == "PASS"
    assert cockpit["latest_evidence_bundle_retention_verification"]["trust_banner"] == "TRUSTED"

    daily = build_ui_daily_operator_run_payload(repo_root=tmp_path, database_path=str(tmp_path / "ledger.sqlite3"))
    paper = next(component for component in daily["components"] if component["component_id"] == "paper_execution")
    assert paper["summary"]["latest_evidence_bundle_retention_verification_status"] == "PASS"
    assert daily["summary"]["paper_execution_latest_bundle_retention_verified_count"] == 1


def test_retention_verification_blocks_when_retained_file_tampered_after_receipt(tmp_path: Path) -> None:
    output_root, latest_retention_receipt_path = _setup_retention_receipt(tmp_path)
    receipt_raw = json.loads(latest_retention_receipt_path.read_text(encoding="utf-8"))
    bundle_entry = next(entry for entry in receipt_raw["entries"] if entry["kind"] == "bundle")
    bundle_path = Path(bundle_entry["artifact_path"])
    bundle_path.write_text(bundle_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    _, _, artifact = write_paper_execution_evidence_bundle_retention_verification_artifact(retention_receipt_artifact_path=latest_retention_receipt_path, output_root=output_root)

    assert artifact.verification_status == "FAIL"
    assert artifact.trust_banner == "UNTRUSTED"
    assert "RETENTION_VERIFICATION_FILE_DIGEST_MISMATCH:bundle" in artifact.blockers
    assert "RETENTION_VERIFICATION_SIZE_MISMATCH:bundle" in artifact.blockers
    bundle_verification = next(entry for entry in artifact.entries if entry.kind == "bundle")
    assert bundle_verification.present is True
    assert bundle_verification.verification_digest_valid is False
