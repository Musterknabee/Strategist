from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane


def test_governance_plane_dispatch_posture_ready_surface_allows_dispatch() -> None:
    result = assess_governance_plane(
        evidence_freshness_status="FRESH",
        evidence_integrity_status="VERIFIED",
        evidence_coverage_status="COMPLETE",
        support_verification_status="VERIFIED",
        support_chain_trust_status="TRUSTED",
        support_chain_remediation_status="NO_REMEDIATION",
        support_chain_remediation_actions=[],
        operator_readiness="READY_FOR_REVIEW",
        surface_label="this strategist surface",
    )
    assert result.governance_plane_dispatch_posture == "DISPATCH_ALLOWED"
    assert result.governance_plane_dispatch_permitted is True


def test_governance_plane_dispatch_posture_blocked_surface_denies_dispatch() -> None:
    result = assess_governance_plane(
        evidence_freshness_status="STALE",
        evidence_integrity_status="UNVERIFIED",
        evidence_coverage_status="MISSING",
        support_verification_status="UNVERIFIED",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        support_chain_remediation_actions=["Repair the support chain before broader use."],
        operator_readiness="HOLD_FOR_REFRESH",
        surface_label="this strategist surface",
    )
    assert result.governance_plane_dispatch_posture == "DISPATCH_BLOCKED"
    assert result.governance_plane_dispatch_permitted is False
    assert any("blocked" in reason.lower() for reason in result.governance_plane_dispatch_reasons)


def test_morning_attestation_carries_dispatch_posture_fields() -> None:
    payload = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T09:00:00Z",
            "universe_label": "GLOBAL_MACRO",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.2,
                    "geopolitical_risk_index": 0.7,
                    "narrative_contradiction_count": 4,
                    "tribunal_belief_conflict": 0.9,
                },
                "microstructure": {
                    "vpin": 0.63,
                    "order_flow_imbalance": 0.04,
                    "spread_variance_zscore": 1.1,
                    "liquidity_thinning_score": 0.72,
                },
                "macro": {
                    "yield_curve_slope_bps": 8.0,
                    "high_yield_credit_spread_bps": 340.0,
                    "equity_bond_correlation": 0.88,
                    "cross_asset_correlation_stress": 0.9,
                    "realized_volatility_zscore": 1.4,
                },
            },
            "strategies": [],
        }
    )
    report = build_oracle_morning_attestation(payload=payload)
    assert report.governance_plane_dispatch_posture in {
        "DISPATCH_ALLOWED",
        "DISPATCH_REVIEW_ONLY",
        "DISPATCH_BLOCKED",
    }
    assert isinstance(report.governance_plane_dispatch_permitted, bool)
    assert report.governance_plane_dispatch_summary_line
