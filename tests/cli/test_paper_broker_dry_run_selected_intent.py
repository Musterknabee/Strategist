from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main


def test_paper_broker_dry_run_selected_intent_replays_selection_sha(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    out_root = tmp_path / "paper_broker"

    rc_select = main(
        [
            "select-intent",
            "--tracking-id",
            "track-replay1",
            "--symbol",
            "QQQ",
            "--side",
            "sell",
            "--qty",
            "0.5",
            "--strategy-id",
            "strategy-qqq",
            "--output-root",
            str(out_root),
        ]
    )
    assert rc_select == 0
    selected = json.loads(capsys.readouterr().out)

    rc_replay = main(
        [
            "dry-run-selected-intent",
            "--tracking-id",
            "track-replay1",
            "--output-root",
            str(out_root),
        ]
    )

    assert rc_replay == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["replayed_from_selected_intent"] is True
    assert replay["selected_intent_sha256"] == selected["artifact_sha256"]
    assert replay["dry_run_source_selection_sha256"] == selected["artifact_sha256"]
    assert replay["intent"]["symbol"] == "QQQ"
    assert replay["intent"]["side"] == "sell"
    artifact = json.loads(Path(replay["artifact"]).read_text(encoding="utf-8"))
    assert artifact["replayed_from_selected_intent"] is True
    assert artifact["source_selection_artifact_sha256"] == selected["artifact_sha256"]
    assert artifact["result"]["dry_run"] is True
