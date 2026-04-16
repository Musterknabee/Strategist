from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleSensorMatrix, SemanticSensorSnapshot, MicrostructureSensorSnapshot, MacroRegimeSensorSnapshot, StrategyHealthSnapshot
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation, render_oracle_morning_attestation_markdown
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


def test_governance_plane_exposes_typed_action_items() -> None:
    result = assess_governance_plane(
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
    assert result.governance_plane_action_items
    dimensions = {item.dimension for item in result.governance_plane_action_items}
    assert "SUPPORT_CHAIN_TRUST" in dimensions
    assert "REMEDIATION" in dimensions
    assert "READINESS" in dimensions
    assert "PROPAGATION" in dimensions
    assert all(item.severity in {"BLOCKING", "RESTRICTING"} for item in result.governance_plane_action_items)
    assert [item.action_text for item in result.governance_plane_action_items] == result.governance_plane_actions


def test_attestation_persists_and_renders_governance_action_items() -> None:
    attestation = build_oracle_morning_attestation(_payload())
    assert attestation.governance_plane_action_items
    markdown = render_oracle_morning_attestation_markdown(attestation)
    assert "## Governance actions" in markdown
    for item in attestation.governance_plane_action_items:
        assert item.dimension in markdown
        assert item.severity in markdown
        assert item.action_text in markdown
