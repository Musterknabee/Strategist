from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.strategy_execution_realism import (
    ExecutionRealismAssumptions,
    ExecutionRealismGateStatus,
    ExecutionRealismResult,
    LiquidityCheckResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def test_assumptions_rejects_negative_fee() -> None:
    with pytest.raises(ValueError):
        ExecutionRealismAssumptions(
            starting_capital=100_000,
            max_participation_rate=0.02,
            fee_bps=-1,
            slippage_bps=2,
            min_average_daily_volume=10_000,
        )


def test_result_roundtrip_and_digest_stable() -> None:
    a = ExecutionRealismAssumptions(
        starting_capital=100_000,
        max_participation_rate=0.02,
        fee_bps=1,
        slippage_bps=3,
        min_average_daily_volume=50_000,
    )
    r = ExecutionRealismResult(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        assumptions=a,
        gate_status=ExecutionRealismGateStatus.PROVEN,
        liquidity=LiquidityCheckResult(status="PASS", average_daily_dollar_volume=100_000, threshold=50_000),
        evidence_digest="x",
    )
    raw = r.model_dump(mode="json")
    r2 = ExecutionRealismResult.model_validate(raw)
    assert r2.gate_status == ExecutionRealismGateStatus.PROVEN
    d1 = canonical_json_sha256(ExecutionRealismResult.model_validate(raw).model_dump(mode="json"))
    d2 = canonical_json_sha256(ExecutionRealismResult.model_validate(raw).model_dump(mode="json"))
    assert d1 == d2
