from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import (
    build_oracle_morning_attestation,
    render_oracle_morning_attestation_markdown,
)


@pytest.mark.constitutional
def test_oracle_attestation_flags_liquidity_stress_and_canary_review() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T07:30:00Z",
            "universe_label": "US_EQ_LIQUID",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 1.4,
                    "geopolitical_risk_index": 0.82,
                    "narrative_contradiction_count": 1,
                    "tribunal_belief_conflict": 0.22,
                },
                "microstructure": {
                    "vpin": 0.84,
                    "order_flow_imbalance": -0.61,
                    "spread_variance_zscore": 2.1,
                    "liquidity_thinning_score": 0.88,
                },
                "macro": {
                    "yield_curve_slope_bps": -55.0,
                    "high_yield_credit_spread_bps": 470.0,
                    "equity_bond_correlation": 0.44,
                    "cross_asset_correlation_stress": 0.79,
                    "realized_volatility_zscore": 2.4,
                },
            },
            "strategies": [
                {
                    "strategy_id": "meanrev-a",
                    "strategy_type": "MEAN_REVERSION",
                    "prior_edge_confidence": 0.67,
                    "deflated_sharpe_ratio": 0.88,
                    "cpcv_lower_bound": 0.45,
                    "realized_live_sharpe": -0.10,
                    "recent_win_rate": 0.39,
                    "drawdown_fraction": 0.14,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )
    attestation = build_oracle_morning_attestation(
        payload=payload,
        now_utc=datetime(2026, 4, 13, 7, 35, tzinfo=timezone.utc),
    )
    assert attestation.execution_authority == "ADVISORY_ONLY"
    assert attestation.dominant_regime in {"LIQUIDITY_STRESS", "RISK_OFF_HIGH_VOL"}
    assert attestation.recommended_global_action in {"CANARY_REVIEW", "DEFENSIVE_POSTURE"}
    assert attestation.strategy_advisories[0].action in {"CANARY", "HIBERNATE"}
    rendered = render_oracle_morning_attestation_markdown(attestation)
    assert "ORACLE MORNING ATTESTATION" in rendered
    assert "Execution authority: ADVISORY_ONLY" in rendered


@pytest.mark.constitutional
def test_epistemic_unknown_unknowns_remains_advisory_only() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-13T08:00:00Z",
            "universe_label": "GLOBAL_MACRO",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.1,
                    "geopolitical_risk_index": 0.71,
                    "narrative_contradiction_count": 5,
                    "tribunal_belief_conflict": 0.92,
                },
                "microstructure": {
                    "vpin": 0.62,
                    "order_flow_imbalance": 0.04,
                    "spread_variance_zscore": 1.4,
                    "liquidity_thinning_score": 0.75,
                },
                "macro": {
                    "yield_curve_slope_bps": 5.0,
                    "high_yield_credit_spread_bps": 360.0,
                    "equity_bond_correlation": 0.92,
                    "cross_asset_correlation_stress": 0.93,
                    "realized_volatility_zscore": 1.8,
                },
            },
            "strategies": [],
        }
    )
    attestation = build_oracle_morning_attestation(payload=payload)
    assert attestation.epistemic_uncertainty.status == "UNKNOWN_UNKNOWNS"
    assert attestation.epistemic_uncertainty.advisory_only is True
    assert attestation.recommended_global_action == "DEFENSIVE_POSTURE"
    assert any("manual review" in item.lower() for item in attestation.operator_actions)


@pytest.mark.constitutional
def test_oracle_advisory_cli_emits_json_and_markdown(tmp_path: Path) -> None:
    payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": -0.2,
                "geopolitical_risk_index": 0.10,
                "narrative_contradiction_count": 0,
                "tribunal_belief_conflict": 0.05,
            },
            "microstructure": {
                "vpin": 0.21,
                "order_flow_imbalance": 0.18,
                "spread_variance_zscore": -0.1,
                "liquidity_thinning_score": 0.12,
            },
            "macro": {
                "yield_curve_slope_bps": 95.0,
                "high_yield_credit_spread_bps": 280.0,
                "equity_bond_correlation": -0.35,
                "cross_asset_correlation_stress": 0.08,
                "realized_volatility_zscore": -0.45,
            },
        },
        "strategies": [
            {
                "strategy_id": "trend-b",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.72,
                "deflated_sharpe_ratio": 0.94,
                "cpcv_lower_bound": 0.30,
                "realized_live_sharpe": 0.58,
                "recent_win_rate": 0.57,
                "drawdown_fraction": 0.04,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }
    input_path = tmp_path / "oracle_input.json"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    from strategy_validator.cli.rollout_ops import main

    output_path = tmp_path / "ORACLE_MORNING_ATTESTATION.json"
    markdown_path = tmp_path / "ORACLE_MORNING_ATTESTATION.md"
    rc = main([
        "oracle-advisory",
        str(input_path),
        "--output",
        str(output_path),
        "--markdown-output",
        str(markdown_path),
    ])
    assert rc == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["execution_authority"] == "ADVISORY_ONLY"
    assert data["recommended_global_action"] == "OBSERVE"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "ORACLE MORNING ATTESTATION" in markdown
