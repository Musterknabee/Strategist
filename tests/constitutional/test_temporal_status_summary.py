from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.application import summarize_temporal_lane_payload
from strategy_validator.cli.oracle_temporal_runners import cmd_summarize_temporal_lane
from strategy_validator.contracts.oracle import OracleSensorRawSemanticInput
from strategy_validator.contracts.oracle_temporal import (
    TemporalCanonicalizationBatchResult,
    TemporalCanonicalizationDayResult,
    TemporalEventLogAppendBatchResult,
    TemporalEventLogAppendDayResult,
    TemporalEvidenceRef,
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
    TemporalSemanticDay,
)


def _manifest() -> TemporalSemanticBatchManifest:
    return TemporalSemanticBatchManifest(
        provider_id="nim-test",
        model_name="minimax-m2.7",
        batch_start_date=datetime(2025, 1, 2, tzinfo=UTC).date(),
        batch_end_date=datetime(2025, 1, 3, tzinfo=UTC).date(),
        days=[
            TemporalSemanticDay(
                point_in_time_date=datetime(2025, 1, 2, tzinfo=UTC).date(),
                trading_session_id="2025-01-02",
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.2,
                    dovish_document_ratio=0.3,
                    geopolitical_headline_share=0.2,
                    contradiction_count=1,
                    belief_conflict_score=0.3,
                ),
                allowed_prefix_digest_sha256="a" * 64,
                citations=[
                    TemporalEvidenceRef(
                        source_id="src-1",
                        source_timestamp_utc=datetime(2025, 1, 2, 8, tzinfo=UTC),
                        exact_quote="market note",
                    )
                ],
            ),
            TemporalSemanticDay(
                point_in_time_date=datetime(2025, 1, 3, tzinfo=UTC).date(),
                trading_session_id="2025-01-03",
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.4,
                    dovish_document_ratio=0.2,
                    geopolitical_headline_share=0.1,
                    contradiction_count=0,
                    belief_conflict_score=0.1,
                ),
                allowed_prefix_digest_sha256="b" * 64,
            ),
        ],
    )



def test_summarize_temporal_lane_payload_reports_operator_status() -> None:
    manifest = _manifest()
    verification = TemporalSemanticBatchVerification(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        status="REJECTED",
        accepted_dates=[datetime(2025, 1, 2, tzinfo=UTC).date()],
        rejected_dates=[datetime(2025, 1, 3, tzinfo=UTC).date()],
    )
    canonicalization = TemporalCanonicalizationBatchResult(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label="SPY",
        output_root="docs/artifacts/oracle_temporal/SPY",
        verification_status="REJECTED",
        canonicalized_dates=[datetime(2025, 1, 2, tzinfo=UTC).date()],
        skipped_dates=[datetime(2025, 1, 3, tzinfo=UTC).date()],
        results=[
            TemporalCanonicalizationDayResult(
                point_in_time_date=datetime(2025, 1, 2, tzinfo=UTC).date(),
                status="CANONICALIZED",
                evidence_verification_status="VERIFIED",
            ),
            TemporalCanonicalizationDayResult(
                point_in_time_date=datetime(2025, 1, 3, tzinfo=UTC).date(),
                status="SKIPPED_REJECTED",
            ),
        ],
    )
    append_report = TemporalEventLogAppendBatchResult(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label="SPY",
        lane_path="docs/artifacts/oracle_temporal/ORACLE_EVENT_LOG.jsonl",
        canonicalization_output_root=canonicalization.output_root,
        canonicalization_verification_status="REJECTED",
        appended_dates=[datetime(2025, 1, 2, tzinfo=UTC).date()],
        skipped_dates=[datetime(2025, 1, 3, tzinfo=UTC).date()],
        results=[
            TemporalEventLogAppendDayResult(
                point_in_time_date=datetime(2025, 1, 2, tzinfo=UTC).date(),
                status="APPENDED",
            ),
            TemporalEventLogAppendDayResult(
                point_in_time_date=datetime(2025, 1, 3, tzinfo=UTC).date(),
                status="SKIPPED_REJECTED",
            ),
        ],
        summary_line="append ok",
    )

    payload = summarize_temporal_lane_payload(
        manifest,
        universe_label="SPY",
        verification=verification,
        canonicalization=canonicalization,
        append_report=append_report,
    )

    status = payload["temporal_lane_status"]
    assert status["extraction_days"] == 2
    assert status["verified_days"] == 1
    assert status["rejected_days"] == 1
    assert status["canonicalized_days"] == 1
    assert status["appended_days"] == 1
    assert "Rejected dates remain outside the canonical truth spine" in "\n".join(status["operator_lines"])



def test_cli_summarize_temporal_lane_writes_payload(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest()
    verification = TemporalSemanticBatchVerification(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        status="VERIFIED",
        accepted_dates=[datetime(2025, 1, 2, tzinfo=UTC).date(), datetime(2025, 1, 3, tzinfo=UTC).date()],
        rejected_dates=[],
    )
    manifest_path = tmp_path / "manifest.json"
    verification_path = tmp_path / "verification.json"
    output_path = tmp_path / "status.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    verification_path.write_text(json.dumps(verification.model_dump(mode="json"), indent=2), encoding="utf-8")

    printed = {}

    def _capture(payload, output):
        printed["payload"] = payload
        printed["output"] = output
        Path(output).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    monkeypatch.setattr("strategy_validator.cli.oracle_temporal_runners.print_or_write_payload", _capture)

    class NS:
        manifest = str(manifest_path)
        universe_label = "SPY"
        verification = str(verification_path)
        canonicalization = ""
        append_report = ""
        output = str(output_path)

    assert cmd_summarize_temporal_lane(NS()) == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["temporal_lane_status"]["verified_days"] == 2
    assert payload["temporal_lane_status"]["append_lane_path"] is None
