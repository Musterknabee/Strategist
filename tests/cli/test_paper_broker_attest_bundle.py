from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
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


def _setup(tmp_path: Path) -> Path:
    output_root = tmp_path / "artifacts" / "paper_broker"
    timeline = []
    for idx, stage in enumerate(_STAGES, start=1):
        path = tmp_path / f"{idx:02d}_{stage.lower()}.json"
        digest = _source(path, stage)
        timeline.append(PaperExecutionTimelineEntry(stage=stage, stage_order=idx * 10, tracking_id="track-cli-attest", generated_at_utc=f"2026-05-03T12:0{idx}:00+00:00", artifact_path=str(path), artifact_sha256=digest, status="OK", ok=True, trusted=True, summary_line=f"{stage} trusted"))  # type: ignore[arg-type]
    summary = PaperExecutionTimelineSummary(event_count=6, stage_count=6, trusted_event_count=6, blocker_count=0, warning_count=0, latest_event_at_utc="2026-05-03T12:06:00+00:00", sequence_status="COMPLETE", completed_stages=list(_STAGES), missing_stages=[])
    write_paper_execution_evidence_bundle_artifact(timeline=timeline, timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 10, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_verification_artifact(output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 11, tzinfo=timezone.utc))
    write_paper_execution_evidence_bundle_drift_artifact(current_timeline=timeline, current_timeline_summary=summary, output_root=output_root, generated_at_utc=datetime(2026, 5, 3, 12, 12, tzinfo=timezone.utc))
    return output_root


def test_attest_evidence_bundle_cli_writes_keyless_envelope(tmp_path: Path, capsys) -> None:
    output_root = _setup(tmp_path)

    rc = paper_broker.main(["attest-evidence-bundle", "--output-root", str(output_root), "--signer-identity", "cli-test-signer"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["attestation_status"] == "ATTESTED"
    assert payload["trust_banner"] == "TRUSTED"
    assert payload["signature_status"] == "UNSIGNED_KEYLESS_STUB"
    artifact_path = Path(payload["artifact"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_evidence_bundle_attestation/v1"
    assert artifact["envelope"]["signatures"][0]["keyid"] == "cli-test-signer"
