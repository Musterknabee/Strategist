from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_control_plane_event_sidecar_cli_executes_empty_replay_and_index(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    event_root = tmp_path / "events"
    event_root.mkdir()

    replay = subprocess.run(
        [
            sys.executable,
            "-m",
            "strategy_validator.cli.control_plane_event_sidecars",
            "replay",
            "--event-root",
            str(event_root),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    assert replay.returncode == 0
    replay_payload = json.loads(replay.stdout)
    assert replay_payload["event_count"] == 0
    assert replay_payload["ok"] is True

    index = subprocess.run(
        [
            sys.executable,
            "-m",
            "strategy_validator.cli.control_plane_event_sidecars",
            "index",
            "--event-root",
            str(event_root),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    assert index.returncode == 0
    index_payload = json.loads(index.stdout)
    assert index_payload["schema_version"] == "control_plane_event_projection_index/v1"
    assert index_payload["event_count"] == 0
    assert index_payload["ok"] is True
