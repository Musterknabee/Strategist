"""Telemetry sink contract tests (failures must not propagate)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.validator.telemetry_sinks import JsonlFileTelemetrySink, emit_decision_telemetry_sinks


@pytest.mark.constitutional
def test_jsonl_sink_writes_one_line_per_emit(tmp_path: Path) -> None:
    path = tmp_path / "t.jsonl"
    sink = JsonlFileTelemetrySink(str(path))
    sink.emit({"k": "v", "n": 1})
    sink.emit({"k": "w", "n": 2})
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["k"] == "v"


@pytest.mark.constitutional
def test_emit_decision_telemetry_sinks_swallows_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TELEMETRY_HTTP_URL", "http://127.0.0.1:9/__no_listener__")
    monkeypatch.setenv("STRATEGY_VALIDATOR_TELEMETRY_HTTP_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setenv("STRATEGY_VALIDATOR_TELEMETRY_HTTP_MAX_RETRIES", "1")
    monkeypatch.setenv("STRATEGY_VALIDATOR_TELEMETRY_HTTP_BACKOFF_START_MS", "0")
    # Must not raise even when the HTTP endpoint is unreachable.
    emit_decision_telemetry_sinks({"event": "test"})
