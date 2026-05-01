from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec


def _minimal_batch(**kwargs: object) -> dict:
    base = {
        "batch_id": "b1",
        "as_of_utc": "2026-01-01T00:00:00+00:00",
        "mode": "paper",
        "output_root": "out",
        "strategies": [
            {
                "strategy_id": "s1",
                "strategy_type": "momentum",
                "universe": "U",
                "timeframe": "1d",
                "as_of_utc": "2026-01-01T00:00:00+00:00",
                "lookback_days": 30,
            }
        ],
    }
    base.update(kwargs)
    return base


def test_load_valid_json_spec(tmp_path: Path) -> None:
    p = tmp_path / "b.json"
    p.write_text(json.dumps(_minimal_batch()), encoding="utf-8")
    spec = load_strategy_batch_spec(p)
    assert spec.batch_id == "b1"
    assert len(spec.strategies) == 1


def test_reject_duplicate_strategy_id(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["strategies"].append(
        {
            "strategy_id": "s1",
            "strategy_type": "mean_reversion",
            "universe": "U",
            "timeframe": "1d",
            "as_of_utc": "2026-01-01T00:00:00+00:00",
            "lookback_days": 30,
        }
    )
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_strategy_batch_spec(p)


def test_reject_naive_as_of(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["as_of_utc"] = "2026-01-01T00:00:00"
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        load_strategy_batch_spec(p)


def test_incomplete_execution_realism_keys_rejected(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["strategies"][0]["execution_assumptions"] = {"starting_capital": 100_000, "paper_only": True}
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete execution realism"):
        load_strategy_batch_spec(p)


def test_robustness_assumptions_optional_defaults(tmp_path: Path) -> None:
    p = tmp_path / "b.json"
    p.write_text(json.dumps(_minimal_batch()), encoding="utf-8")
    spec = load_strategy_batch_spec(p)
    assert spec.strategies[0].robustness_config.fold_count == 4


def test_robustness_assumptions_full_loads(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["strategies"][0]["robustness_assumptions"] = {
        "fold_count": 3,
        "min_train_bars": 8,
        "min_test_bars": 4,
        "min_positive_fold_ratio": 0.5,
        "max_worst_fold_return": -0.25,
        "max_pbo_like_score": 0.8,
        "min_dsr_like_score": -0.1,
    }
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    spec = load_strategy_batch_spec(p)
    assert spec.strategies[0].robustness_config.fold_count == 3


def test_robustness_partial_keys_rejected(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["strategies"][0]["robustness_assumptions"] = {"fold_count": 3}
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="robustness_assumptions"):
        load_strategy_batch_spec(p)


def test_robustness_bad_ratio_rejected(tmp_path: Path) -> None:
    raw = _minimal_batch()
    raw["strategies"][0]["robustness_assumptions"] = {
        "fold_count": 3,
        "min_train_bars": 8,
        "min_test_bars": 4,
        "min_positive_fold_ratio": 2.0,
        "max_worst_fold_return": -0.25,
        "max_pbo_like_score": 0.8,
        "min_dsr_like_score": -0.1,
    }
    p = tmp_path / "b.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_strategy_batch_spec(p)


def test_strategy_batch_spec_roundtrip() -> None:
    spec = StrategyBatchSpec(
        batch_id="x",
        as_of_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        mode="research",
        strategies=[
            StrategyCandidateSpec(
                strategy_id="a",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
                lookback_days=10,
            )
        ],
        output_root="/tmp/out",
        pit_policy=PitPolicy.STRICT,
    )
    dumped = spec.model_dump(mode="json")
    assert StrategyBatchSpec.model_validate(dumped).batch_id == "x"
