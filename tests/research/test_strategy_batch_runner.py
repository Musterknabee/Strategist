from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec, StrategyRunStatus
from strategy_validator.contracts.strategy_data_snapshot import LocalBarsDataSourceConfig, StrategyPitSnapshotStatus
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_runner import run_single_strategy, run_strategy_batch

REPO = Path(__file__).resolve().parents[2]


def _spec(tmp_path: Path, *, pit: PitPolicy = PitPolicy.DEGRADE_TO_PAPER_ONLY) -> StrategyBatchSpec:
    return StrategyBatchSpec(
        batch_id="test-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=4,
        pit_policy=pit,
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="z-momo",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=60,
                params={"signal_window": 10},
            ),
            StrategyCandidateSpec(
                strategy_id="a-mr",
                strategy_type="mean_reversion",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=40,
            ),
            StrategyCandidateSpec(
                strategy_id="m-vol",
                strategy_type="volatility_breakout",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=50,
            ),
        ],
    )


def test_batch_runner_three_strategies_concurrent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "fixed-run-test")
    spec = _spec(tmp_path)
    summary = run_strategy_batch(spec, allow_synthetic=True, fail_fast=False)
    assert summary.strategy_count == 3
    assert summary.failed_count == 0
    assert summary.paper_only_count == 3
    assert summary.ok is True
    ids = [r.strategy_id for r in summary.strategies]
    assert ids == sorted(ids)
    manifest = Path(summary.output_dir) / "strategies" / "a-mr" / "evidence_manifest.json"
    assert manifest.is_file()
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["synthetic_demo"] is True
    assert body["may_gate_live_promotion"] is False
    assert body.get("robustness_gate_status") == "NOT_APPLICABLE"
    assert body.get("robustness_model_label") == "WALK_FORWARD_LOCAL_BAR_MODEL"


def test_no_synthetic_blocks_under_strict_pit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "pit-strict")
    spec = _spec(tmp_path, pit=PitPolicy.STRICT)
    r = run_single_strategy(
        candidate=spec.strategies[0],
        batch=spec,
        run_id="r1",
        run_dir=tmp_path / "rd",
        allow_synthetic=True,
    )
    assert r.status == StrategyRunStatus.BLOCKED


def test_digest_changes_when_metrics_change() -> None:
    a = canonical_json_sha256({"m": {"x": 1.0}})
    b = canonical_json_sha256({"m": {"x": 1.01}})
    assert a != b


def test_runner_has_no_ledger_writer_import() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "strategy_validator/research/strategy_batch_runner.py").read_text(encoding="utf-8")
    assert "ledger.writer" not in text


def test_fail_fast_leaves_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "ff")
    spec = _spec(tmp_path)

    def boom(**kwargs: object):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "strategy_validator.research.strategy_batch_runner.deterministic_prices",
        boom,
    )
    summary = run_strategy_batch(spec, fail_fast=True)
    assert summary.failed_count >= 1
    assert summary.pending_count > 0
    assert summary.ok is False


def _execution_realism_assumptions_base() -> dict[str, float | bool]:
    return {
        "starting_capital": 1_000_000.0,
        "max_participation_rate": 0.12,
        "fee_bps": 1.0,
        "slippage_bps": 5.0,
        "min_average_daily_volume": 50_000.0,
        "allow_short": False,
        "borrow_required": False,
    }


def _local_bars_candidate() -> StrategyCandidateSpec:
    return StrategyCandidateSpec(
        strategy_id="local-momo",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=90,
        params={"signal_window": 15},
        data_source=LocalBarsDataSourceConfig(
            path="tests/fixtures/strategy_data/demo_daily_bars.csv",
            pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
        ),
        execution_assumptions={
            "friction_bps": 5.0,
            "paper_only": True,
            **_execution_realism_assumptions_base(),
        },
    )


def test_local_bars_batch_non_synthetic_manifests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "local-bars-run")
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="batch-local",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        output_root=str(tmp_path / "runs"),
        strategies=[_local_bars_candidate()],
    )
    summary = run_strategy_batch(spec, allow_synthetic=True)
    assert summary.passed_count == 1
    assert summary.strategies[0].data_status == "LOCAL_BARS"
    assert summary.strategies[0].data_plane == "REAL_LOCAL"
    assert summary.strategies[0].pit_snapshot_status == "PIT_VERIFIED"
    strat_dir = Path(summary.output_dir) / "strategies" / "local-momo"
    assert (strat_dir / "data_snapshot_manifest.json").is_file()
    assert (strat_dir / "execution_realism_result.json").is_file()
    assert summary.strategies[0].data_snapshot_digest
    assert summary.strategies[0].gate_summary.execution_realism_gate == "PROVEN"
    assert summary.strategies[0].execution_realism_gate == "PROVEN"
    assert summary.strategies[0].gate_summary.promotion_eligible is True
    assert summary.strategies[0].execution_realism_digest
    assert (strat_dir / "robustness_result.json").is_file()
    rob = json.loads((strat_dir / "robustness_result.json").read_text(encoding="utf-8"))
    assert rob["gate_status"] == "PROVEN"
    ev = json.loads((strat_dir / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert ev["robustness_gate_status"] == "PROVEN"
    assert ev["robustness_evidence_sha256"] == rob["robustness_evidence_sha256"]
    assert summary.strategies[0].robustness_gate_status == "PROVEN"


def test_strict_pit_passes_with_verified_local_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "strict-local")
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="batch-strict-ok",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        pit_policy=PitPolicy.STRICT,
        output_root=str(tmp_path / "runs"),
        strategies=[_local_bars_candidate()],
    )
    summary = run_strategy_batch(spec, allow_synthetic=True)
    assert summary.strategies[0].status == StrategyRunStatus.PASSED


def test_strict_pit_blocks_synthetic_demo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "strict-synth")
    spec = _spec(tmp_path, pit=PitPolicy.STRICT)
    r = run_single_strategy(
        candidate=spec.strategies[0],
        batch=spec,
        run_id="r1",
        run_dir=tmp_path / "rd",
        allow_synthetic=True,
    )
    assert r.status == StrategyRunStatus.BLOCKED


def test_no_synthetic_blocks_without_local_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "no-synth")
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="b",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="no-data",
                strategy_type="momentum",
                universe="DEMO",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=30,
                data_source=LocalBarsDataSourceConfig(
                    path="tests/fixtures/strategy_data/does_not_exist.csv",
                    pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
                ),
            ),
        ],
    )
    r = run_single_strategy(
        candidate=spec.strategies[0],
        batch=spec,
        run_id="r1",
        run_dir=tmp_path / "rd",
        allow_synthetic=False,
    )
    assert r.status == StrategyRunStatus.BLOCKED


def test_coverage_gate_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "cov-block")
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="cov",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="cov-s",
                strategy_type="momentum",
                universe="DEMO",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=500,
                params={"signal_window": 10},
                data_source=LocalBarsDataSourceConfig(
                    path="tests/fixtures/strategy_data/demo_daily_bars.csv",
                    pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
                ),
                execution_assumptions={"paper_only": True, **_execution_realism_assumptions_base()},
            ),
        ],
    )
    r = run_single_strategy(
        candidate=spec.strategies[0],
        batch=spec,
        run_id="r1",
        run_dir=tmp_path / "rd",
        allow_synthetic=True,
    )
    assert r.status == StrategyRunStatus.BLOCKED
    assert r.gate_summary.data_coverage_gate.startswith("BLOCKED")


def test_synthetic_promotion_not_eligible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "promo-syn")
    spec = _spec(tmp_path)
    summary = run_strategy_batch(spec, allow_synthetic=True)
    for r in summary.strategies:
        assert r.gate_summary.promotion_eligible is False
        assert r.status == StrategyRunStatus.PAPER_ONLY
        assert r.gate_summary.execution_realism_gate == "NOT_APPLICABLE"


def test_insufficient_sample_warns_on_short_local_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "short-win")
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="short",
        as_of_utc=datetime(2026, 1, 25, tzinfo=timezone.utc),
        mode="paper",
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="short-momo",
                strategy_type="momentum",
                universe="DEMO",
                timeframe="1d",
                as_of_utc=datetime(2026, 1, 25, tzinfo=timezone.utc),
                lookback_days=45,
                params={"signal_window": 5},
                data_source=LocalBarsDataSourceConfig(
                    path="tests/fixtures/strategy_data/demo_daily_bars.csv",
                    pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
                ),
                execution_assumptions={
                    "paper_only": True,
                    **_execution_realism_assumptions_base(),
                    "starting_capital": 150_000.0,
                    "max_participation_rate": 0.25,
                },
            ),
        ],
    )
    r = run_single_strategy(
        candidate=spec.strategies[0],
        batch=spec,
        run_id="r1",
        run_dir=tmp_path / "rd",
        allow_synthetic=True,
    )
    assert r.status == StrategyRunStatus.BLOCKED
    assert r.gate_summary.robustness_gate == "BLOCKED"
    assert r.gate_summary.execution_realism_gate == "PROVEN"
    assert any("INSUFFICIENT_SAMPLE" in w for w in r.warnings)
    assert r.gate_summary.promotion_eligible is False
    assert any("ROBUSTNESS:BLOCKED" in x for x in r.gate_summary.promotion_blocked_reasons)
