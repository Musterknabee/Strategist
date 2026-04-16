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


def test_governance_plane_emits_canonical_codes() -> None:
    assessment = assess_governance_plane(
        evidence_freshness_status="STALE",
        evidence_integrity_status="UNVERIFIED",
        evidence_coverage_status="MISSING",
        support_verification_status="UNVERIFIED",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        support_chain_remediation_actions=["Repair the missing support chain before broader use."],
        operator_readiness="HOLD_FOR_REFRESH",
        surface_label="this briefing pack",
    )
    assert assessment.governance_plane_status == "GOVERNANCE_BLOCKED"
    assert "UNTRUSTED_SUPPORT_CHAIN" in assessment.governance_plane_codes
    assert "REMEDIATION_REQUIRED" in assessment.governance_plane_codes
    assert "READINESS_HOLD" in assessment.governance_plane_codes
    assert "codes=" in assessment.governance_plane_vector


def test_attestation_persists_and_renders_governance_codes() -> None:
    attestation = build_oracle_morning_attestation(_payload())
    assert isinstance(attestation.governance_plane_codes, list)
    markdown = render_oracle_morning_attestation_markdown(attestation)
    assert "Codes:" in markdown
    for code in attestation.governance_plane_codes:
        assert f"- {code}" in markdown
