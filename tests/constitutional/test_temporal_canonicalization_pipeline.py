from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.application import canonicalize_temporal_semantic_batch_payload
from strategy_validator.contracts.oracle import (
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
    OracleSensorRawSemanticInput,
)
from strategy_validator.contracts.oracle_temporal import (
    TemporalEvidenceRef,
    TemporalSemanticBatchManifest,
    TemporalSemanticDay,
)
from strategy_validator.validator.oracle_temporal_pipeline import canonicalize_temporal_semantic_batch
from strategy_validator.validator.rollout_ops_evidence import generate_snapshot_signing_keypair


@pytest.mark.constitutional
def test_canonicalize_temporal_semantic_batch_emits_daily_oracle_artifacts(tmp_path: Path) -> None:
    private_key = tmp_path / "keys" / "oracle_private.pem"
    public_key = tmp_path / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    pt_date = date(2026, 1, 5)
    manifest = TemporalSemanticBatchManifest(
        provider_kind="NVIDIA_NIM",
        provider_id="nim-1",
        model_name="minimaxai/minimax-m2.7",
        batch_start_date=pt_date,
        batch_end_date=pt_date,
        days=[
            TemporalSemanticDay(
                point_in_time_date=pt_date,
                trading_session_id="XNYS:2026-01-05",
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.45,
                    dovish_document_ratio=0.15,
                    geopolitical_headline_share=0.10,
                    contradiction_count=1,
                    belief_conflict_score=0.20,
                ),
                allowed_prefix_digest_sha256="prefix-1",
                provider_response_sha256="resp-1",
                citations=[
                    TemporalEvidenceRef(
                        source_id="doc-1",
                        source_timestamp_utc=datetime(2026, 1, 5, 11, tzinfo=timezone.utc),
                        exact_quote="same day note",
                    )
                ],
            )
        ],
    )

    report = canonicalize_temporal_semantic_batch(
        manifest,
        universe_label="US_EQ",
        output_root=tmp_path / "docs" / "artifacts" / "oracle_temporal",
        repo_root=tmp_path,
        macro_by_date={
            pt_date: OracleSensorRawMacroInput(
                yield_curve_slope_bps=-25.0,
                high_yield_credit_spread_bps=390.0,
                equity_bond_correlation_20d=-0.25,
                cross_asset_correlation_20d=0.35,
                realized_volatility_20d=0.20,
                realized_volatility_252d=0.18,
            )
        },
        microstructure_by_date={
            pt_date: OracleSensorRawMicrostructureInput(
                buy_volume=1200.0,
                sell_volume=900.0,
                median_spread_bps=7.5,
                baseline_spread_bps=5.0,
                top_book_depth_usd=1_800_000.0,
                baseline_top_book_depth_usd=2_000_000.0,
                toxic_flow_ratio=0.25,
            )
        },
        signing_private_key_path=private_key,
        public_key_path=public_key,
    )

    assert report.verification_status == "VERIFIED"
    assert report.canonicalized_dates == [pt_date]
    day = report.results[0]
    assert day.status == "CANONICALIZED"
    assert day.evidence_verification_status == "VERIFIED"
    for rel in [
        day.sensor_input_path,
        day.sensor_report_path,
        day.advisory_input_path,
        day.attestation_path,
        day.markdown_path,
        day.evidence_manifest_path,
        day.dsse_path,
        day.evidence_verification_path,
    ]:
        assert rel is not None
        assert (tmp_path / rel).exists(), rel


@pytest.mark.constitutional
def test_canonicalize_temporal_semantic_batch_skips_rejected_dates_and_application_surface_returns_payload(tmp_path: Path) -> None:
    good = date(2026, 1, 5)
    bad = date(2026, 1, 6)
    manifest = TemporalSemanticBatchManifest(
        provider_kind="NVIDIA_NIM",
        provider_id="nim-1",
        model_name="minimaxai/minimax-m2.7",
        batch_start_date=good,
        batch_end_date=bad,
        days=[
            TemporalSemanticDay(
                point_in_time_date=good,
                trading_session_id="XNYS:2026-01-05",
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.45,
                    dovish_document_ratio=0.15,
                    geopolitical_headline_share=0.10,
                    contradiction_count=1,
                    belief_conflict_score=0.20,
                ),
                allowed_prefix_digest_sha256="prefix-1",
                provider_response_sha256="resp-1",
                citations=[],
            ),
            TemporalSemanticDay(
                point_in_time_date=bad,
                trading_session_id="XNYS:2026-01-06",
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.10,
                    dovish_document_ratio=0.55,
                    geopolitical_headline_share=0.20,
                    contradiction_count=0,
                    belief_conflict_score=0.10,
                ),
                allowed_prefix_digest_sha256="prefix-2",
                provider_response_sha256="resp-2",
                citations=[
                    TemporalEvidenceRef(
                        source_id="future-doc",
                        source_timestamp_utc=datetime(2026, 1, 7, 0, 0, 1, tzinfo=timezone.utc),
                        exact_quote="future note",
                    )
                ],
            ),
        ],
    )

    payload = canonicalize_temporal_semantic_batch_payload(
        manifest,
        universe_label="US_EQ",
        output_root=tmp_path / "docs" / "artifacts" / "oracle_temporal",
        repo_root=tmp_path,
        macro_by_date={
            good: OracleSensorRawMacroInput(
                yield_curve_slope_bps=-25.0,
                high_yield_credit_spread_bps=390.0,
                equity_bond_correlation_20d=-0.25,
                cross_asset_correlation_20d=0.35,
                realized_volatility_20d=0.20,
                realized_volatility_252d=0.18,
            ),
            bad: OracleSensorRawMacroInput(
                yield_curve_slope_bps=-20.0,
                high_yield_credit_spread_bps=395.0,
                equity_bond_correlation_20d=-0.20,
                cross_asset_correlation_20d=0.30,
                realized_volatility_20d=0.21,
                realized_volatility_252d=0.18,
            ),
        },
        microstructure_by_date={
            good: OracleSensorRawMicrostructureInput(
                buy_volume=1200.0,
                sell_volume=900.0,
                median_spread_bps=7.5,
                baseline_spread_bps=5.0,
                top_book_depth_usd=1_800_000.0,
                baseline_top_book_depth_usd=2_000_000.0,
                toxic_flow_ratio=0.25,
            ),
            bad: OracleSensorRawMicrostructureInput(
                buy_volume=1000.0,
                sell_volume=1100.0,
                median_spread_bps=9.0,
                baseline_spread_bps=5.0,
                top_book_depth_usd=1_600_000.0,
                baseline_top_book_depth_usd=2_000_000.0,
                toxic_flow_ratio=0.35,
            ),
        },
        expected_dates=[good, bad],
        allowed_prefix_digests_by_date={good: "prefix-1", bad: "prefix-2"},
    )

    report = payload["canonicalization"]
    assert payload["idempotency_key"]
    assert report["verification_status"] == "REJECTED"
    assert report["canonicalized_dates"] == [good.isoformat()]
    assert report["skipped_dates"] == [bad.isoformat()]
    statuses = {item["point_in_time_date"]: item["status"] for item in report["results"]}
    assert statuses[good.isoformat()] == "CANONICALIZED"
    assert statuses[bad.isoformat()] == "SKIPPED_REJECTED"
