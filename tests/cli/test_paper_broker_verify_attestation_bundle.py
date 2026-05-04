from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import write_paper_execution_evidence_bundle_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_drift import write_paper_execution_evidence_bundle_drift_artifact
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


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        timeline.append(PaperExecutionTimelineEntry(stage=stage, stage_order=idx * 10, tracking_id="track-cli-attest-verify", generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00", artifact_path=str(path), artifact_sha256=digest, status="OK", ok=True, trusted=True, summary_line=f"{stage} trusted"))  # type: ignore[arg-type]
    summary = PaperExecutionTimelineSummary(event_count=6, stage_count=6, trusted_event_count=6, blocker_count=0, warning_count=0, latest_event_at_utc="2026-05-03T12:06:00+00:00", sequence_status="COMPLETE", completed_stages=list(_STAGES), missing_stages=[])
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 10, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 11, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 12, tzinfo=timezone.utc))
    latest_attestation_path, _, _ = write_paper_execution_evidence_bundle_attestation_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 13, tzinfo=timezone.utc))
    return output_root, latest_attestation_path


def test_verify_evidence_bundle_attestation_cli_writes_verification(tmp_path: Path, capsys) -> None:
    output_root, latest_attestation_path = _setup(tmp_path)

    rc = paper_broker.main(["verify-evidence-bundle-attestation", "--attestation-artifact", str(latest_attestation_path), "--output-root", str(output_root)])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verification_status"] == "PASS"
    assert payload["trust_banner"] == "TRUSTED"
    assert payload["artifact_hash_valid"] is True
    assert payload["statement_payload_hash_valid"] is True
    assert payload["keyless_stub_signature_valid"] is True
    assert Path(payload["artifact"]).exists()
