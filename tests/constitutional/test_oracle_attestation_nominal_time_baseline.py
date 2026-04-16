from __future__ import annotations

from datetime import UTC, datetime

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation


def _payload() -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate({
        "generated_for_utc": datetime(2026, 4, 14, 8, 0, tzinfo=UTC),
        "universe_label": "test-universe",
        "sensors": {
            "semantic": {"tribunal_belief_conflict": 0.15, "narrative_contradiction_count": 1},
            "microstructure": {"liquidity_thinning_score": 0.2, "spread_variance_zscore": 0.1},
            "macro": {
                "yield_curve_slope_bps": 12.0,
                "high_yield_credit_spread_bps": 310.0,
                "equity_bond_correlation": -0.2,
                "cross_asset_correlation_stress": 0.2,
                "realized_volatility_zscore": 0.1,
            },
        },
        "strategies": [],
    })


def test_attestation_default_clock_uses_payload_generation_time_for_nominal_baseline() -> None:
    report = build_oracle_morning_attestation(_payload())
    assert report.evidence_freshness_status == "FRESH"
    assert report.support_chain_trust_status == "TRUSTED"
    assert report.support_chain_remediation_status == "NO_REMEDIATION"
    assert report.operator_reliance_posture == "ROUTINE_ADVISORY"
    assert report.operator_escalation_lane == "STANDARD_OPERATOR_FLOW"
    assert report.propagation_posture == "DOWNSTREAM_PROPAGATION_ALLOWED"
    assert report.automation_posture == "AUTOMATION_ELIGIBLE"
