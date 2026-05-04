from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.research.strategy_batch_runner import run_strategy_batch


def _one_strategy_batch(tmp_path: Path) -> None:
    spec = StrategyBatchSpec(
        batch_id="ui-batch",
        as_of_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp_path),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="only",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
                lookback_days=20,
            ),
        ],
    )
    run_strategy_batch(spec)


def test_strategy_batch_latest_empty_without_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "empty"))
    client = TestClient(create_app())
    r = client.get("/ui/strategy-batches/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "ui_strategy_batch/v1"
    assert body["latest"] is None
    assert "NO_BATCH_ARTIFACTS" in body["degraded"]


def test_strategy_batch_latest_returns_summary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "runs"
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "ui-run")
    _one_strategy_batch(root)
    client = TestClient(create_app())
    r = client.get("/ui/strategy-batches/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["latest"] is not None
    assert body["latest"]["batch_id"] == "ui-batch"
    strat = body["latest"]["strategies"][0]
    assert strat.get("robustness_gate_status") == "NOT_APPLICABLE"
    assert strat.get("robustness_model_label") == "WALK_FORWARD_LOCAL_BAR_MODEL"
    assert isinstance(body["latest"].get("batch_ranking"), list)
    assert strat.get("charts_compact") is not None


def test_facade_lists_strategy_batch_routes() -> None:
    from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory

    inv = build_ui_public_facade_inventory()
    paths = {r["path"] if isinstance(r, dict) else getattr(r, "path", "") for r in inv["routes"]}
    assert "/ui/strategy-batches/latest" in paths
