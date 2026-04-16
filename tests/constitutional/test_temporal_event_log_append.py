from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from strategy_validator.application import append_temporal_canonicalization_to_event_log_payload, canonicalize_temporal_semantic_batch_payload
from strategy_validator.contracts.oracle import OracleSensorRawMacroInput, OracleSensorRawMicrostructureInput
from strategy_validator.contracts.oracle_temporal import TemporalEvidenceRef, TemporalSemanticBatchManifest, TemporalSemanticDay
from strategy_validator.validator.oracle_event_log import _read_jsonl_models
from strategy_validator.validator.rollout_ops_evidence import generate_snapshot_signing_keypair


def _manifest() -> TemporalSemanticBatchManifest:
    good = date(2026, 1, 5)
    bad = date(2026, 1, 6)
    return TemporalSemanticBatchManifest(
        provider_kind="NVIDIA_NIM",
        provider_id="nim-test",
        model_name="minimaxai/minimax-m2.7",
        batch_start_date=good,
        batch_end_date=bad,
        days=[
            TemporalSemanticDay(
                point_in_time_date=good,
                trading_session_id="XNYS:2026-01-05",
                semantic_raw={
                    "hawkish_document_ratio": 0.45,
                    "dovish_document_ratio": 0.15,
                    "geopolitical_headline_share": 0.10,
                    "contradiction_count": 1,
                    "belief_conflict_score": 0.20,
                },
                allowed_prefix_digest_sha256="prefix-1",
                provider_response_sha256="resp-1",
                citations=[],
            ),
            TemporalSemanticDay(
                point_in_time_date=bad,
                trading_session_id="XNYS:2026-01-06",
                semantic_raw={
                    "hawkish_document_ratio": 0.10,
                    "dovish_document_ratio": 0.55,
                    "geopolitical_headline_share": 0.20,
                    "contradiction_count": 0,
                    "belief_conflict_score": 0.10,
                },
                allowed_prefix_digest_sha256="prefix-2",
                provider_response_sha256="resp-2",
                citations=[
                    TemporalEvidenceRef(
                        source_id="future-doc",
                        source_timestamp_utc="2026-01-07T00:00:01Z",
                        exact_quote="future note",
                    )
                ],
            ),
        ],
    )


def _macro(good: date, bad: date):
    return {
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
    }


def _micro(good: date, bad: date):
    return {
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
    }


def test_append_temporal_canonicalization_to_event_log_appends_verified_days_only(tmp_path: Path) -> None:
    manifest = _manifest()
    good = date(2026, 1, 5)
    bad = date(2026, 1, 6)
    private_key = tmp_path / "keys" / "oracle_private.pem"
    public_key = tmp_path / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    private_key = tmp_path / "keys" / "oracle_private.pem"
    public_key = tmp_path / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    payload = canonicalize_temporal_semantic_batch_payload(
        manifest,
        universe_label="US_EQ",
        output_root=tmp_path / "docs" / "artifacts" / "oracle_temporal",
        repo_root=tmp_path,
        macro_by_date=_macro(good, bad),
        microstructure_by_date=_micro(good, bad),
        expected_dates=[good, bad],
        allowed_prefix_digests_by_date={good: "prefix-1", bad: "prefix-2"},
        signing_private_key_path=private_key,
        public_key_path=public_key,
    )
    canonicalization = payload["canonicalization"]
    append_payload = append_temporal_canonicalization_to_event_log_payload(
        canonicalization,
        lane_path=tmp_path / "docs" / "artifacts" / "ORACLE_EVENT_LOG.jsonl",
        repo_root=tmp_path,
    )
    report = append_payload["event_log_append"]
    assert report["appended_dates"] == [good.isoformat()]
    assert report["skipped_dates"] == [bad.isoformat()]
    rows = _read_jsonl_models(tmp_path / "docs" / "artifacts" / "ORACLE_EVENT_LOG.jsonl")
    assert len(rows) == 1
    assert rows[0].evidence_status == "VERIFIED"


def test_append_temporal_canonicalization_can_fail_closed_on_skips(tmp_path: Path) -> None:
    manifest = _manifest()
    good = date(2026, 1, 5)
    bad = date(2026, 1, 6)
    private_key = tmp_path / "keys" / "oracle_private.pem"
    public_key = tmp_path / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    payload = canonicalize_temporal_semantic_batch_payload(
        manifest,
        universe_label="US_EQ",
        output_root=tmp_path / "docs" / "artifacts" / "oracle_temporal",
        repo_root=tmp_path,
        macro_by_date=_macro(good, bad),
        microstructure_by_date=_micro(good, bad),
        expected_dates=[good, bad],
        allowed_prefix_digests_by_date={good: "prefix-1", bad: "prefix-2"},
        signing_private_key_path=private_key,
        public_key_path=public_key,
    )
    try:
        append_temporal_canonicalization_to_event_log_payload(
            payload["canonicalization"],
            lane_path=tmp_path / "docs" / "artifacts" / "ORACLE_EVENT_LOG.jsonl",
            repo_root=tmp_path,
            require_complete_success=True,
        )
    except ValueError as exc:
        assert "complete canonicalization success" in str(exc)
    else:
        raise AssertionError("expected fail-closed append to reject skipped dates")
