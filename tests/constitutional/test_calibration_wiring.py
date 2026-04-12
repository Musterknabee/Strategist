"""Calibration mode selection and artifact provenance."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest


def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1",
        cost_model_version="v1",
        calendar_version="v1",
    )


def _exp(eid: str, **bundle_kw) -> ExperimentManifest:
    bundle = EvidenceBundle(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        decoy_survival_passed=True,
        decoy_suite_version="v1",
        decoy_coverage=1.0,
        cpcv_passed=True,
        cpcv_folds=5,
        cpcv_path_coverage=1.0,
        cpcv_path_stability=0.1,
        incrementality_significant=True,
        dsr_estimate=0.5,
        pbo_estimate=0.1,
        **bundle_kw,
    )
    return ExperimentManifest(
        experiment_id=eid,
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
        state=PromotionState.QUARANTINED,
    )


@pytest.mark.constitutional
def test_calibrated_mode_loads_multiplier_from_artifact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    art = tmp_path / "cal.json"
    art.write_text(
        json.dumps(
            {
                "calibration_schema_version": "1.0.0",
                "dataset_fingerprint": "0" * 8,
                "model_version": "empirical_sqrt_v1",
                "nonlinear_sqrt_multiplier": 900.0,
                "fitted_at_utc": "2026-04-12T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", str(art))

    exp = _exp("CAL-1")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="CAL-1",
            evidence_type=EvidenceType.COST_SUMMARY,
            timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
            payload={
                "benchmark_delta": 0.5,
                "benchmark_passed": True,
                "benchmark_id": "L1_BMK",
                "benchmark_version": "bench-v1",
                "strategy_return": 0.05,
                "benchmark_return": 0.02,
                "horizon": "1y",
                "estimated_trade_notional": 1000.0,
                "estimated_participation_rate": 0.01,
            },
            source_module="t",
            checksum="abc",
        )
    ]
    adjudicate(exp, evidence)
    rep = exp.promotion_history[-1].execution_report
    assert rep.impact_model_mode == "EMPIRICAL_CALIBRATED"
    assert rep.impact_calibration_metadata is not None
    assert rep.impact_calibration_metadata.nonlinear_sqrt_multiplier == 900.0
    assert rep.impact_calibration_metadata.impact_model_kind == "SQRT_MULTIPLIER"
    import math

    assert rep.nonlinear_impact_bps == math.sqrt(0.01) * 900.0


@pytest.mark.constitutional
def test_calibrated_empirical_curve_overrides_sqrt(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    art = tmp_path / "curve_cal.json"
    art.write_text(
        json.dumps(
            {
                "calibration_schema_version": "1.0.0",
                "dataset_fingerprint": "0" * 8,
                "model_version": "empirical_curve_v1",
                "nonlinear_sqrt_multiplier": 999.0,
                "fitted_at_utc": "2026-04-12T00:00:00+00:00",
                "empirical_participation_curve": [
                    {"participation_rate": 0.0, "impact_bps": 0.0},
                    {"participation_rate": 0.01, "impact_bps": 50.0},
                    {"participation_rate": 0.05, "impact_bps": 200.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", str(art))

    exp = _exp("CAL-CURVE")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="CAL-CURVE",
            evidence_type=EvidenceType.COST_SUMMARY,
            timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
            payload={
                "benchmark_delta": 0.5,
                "benchmark_passed": True,
                "benchmark_id": "L1_BMK",
                "benchmark_version": "bench-v1",
                "strategy_return": 0.05,
                "benchmark_return": 0.02,
                "horizon": "1y",
                "estimated_trade_notional": 1000.0,
                "estimated_participation_rate": 0.01,
            },
            source_module="t",
            checksum="abc",
        )
    ]
    adjudicate(exp, evidence)
    rep = exp.promotion_history[-1].execution_report
    assert rep.impact_model_mode == "EMPIRICAL_CALIBRATED"
    assert rep.impact_calibration_metadata is not None
    assert rep.impact_calibration_metadata.impact_model_kind == "EMPIRICAL_CURVE"
    assert rep.impact_calibration_metadata.empirical_curve_point_count == 3
    assert rep.nonlinear_impact_bps == 50.0


@pytest.mark.constitutional
def test_calibrated_mode_without_artifact_fails_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL", "CALIBRATED")
    monkeypatch.delenv("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH", raising=False)

    exp = _exp("CAL-2")
    evidence = [
        Evidence(
            evidence_id="e1",
            experiment_id="CAL-2",
            evidence_type=EvidenceType.COST_SUMMARY,
            timestamp=datetime(2026, 4, 1, tzinfo=timezone.utc),
            payload={
                "benchmark_delta": 0.5,
                "benchmark_passed": True,
                "benchmark_id": "L1_BMK",
                "benchmark_version": "bench-v1",
                "strategy_return": 0.05,
                "benchmark_return": 0.02,
                "horizon": "1y",
                "estimated_trade_notional": 1000.0,
                "estimated_participation_rate": 0.01,
            },
            source_module="t",
            checksum="abc",
        )
    ]
    adjudicate(exp, evidence)
    rep = exp.promotion_history[-1].execution_report
    assert rep.impact_model_mode == "PROVISIONAL"
    assert "CALIBRATION_ARTIFACT_PATH_MISSING" in (rep.failure_reason or "")
