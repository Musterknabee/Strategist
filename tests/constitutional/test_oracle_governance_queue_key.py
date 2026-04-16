from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane


def test_governance_queue_key_tracks_review_target_priority_and_primary_driver():
    assessment = assess_governance_plane(
        evidence_freshness_status="STALE",
        evidence_integrity_status="UNVERIFIED",
        evidence_coverage_status="MISSING",
        support_verification_status="UNVERIFIED",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        operator_readiness="HOLD_FOR_REFRESH",
        surface_label="fusion surface",
    )
    assert assessment.governance_plane_queue_key == (
        f"{assessment.governance_plane_review_target}::"
        f"{assessment.governance_plane_priority_band}::"
        f"{assessment.governance_plane_primary_dimension}::"
        f"{assessment.governance_plane_primary_severity}"
    )
    assert f"queue_key={assessment.governance_plane_queue_key}" in assessment.governance_plane_vector


@pytest.mark.constitutional
def test_oracle_attestation_carries_governance_queue_key():
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
    now_utc = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
    attestation = build_oracle_morning_attestation(payload=payload, now_utc=now_utc)
    assert attestation.governance_plane_queue_key
    assert attestation.governance_plane_review_target in attestation.governance_plane_queue_key
    assert attestation.governance_plane_priority_band in attestation.governance_plane_queue_key
