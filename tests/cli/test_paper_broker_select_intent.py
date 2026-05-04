from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main


def test_paper_broker_select_intent_writes_artifact(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "select-intent",
            "--tracking-id",
            "track-select1",
            "--symbol",
            "QQQ",
            "--side",
            "sell",
            "--qty",
            "0.25",
            "--strategy-id",
            "strategy-qqq",
            "--selected-by",
            "jp",
            "--reason",
            "prepare paper dry-run",
            "--output-root",
            str(tmp_path / "paper_broker"),
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert Path(payload["artifact"]).exists()
    assert Path(payload["history_artifact"]).exists()
    assert payload["selected_intent"]["symbol"] == "QQQ"
    assert payload["selected_intent"]["side"] == "sell"
    assert "dry-run-order" in payload["dry_run_command_hint"]
