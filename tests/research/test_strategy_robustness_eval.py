from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.strategy_robustness import (
    RobustnessAssumptions,
    RobustnessGateStatus,
)
from strategy_validator.research.strategy_robustness import evaluate_strategy_robustness


def _write_bars(path: Path, closes: list[float], start: datetime | None = None) -> None:
    t0 = start or datetime(2026, 1, 2, tzinfo=timezone.utc)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "close"])
        for i, c in enumerate(closes):
            ts = (t0 + timedelta(days=i)).isoformat()
            w.writerow([ts, c])


def test_synthetic_not_applicable() -> None:
    r = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=None,
        synthetic_demo=True,
        assumptions=RobustnessAssumptions(),
    )
    assert r.gate_status == RobustnessGateStatus.NOT_APPLICABLE
    assert "SYNTHETIC" in r.blockers[0]
    assert r.robustness_evidence_sha256


def test_missing_file_blocked(tmp_path: Path) -> None:
    p = tmp_path / "nope.csv"
    r = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        assumptions=RobustnessAssumptions(),
    )
    assert r.gate_status == RobustnessGateStatus.BLOCKED
    assert r.blockers[0] == "MISSING_FILTERED_BARS"


def test_insufficient_sample_blocked(tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    _write_bars(p, [100.0, 101.0])
    r = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        assumptions=RobustnessAssumptions(fold_count=4, min_train_bars=20, min_test_bars=5),
    )
    assert r.gate_status == RobustnessGateStatus.BLOCKED
    assert any("INSUFFICIENT" in b for b in r.blockers)


def test_upward_trend_proven(tmp_path: Path) -> None:
    p = tmp_path / "up.csv"
    closes = [100.0 + i * 0.15 for i in range(80)]
    _write_bars(p, closes)
    a = RobustnessAssumptions(fold_count=3, min_train_bars=15, min_test_bars=5)
    r1 = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        assumptions=a,
    )
    r2 = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        assumptions=a,
    )
    assert r1.gate_status == RobustnessGateStatus.PROVEN
    assert r1.median_test_return == r2.median_test_return
    assert r1.pbo_like_score == r2.pbo_like_score
    assert r1.folds[0].train_end_utc < r1.folds[0].test_start_utc


def test_choppy_may_warn_or_block(tmp_path: Path) -> None:
    p = tmp_path / "chop.csv"
    # Strong mean reversion around a flat level → many negative test folds.
    closes = [100.0 + 3.0 * (1 if i % 3 == 0 else -1) for i in range(120)]
    _write_bars(p, closes)
    r = evaluate_strategy_robustness(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        assumptions=RobustnessAssumptions(fold_count=4, min_train_bars=15, min_test_bars=5),
    )
    assert r.gate_status in (
        RobustnessGateStatus.WARNING,
        RobustnessGateStatus.BLOCKED,
    )
