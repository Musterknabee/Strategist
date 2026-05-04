from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.provider_historical_snapshot import ProviderHistoricalSnapshotManifest
from strategy_validator.contracts.strategy_batch import StrategyBatchSpec
from strategy_validator.contracts.strategy_data_snapshot import ProviderSnapshotDataSourceConfig
from strategy_validator.research.provider_historical_snapshot_io import finalize_manifest_sha
from strategy_validator.research.strategy_data_loader import StrategyDataLoadError, load_provider_snapshot_bars


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def test_provider_snapshot_loads_fixture_csv() -> None:
    repo = _repo()
    batch = StrategyBatchSpec.model_validate(
        {
            "batch_id": "b",
            "as_of_utc": "2026-02-15T12:00:00+00:00",
            "mode": "paper",
            "output_root": "out",
            "strategies": [
                {
                    "strategy_id": "s1",
                    "strategy_type": "momentum",
                    "universe": "SPY",
                    "timeframe": "1d",
                    "as_of_utc": "2026-02-15T12:00:00+00:00",
                    "lookback_days": 35,
                    "params": {"signal_window": 5},
                    "data_source": {
                        "kind": "provider_snapshot",
                        "manifest_path": "tests/fixtures/provider_snapshots/demo_provider_bars_manifest.json",
                    },
                    "execution_assumptions": {
                        "starting_capital": 1_000_000,
                        "max_participation_rate": 0.12,
                        "fee_bps": 1.0,
                        "slippage_bps": 5.0,
                        "min_average_daily_volume": 50_000,
                    },
                    "robustness_assumptions": {
                        "fold_count": 3,
                        "min_train_bars": 8,
                        "min_test_bars": 4,
                        "min_positive_fold_ratio": 0.5,
                        "max_worst_fold_return": -0.25,
                        "max_pbo_like_score": 0.8,
                        "min_dsr_like_score": -0.1,
                    },
                }
            ],
        }
    )
    cand = batch.strategies[0]
    ds = cand.data_source
    assert isinstance(ds, ProviderSnapshotDataSourceConfig)
    loaded, prov = load_provider_snapshot_bars(
        repo_root=repo,
        candidate=cand,
        batch=batch,
        data_source=ds,
        retrieved_at_utc=datetime.now(timezone.utc),
    )
    assert loaded.bars
    assert prov.provider_id == "demo_provider"
    assert loaded.snapshot.source_classification.value == "PROVIDER_GOVERNED_SNAPSHOT"


def test_provider_snapshot_digest_mismatch_blocks() -> None:
    repo = _repo()
    man_path = repo / "tests" / "fixtures" / "provider_snapshots" / "demo_provider_bars_manifest.json"
    raw = ProviderHistoricalSnapshotManifest.model_validate_json(man_path.read_text(encoding="utf-8"))
    bad = raw.model_copy(update={"bars_sha256": "0" * 64})
    bad = finalize_manifest_sha(bad)
    tmp = repo / "tests" / "fixtures" / "provider_snapshots" / "_tmp_bad_digest_manifest.json"
    tmp.write_text(bad.model_dump_json(indent=2), encoding="utf-8")
    try:
        batch = StrategyBatchSpec.model_validate(
            {
                "batch_id": "b",
                "as_of_utc": "2026-02-15T12:00:00+00:00",
                "mode": "paper",
                "output_root": "out",
                "strategies": [
                    {
                        "strategy_id": "s1",
                        "strategy_type": "momentum",
                        "universe": "SPY",
                        "timeframe": "1d",
                        "as_of_utc": "2026-02-15T12:00:00+00:00",
                        "lookback_days": 35,
                        "params": {"signal_window": 5},
                        "data_source": {
                            "kind": "provider_snapshot",
                            "manifest_path": str(tmp.relative_to(repo)).replace("\\", "/"),
                        },
                        "execution_assumptions": {
                            "starting_capital": 1_000_000,
                            "max_participation_rate": 0.12,
                            "fee_bps": 1.0,
                            "slippage_bps": 5.0,
                            "min_average_daily_volume": 50_000,
                        },
                        "robustness_assumptions": {
                            "fold_count": 3,
                            "min_train_bars": 8,
                            "min_test_bars": 4,
                            "min_positive_fold_ratio": 0.5,
                            "max_worst_fold_return": -0.25,
                            "max_pbo_like_score": 0.8,
                            "min_dsr_like_score": -0.1,
                        },
                    }
                ],
            }
        )
        cand = batch.strategies[0]
        ds = cand.data_source
        assert isinstance(ds, ProviderSnapshotDataSourceConfig)
        with pytest.raises(StrategyDataLoadError) as exc:
            load_provider_snapshot_bars(
                repo_root=repo,
                candidate=cand,
                batch=batch,
                data_source=ds,
                retrieved_at_utc=datetime.now(timezone.utc),
            )
        assert "SHA256_MISMATCH" in "".join(exc.value.blockers)
    finally:
        tmp.unlink(missing_ok=True)


def test_provider_snapshot_strict_pit_rejects_best_effort() -> None:
    repo = _repo()
    man_path = repo / "tests" / "fixtures" / "provider_snapshots" / "demo_provider_bars_manifest.json"
    raw = ProviderHistoricalSnapshotManifest.model_validate_json(man_path.read_text(encoding="utf-8"))
    from strategy_validator.contracts.provider_historical_data import ProviderHistoricalPitStatus

    be = raw.model_copy(
        update={"pit_status": ProviderHistoricalPitStatus.BEST_EFFORT_AS_OF},
    )
    be = finalize_manifest_sha(be)
    p = repo / "tests" / "fixtures" / "provider_snapshots" / "_tmp_strict_pit_manifest.json"
    try:
        p.write_text(be.model_dump_json(indent=2), encoding="utf-8")
        batch = StrategyBatchSpec.model_validate(
            {
                "batch_id": "b",
                "as_of_utc": "2026-02-15T12:00:00+00:00",
                "mode": "paper",
                "output_root": "out",
                "pit_policy": "STRICT",
                "strategies": [
                    {
                        "strategy_id": "s1",
                        "strategy_type": "momentum",
                        "universe": "SPY",
                        "timeframe": "1d",
                        "as_of_utc": "2026-02-15T12:00:00+00:00",
                        "lookback_days": 35,
                        "params": {"signal_window": 5},
                        "data_source": {
                            "kind": "provider_snapshot",
                            "manifest_path": "tests/fixtures/provider_snapshots/_tmp_strict_pit_manifest.json",
                        },
                        "execution_assumptions": {
                            "starting_capital": 1_000_000,
                            "max_participation_rate": 0.12,
                            "fee_bps": 1.0,
                            "slippage_bps": 5.0,
                            "min_average_daily_volume": 50_000,
                        },
                        "robustness_assumptions": {
                            "fold_count": 3,
                            "min_train_bars": 8,
                            "min_test_bars": 4,
                            "min_positive_fold_ratio": 0.5,
                            "max_worst_fold_return": -0.25,
                            "max_pbo_like_score": 0.8,
                            "min_dsr_like_score": -0.1,
                        },
                    }
                ],
            }
        )
        cand = batch.strategies[0]
        ds = cand.data_source
        assert isinstance(ds, ProviderSnapshotDataSourceConfig)
        with pytest.raises(StrategyDataLoadError) as exc:
            load_provider_snapshot_bars(
                repo_root=repo,
                candidate=cand,
                batch=batch,
                data_source=ds,
                retrieved_at_utc=datetime.now(timezone.utc),
            )
        assert "PIT_STRICT" in "".join(exc.value.blockers)
    finally:
        p.unlink(missing_ok=True)
