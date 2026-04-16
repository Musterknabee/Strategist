from datetime import datetime, timezone

from strategy_validator.validator.oracle_advisory import OracleAdvisoryInput, build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import (
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)


def test_dispatch_envelope_exposes_claim_key():
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)
    review = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=24,
        priority_score=72,
        queue_key="HEIGHTENED_REVIEW_QUEUE::READINESS::RESTRICTING",
    )
    routing = materialize_governance_routing_envelope(
        review_target="HEIGHTENED_REVIEW_QUEUE",
        review_sla_hours=24,
        queue_key="HEIGHTENED_REVIEW_QUEUE::READINESS::RESTRICTING",
        route_vector="priority=ELEVATED_PRIORITY|review_target=HEIGHTENED_REVIEW_QUEUE",
        review_envelope=review,
    )
    dispatch = materialize_governance_dispatch_envelope(
        queue_key="HEIGHTENED_REVIEW_QUEUE::READINESS::RESTRICTING",
        route_sha256="a" * 64,
        review_envelope=review,
        routing_envelope=routing,
        dispatch_posture="DISPATCH_REVIEW_ONLY",
        dispatch_permitted=True,
        dispatch_summary_line="Dispatch posture: DISPATCH_REVIEW_ONLY; handoff is permitted only into governed review queues.",
        dispatch_reasons=["Dispatch is restricted to review-controlled handoff rather than routine downstream flow."],
        priority_band="ELEVATED_PRIORITY",
        now_utc=issued_at,
    )
    assert dispatch.governance_plane_dispatch_claim_key.startswith(
        "HEIGHTENED_REVIEW_QUEUE::READINESS::RESTRICTING::2026-04-15T08:00:00+00:00::"
    )
    assert dispatch.governance_plane_dispatch_sha256 in dispatch.governance_plane_dispatch_claim_key
    assert "review_due_by_utc=2026-04-15T08:00:00+00:00" in dispatch.governance_plane_dispatch_vector
    assert "review_sort_key=" in dispatch.governance_plane_dispatch_vector
    assert "dispatch_claim_urgency=CLAIM_SOON" in dispatch.governance_plane_dispatch_vector


def test_attestation_carries_dispatch_claim_key():
    advisory_input = OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T09:00:00Z",
            "universe_label": "unit-test",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.1,
                    "geopolitical_risk_index": 0.2,
                    "narrative_contradiction_count": 0,
                    "tribunal_belief_conflict": 0.05,
                },
                "microstructure": {
                    "vpin": 0.2,
                    "order_flow_imbalance": 0.1,
                    "spread_variance_zscore": 0.1,
                    "liquidity_thinning_score": 0.1,
                },
                "macro": {
                    "yield_curve_slope_bps": 50.0,
                    "high_yield_credit_spread_bps": 300.0,
                    "equity_bond_correlation": 0.1,
                    "cross_asset_correlation_stress": 0.1,
                    "realized_volatility_zscore": 0.2,
                },
            },
            "strategies": [],
        }
    )
    report = build_oracle_morning_attestation(advisory_input)
    assert report.governance_plane_dispatch_claim_key
    assert report.governance_plane_queue_key in report.governance_plane_dispatch_claim_key
    due = report.governance_plane_review_due_by_utc.isoformat()
    assert due in report.governance_plane_dispatch_claim_key
    assert report.governance_plane_dispatch_sha256 in report.governance_plane_dispatch_claim_key
