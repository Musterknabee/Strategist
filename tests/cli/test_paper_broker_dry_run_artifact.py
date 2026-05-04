from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main


def test_paper_broker_dry_run_order_writes_artifact(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    out_root = tmp_path / "paper_broker"

    rc = main([
        "dry-run-order",
        "--tracking-id",
        "track-cli123",
        "--symbol",
        "SPY",
        "--qty",
        "1",
        "--side",
        "buy",
        "--output-root",
        str(out_root),
    ])

    assert rc == 0
    stdout = json.loads(capsys.readouterr().out)
    latest = Path(stdout["artifact"])
    history = Path(stdout["history_artifact"])
    assert latest.exists()
    assert history.exists()
    artifact = json.loads(latest.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "paper_execution_dry_run_artifact/v1"
    assert artifact["tracking_id"] == "track-cli123"
    assert artifact["no_order_submitted"] is True
    assert artifact["result"]["dry_run"] is True
    assert artifact["result"]["ok"] is False
