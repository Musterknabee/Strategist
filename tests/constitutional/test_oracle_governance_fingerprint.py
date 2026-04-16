import hashlib

from strategy_validator.contracts.oracle import (
    MacroRegimeSensorSnapshot,
    MicrostructureSensorSnapshot,
    OracleAdvisoryInput,
    OracleSensorMatrix,
    SemanticSensorSnapshot,
    StrategyHealthSnapshot,
)
from strategy_validator.validator.oracle_advisory import (
    build_oracle_morning_attestation,
    render_oracle_morning_attestation_markdown,
)
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane


def _payload() -> OracleAdvisoryInput:
    return OracleAdvisoryInput(
        generated_for_utc="2026-01-01T08:00:00+00:00",
        universe_label="core",
        sensors=OracleSensorMatrix(
            semantic=SemanticSensorSnapshot(),
            microstructure=MicrostructureSensorSnapshot(),
            macro=MacroRegimeSensorSnapshot(
                yield_curve_slope_bps=12.0,
                high_yield_credit_spread_bps=350.0,
                equity_bond_correlation=0.2,
            ),
        ),
        strategies=[
            StrategyHealthSnapshot(
                strategy_id="s1",
                strategy_type="macro",
                prior_edge_confidence=0.6,
                deflated_sharpe_ratio=0.8,
                cpcv_lower_bound=0.2,
                realized_live_sharpe=0.4,
                recent_win_rate=0.55,
                drawdown_fraction=0.1,
            )
        ],
    )


def test_governance_plane_emits_stable_vector_and_sha256() -> None:
    result = assess_governance_plane(
        evidence_freshness_status="AGING",
        evidence_integrity_status="VERIFIED",
        evidence_coverage_status="COMPLETE",
        support_verification_status="ABSENT",
        support_chain_trust_status="TRUST_RESTRICTED",
        support_chain_remediation_status="REMEDIATION_RECOMMENDED",
        support_chain_remediation_actions=["Complete the recommended support-chain remediation work before expanding reliance."],
        operator_readiness="REVIEW_WITH_CAUTION",
        surface_label="this strategist surface",
    )
    assert result.governance_plane_vector
    assert "status=GOVERNANCE_RESTRICTED" in result.governance_plane_vector
    assert "restricted=" in result.governance_plane_vector
    assert result.governance_plane_sha256 == hashlib.sha256(result.governance_plane_vector.encode("utf-8")).hexdigest()


def test_attestation_persists_and_renders_governance_fingerprint() -> None:
    attestation = build_oracle_morning_attestation(_payload())
    assert attestation.governance_plane_vector
    assert attestation.governance_plane_sha256 == hashlib.sha256(attestation.governance_plane_vector.encode("utf-8")).hexdigest()
    markdown = render_oracle_morning_attestation_markdown(attestation)
    assert attestation.governance_plane_vector in markdown
    assert attestation.governance_plane_sha256 in markdown
