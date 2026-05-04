from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.strategy_thesis import ExpectedEdge, ExpectedFailureMode, StrategyThesis
from strategy_validator.research.oracle_mutation_proposal import build_mutation_proposals


def _minimal_thesis() -> StrategyThesis:
    return StrategyThesis(
        strategy_id="s1",
        thesis_id="t1",
        hypothesis="h",
        economic_rationale="r",
        market_inefficiency="i",
        expected_edge=ExpectedEdge(description="demo edge"),
        falsification_criteria=[],
        required_evidence=[],
        expected_failure_regimes=[ExpectedFailureMode(regime="x", description="y")],
        created_at_utc=datetime.now(timezone.utc),
    )


def test_build_mutation_proposals_digest_stable_shape() -> None:
    thesis = _minimal_thesis()
    art = build_mutation_proposals(thesis=thesis, batch_run_id="run-a", strategy_type="momentum_breakout")
    assert art.schema_version == "oracle_mutation_proposal/v1"
    assert len(art.proposals) >= 2
    assert len(art.digest_sha256) == 64
