from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_governance_plane import materialize_governance_review_envelope


def test_governance_review_envelope_is_stable() -> None:
    issued_at = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)
    envelope = materialize_governance_review_envelope(
        issued_at_utc=issued_at,
        review_sla_hours=24,
        priority_score=88,
        queue_key="HEIGHTENED_REVIEW_QUEUE::ELEVATED_PRIORITY::AUTOMATION::RESTRICTING",
    )
    assert envelope.governance_plane_review_due_by_utc.isoformat() in envelope.governance_plane_review_envelope_vector
    assert envelope.governance_plane_review_sort_key in envelope.governance_plane_review_envelope_vector
    assert envelope.governance_plane_review_envelope_sha256 == hashlib.sha256(
        envelope.governance_plane_review_envelope_vector.encode("utf-8")
    ).hexdigest()


def test_attestation_carries_governance_review_envelope() -> None:
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
    assert attestation.governance_plane_review_envelope_vector
    assert attestation.governance_plane_review_envelope_sha256 == hashlib.sha256(
        attestation.governance_plane_review_envelope_vector.encode("utf-8")
    ).hexdigest()
    assert attestation.governance_plane_review_sort_key in attestation.governance_plane_review_envelope_vector
    assert attestation.governance_plane_queue_key in attestation.governance_plane_review_envelope_vector
