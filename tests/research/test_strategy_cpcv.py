from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.strategy_cpcv import CPCVConfig
from strategy_validator.research.strategy_cpcv import evaluate_strategy_cpcv


def _write_bars(path: Path, n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    lines = ["timestamp_utc,close\n"]
    for i in range(n):
        ts = start + timedelta(days=i)
        lines.append(f"{ts.isoformat()},{100.0 + i * 0.1}\n")
    path.write_text("".join(lines), encoding="utf-8")


def test_cpcv_deterministic(tmp_path: Path) -> None:
    p = tmp_path / "f.csv"
    _write_bars(p, 80)
    a = evaluate_strategy_cpcv(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        config=CPCVConfig(n_groups=4, n_test_groups=2, max_paths=8, min_train_bars=20, min_test_bars=8),
    )
    b = evaluate_strategy_cpcv(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        config=CPCVConfig(n_groups=4, n_test_groups=2, max_paths=8, min_train_bars=20, min_test_bars=8),
    )
    assert a.cpcv_evidence_sha256 == b.cpcv_evidence_sha256
    assert a.path_count == b.path_count


def test_cpcv_produces_paths(tmp_path: Path) -> None:
    p = tmp_path / "f.csv"
    _write_bars(p, 90)
    r = evaluate_strategy_cpcv(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        filtered_bars_path=p,
        synthetic_demo=False,
        config=CPCVConfig(max_paths=12),
    )
    assert r.path_count >= 1


def test_no_ledger_import_in_research_cpcv() -> None:
    import strategy_validator.research.strategy_cpcv as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "ledger.writer" not in src
