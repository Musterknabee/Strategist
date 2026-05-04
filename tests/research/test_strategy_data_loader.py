from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.contracts.strategy_data_snapshot import LocalBarsDataSourceConfig, StrategyPitSnapshotStatus
from strategy_validator.research.strategy_data_loader import StrategyDataLoadError, bars_digest, load_local_bars_snapshot

REPO = Path(__file__).resolve().parents[2]
FIXTURE_CSV = REPO / "tests/fixtures/strategy_data/demo_daily_bars.csv"


def _candidate(**kw: object) -> StrategyCandidateSpec:
    defaults = dict(
        strategy_id="ld",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=90,
        params={"signal_window": 10},
        data_source=LocalBarsDataSourceConfig(
            path="tests/fixtures/strategy_data/demo_daily_bars.csv",
            pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
        ),
    )
    defaults.update(kw)
    return StrategyCandidateSpec(**defaults)


def _batch(c: StrategyCandidateSpec) -> StrategyBatchSpec:
    return StrategyBatchSpec(
        batch_id="b-load",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        output_root="artifacts/strategy_runs",
        strategies=[c],
    )


def test_loads_csv_and_digest_deterministic() -> None:
    c = _candidate()
    b = _batch(c)
    out = load_local_bars_snapshot(
        repo_root=REPO,
        candidate=c,
        batch=b,
        data_source=c.data_source,  # type: ignore[arg-type]
        retrieved_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    d1 = bars_digest(out.bars)
    d2 = bars_digest(out.bars)
    assert d1 == d2
    assert out.snapshot.row_count >= 30
    assert out.snapshot.pit_status == StrategyPitSnapshotStatus.PIT_VERIFIED


def test_excludes_future_rows_with_warning() -> None:
    c = _candidate()
    b = _batch(c)
    out = load_local_bars_snapshot(
        repo_root=REPO,
        candidate=c,
        batch=b,
        data_source=c.data_source,  # type: ignore[arg-type]
        retrieved_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    assert any("EXCLUDED_FUTURE_ROWS" in w for w in out.warnings)
    assert all(bar.timestamp_utc <= c.as_of_utc for bar in out.bars)


def test_duplicate_row_fails() -> None:
    rel = "tests/fixtures/strategy_data/_dup_test.csv"
    text = FIXTURE_CSV.read_text(encoding="utf-8")
    lines = text.strip().splitlines()
    dup = "\n".join([lines[0], lines[1], lines[1]]) + "\n"
    p = REPO / rel
    try:
        p.write_text(dup, encoding="utf-8")
        ds = LocalBarsDataSourceConfig(path=rel, pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED)
        c = _candidate(data_source=ds)
        b = _batch(c)
        with pytest.raises(StrategyDataLoadError) as ei:
            load_local_bars_snapshot(
                repo_root=REPO,
                candidate=c,
                batch=b,
                data_source=ds,
                retrieved_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )
        assert any("DUPLICATE" in x for x in ei.value.blockers)
    finally:
        p.unlink(missing_ok=True)


def test_json_batch_spec_with_data_source() -> None:
    p = REPO / "configs/strategy_batches/example_local_bars_batch.json"
    spec = load_strategy_batch_spec(p)
    assert spec.strategies[0].data_source is not None
    assert spec.strategies[0].data_source.kind == "local_bars"


def test_missing_published_downgrades_pit_claim() -> None:
    p = REPO / "tests/fixtures/strategy_data/demo_no_pub.csv"
    header = "symbol,timestamp_utc,open,high,low,close,volume\n"
    row = "DEMO,2026-04-01T00:00:00+00:00,1,1,1,1,0\n"
    p.write_text(header + row, encoding="utf-8")
    try:
        c = _candidate(
            lookback_days=30,
            data_source=LocalBarsDataSourceConfig(
                path="tests/fixtures/strategy_data/demo_no_pub.csv",
                pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
            ),
        )
        b = _batch(c)
        out = load_local_bars_snapshot(
            repo_root=REPO,
            candidate=c,
            batch=b,
            data_source=c.data_source,  # type: ignore[arg-type]
            retrieved_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert out.snapshot.pit_status == StrategyPitSnapshotStatus.MISSING_RELEASE_TIMESTAMPS
    finally:
        p.unlink(missing_ok=True)
