from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.research.strategy_batch_runner import run_strategy_batch


def _spec(tmp_path: Path) -> StrategyBatchSpec:
    return StrategyBatchSpec(
        batch_id="collision-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="one",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=40,
            ),
        ],
    )


def test_explicit_run_id_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", raising=False)
    spec = _spec(tmp_path)
    s = run_strategy_batch(spec, allow_synthetic=True, run_id="my-custom-run")
    assert s.run_id == "my-custom-run"
    assert (Path(s.output_dir).name) == "my-custom-run"


def test_existing_run_dir_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", raising=False)
    spec = _spec(tmp_path)
    run_strategy_batch(spec, allow_synthetic=True, run_id="dup")
    with pytest.raises(FileExistsError, match="RUN_DIRECTORY_EXISTS"):
        run_strategy_batch(spec, allow_synthetic=True, run_id="dup")


def test_overwrite_removes_previous_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", raising=False)
    spec = _spec(tmp_path)
    first = run_strategy_batch(spec, allow_synthetic=True, run_id="rw")
    marker = Path(first.output_dir) / "strategies" / "one" / "input_manifest.json"
    assert marker.is_file()
    second = run_strategy_batch(spec, allow_synthetic=True, run_id="rw", overwrite=True)
    assert second.run_id == "rw"
    assert marker.is_file()


def test_overwrite_rejects_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", raising=False)
    spec = _spec(tmp_path)
    with pytest.raises(ValueError, match="INVALID_RUN_ID"):
        run_strategy_batch(spec, allow_synthetic=True, run_id="../escape", overwrite=True)
