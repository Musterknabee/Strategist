from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_stack_evidence import build_oracle_strategic_stack_evidence_bundle
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report


_NOW = datetime(2026, 4, 14, 1, 0, tzinfo=timezone.utc)


def _payload(*, ts: str = "2026-04-13T08:10:00Z", universe: str = "US_EQ_FACTORS") -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": ts,
            "universe_label": universe,
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": -0.2,
                    "geopolitical_risk_index": 0.12,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.08,
                },
                "microstructure": {
                    "vpin": 0.18,
                    "order_flow_imbalance": 0.16,
                    "spread_variance_zscore": -0.2,
                    "liquidity_thinning_score": 0.10,
                },
                "macro": {
                    "yield_curve_slope_bps": 100.0,
                    "high_yield_credit_spread_bps": 275.0,
                    "equity_bond_correlation": -0.25,
                    "cross_asset_correlation_stress": 0.14,
                    "realized_volatility_zscore": -0.3,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-a",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.91,
                    "cpcv_lower_bound": 0.28,
                    "realized_live_sharpe": 0.66,
                    "recent_win_rate": 0.58,
                    "drawdown_fraction": 0.06,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )


@pytest.mark.constitutional
def test_strategic_reports_propagate_canonical_run_identity() -> None:
    payload = _payload()
    fusion = build_oracle_strategic_fusion_report(payload, now_utc=_NOW)
    posterior = build_strategy_health_posterior_report(payload, fusion, now_utc=_NOW)
    briefing = build_oracle_strategic_briefing(payload, fusion_report=fusion, posterior_report=posterior, now_utc=_NOW)

    assert fusion.input_timestamp_utc == payload.generated_for_utc
    assert posterior.input_timestamp_utc == payload.generated_for_utc
    assert briefing.input_timestamp_utc == payload.generated_for_utc
    assert fusion.oracle_run_id == posterior.oracle_run_id == briefing.oracle_run_id


@pytest.mark.constitutional
def test_strategic_stack_evidence_carries_briefing_run_identity(tmp_path) -> None:
    payload = _payload()
    input_path = tmp_path / "input.json"
    briefing_path = tmp_path / "briefing.json"
    input_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    briefing = build_oracle_strategic_briefing(payload, now_utc=_NOW)
    briefing_path.write_text(briefing.model_dump_json(indent=2), encoding="utf-8")

    manifest, _ = build_oracle_strategic_stack_evidence_bundle(
        input_path=input_path,
        briefing_report_path=briefing_path,
        repo_root=tmp_path,
        now_utc=_NOW,
    )

    assert manifest.oracle_run_id == briefing.oracle_run_id
    assert manifest.input_timestamp_utc == payload.generated_for_utc
