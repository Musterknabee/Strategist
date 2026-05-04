from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.paper_tracking_ops import enroll_strategies_from_batch_run
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.contracts.strategy_data_snapshot import LocalBarsDataSourceConfig, StrategyPitSnapshotStatus
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]


def _exec_base() -> dict[str, float | bool]:
    return {
        "starting_capital": 1_000_000.0,
        "max_participation_rate": 0.12,
        "fee_bps": 1.0,
        "slippage_bps": 5.0,
        "min_average_daily_volume": 50_000.0,
        "allow_short": False,
        "borrow_required": False,
    }


def _run_local_batch(tmp: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(REPO)
    spec = StrategyBatchSpec(
        batch_id="api-pt-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="api-pt-momo",
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
                execution_assumptions={"friction_bps": 5.0, "paper_only": True, **_exec_base()},
            ),
        ],
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "api-pt-run")
    summary = run_strategy_batch(spec, allow_synthetic=True)
    return Path(summary.output_dir)


def test_paper_tracking_latest_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "empty"))
    client = TestClient(create_app())
    r = client.get("/ui/paper-tracking/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "ui_paper_tracking/v2"
    assert body["latest"] is None
    assert "NO_PAPER_TRACKING_ARTIFACTS" in body["degraded"]


def test_paper_tracking_latest_with_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pt = tmp_path / "pt"
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt))
    run_dir = _run_local_batch(tmp_path, monkeypatch)
    enroll_strategies_from_batch_run(run_dir, repo_root=REPO)
    client = TestClient(create_app())
    r = client.get("/ui/paper-tracking/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["latest"] is not None
    assert body["latest"]["manifest"]["candidate"]["strategy_id"] == "api-pt-momo"
    assert "lifecycle_state" in body["latest"]


def test_facade_lists_paper_tracking_routes() -> None:
    from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory

    inv = build_ui_public_facade_inventory()
    paths = {r["path"] if isinstance(r, dict) else getattr(r, "path", "") for r in inv["routes"]}
    assert "/ui/paper-tracking/latest" in paths
    assert "/ui/paper-tracking/{tracking_id}" in paths

