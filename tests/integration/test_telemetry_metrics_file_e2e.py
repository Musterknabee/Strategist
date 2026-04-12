"""End-to-end file sinks: telemetry JSONL + Prometheus textfile (stdlib only)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.validator.metrics_sinks import emit_runtime_metrics
from strategy_validator.validator.telemetry_sinks import emit_decision_telemetry_sinks


@pytest.mark.integration
def test_telemetry_jsonl_and_metrics_textfile_emit_lines(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    jl = tmp_path / "telemetry.jsonl"
    prom = tmp_path / "sv.prom"
    monkeypatch.setenv("STRATEGY_VALIDATOR_TELEMETRY_JSONL_PATH", str(jl))
    monkeypatch.setenv("STRATEGY_VALIDATOR_METRICS_TEXTFILE_PATH", str(prom))

    record = {"event": "smoke_test", "ok": True, "n": 1}
    emit_decision_telemetry_sinks(record)
    emit_runtime_metrics(readiness_status="READY", blocker_count=0, schema_ok=True)

    assert jl.is_file()
    line = jl.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert json.loads(line)["event"] == "smoke_test"

    text = prom.read_text(encoding="utf-8")
    assert "strategy_validator_blocker_count" in text
    assert "strategy_validator_schema_ok" in text
