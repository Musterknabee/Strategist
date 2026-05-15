from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.application.research_cycle_ops import (
    build_ui_research_cycle_status_payload,
    consume_pending_trigger,
    pending_trigger_path,
    request_research_cycle_trigger,
)


def test_trigger_and_consume_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path))
    receipt = request_research_cycle_trigger(
        operator_id="tester",
        mode="heavy",
        idempotency_key="idem-1",
        artifact_root=tmp_path,
    )
    assert receipt["accepted"] is True
    assert receipt["queued"] is True
    assert pending_trigger_path(artifact_root=tmp_path).is_file()

    raw = consume_pending_trigger(artifact_root=tmp_path)
    assert raw is not None
    assert raw["mode"] == "heavy"
    assert raw["operator_id"] == "tester"
    assert not pending_trigger_path(artifact_root=tmp_path).is_file()


def test_status_payload_flags_missing_daemon(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path))
    payload = build_ui_research_cycle_status_payload(artifact_root=tmp_path)
    assert payload["schema_version"] == "ui_research_cycle_status/v1"
    assert "DAEMON_NOT_REGISTERED" in payload["degraded"]
