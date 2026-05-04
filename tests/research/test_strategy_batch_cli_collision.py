from __future__ import annotations

import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest

from strategy_validator.cli.strategy_batch_run import main
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec


def _write_batch(path: Path, *, output_root: str) -> None:
    spec = StrategyBatchSpec(
        batch_id="cli-collision-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=output_root,
        strategies=[
            StrategyCandidateSpec(
                strategy_id="cli-one",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=40,
            ),
        ],
    )
    path.write_text(json.dumps(spec.model_dump(mode="json"), indent=2), encoding="utf-8")


def test_cli_json_emits_parseable_error_on_run_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", raising=False)
    batch = tmp_path / "batch.json"
    root = tmp_path / "runs"
    _write_batch(batch, output_root=str(root))
    assert main(["--batch", str(batch), "--run-id", "same-run", "--json"]) == 0
    out = StringIO()
    monkeypatch.setattr("sys.stdout", out)
    code = main(["--batch", str(batch), "--run-id", "same-run", "--json"])
    assert code == 2
    err_payload = json.loads(out.getvalue().strip())
    assert err_payload["ok"] is False
    assert err_payload["error"] == "RUN_DIRECTORY_EXISTS"
    assert "path" in err_payload and str(err_payload["path"])
