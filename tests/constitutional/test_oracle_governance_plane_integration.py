from strategy_validator.contracts.oracle import OracleAdvisoryInput, OracleSensorMatrix, SemanticSensorSnapshot, MicrostructureSensorSnapshot, MacroRegimeSensorSnapshot, StrategyHealthSnapshot
from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation, render_oracle_morning_attestation_markdown


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


def test_attestation_exposes_governance_plane_summary() -> None:
    attestation = build_oracle_morning_attestation(_payload())
    assert attestation.governance_plane_status in {"GOVERNANCE_READY", "GOVERNANCE_RESTRICTED", "GOVERNANCE_BLOCKED"}
    assert attestation.governance_plane_summary_line
    markdown = render_oracle_morning_attestation_markdown(attestation)
    assert attestation.governance_plane_summary_line in markdown
