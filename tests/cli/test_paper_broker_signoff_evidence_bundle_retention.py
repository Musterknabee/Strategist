from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import write_paper_execution_evidence_bundle_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import write_paper_execution_evidence_bundle_attestation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure import write_paper_execution_evidence_bundle_closure_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure_verification import write_paper_execution_evidence_bundle_closure_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_drift import write_paper_execution_evidence_bundle_drift_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export import write_paper_execution_evidence_bundle_export_manifest_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export_verification import write_paper_execution_evidence_bundle_export_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention import write_paper_execution_evidence_bundle_retention_receipt_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_verification import write_paper_execution_evidence_bundle_retention_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
from strategy_validator.cli import paper_broker
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_STAGES = ["SELECTED_INTENT", "DRY_RUN", "SUBMISSION", "ORDER_STATUS", "POSITION_SNAPSHOT", "POSITION_RECONCILIATION"]


def _source(path: Path, stage: str) -> str:
    raw = {"schema_version": "test_source/v1", "stage": stage, "ok": True}
    digest = canonical_json_sha256(raw)
    path.write_text(json.dumps({**raw, "artifact_sha256": digest}, sort_keys=True), encoding="utf-8")
    return digest


def _timeline(tmp_path: Path, tracking_id: str = "track-retention-signoff-cli") -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    entries: list[PaperExecutionTimelineEntry] = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        entries.append(PaperExecutionTimelineEntry(stage=stage, stage_order=idx * 10, tracking_id=tracking_id, generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00", artifact_path=str(path), artifact_sha256=digest, status="OK", ok=True, trusted=True, summary_line=f"{stage} trusted"))  # type: ignore[arg-type]
    return entries, PaperExecutionTimelineSummary(event_count=6, stage_count=6, trusted_event_count=6, blocker_count=0, warning_count=0, latest_event_at_utc="2026-05-03T12:06:00+00:00", sequence_status="COMPLETE", completed_stages=list(_STAGES), missing_stages=[])


def _setup(tmp_path: Path) -> tuple[Path, Path]:
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


def test_signoff_evidence_bundle_retention_cli_writes_certificate(tmp_path: Path, capsys) -> None:
    output_root, latest_retention_verification_path = _setup(tmp_path)

    rc = paper_broker.main(["signoff-evidence-bundle-retention", "--retention-verification-artifact", str(latest_retention_verification_path), "--operator-id", "jp", "--decision-note", "retain externally", "--output-root", str(output_root)])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["signoff_status"] == "SIGNED_OFF"
    assert payload["trust_banner"] == "TRUSTED"
    assert payload["operator_id"] == "jp"
    assert payload["retention_verification_artifact_hash_valid"] is True
    assert payload["recomputed_retention_entry_count"] == 7
    assert payload["recomputed_retention_ready_entry_count"] == 7
    artifact_path = Path(payload["artifact"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle_retention_signoff/v1"
    assert artifact["artifact_sha256"] == payload["artifact_sha256"]
    assert Path(payload["history_artifact"]).exists()
