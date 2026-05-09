from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.market_data_integrity_projection import build_ui_market_data_integrity_payload
from strategy_validator.contracts.market_data_integrity import MarketDataIntegrityGateStatus
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity


def _bar(symbol: str, day: int, close: float) -> StrategyBar:
    return StrategyBar(
        symbol=symbol,
        timestamp_utc=datetime(2026, 1, day, 16, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1000,
    )


def _write_result(path: Path, *, strategy_id: str, provider_id: str, adjusted_status: str, bars: list[StrategyBar]) -> None:
    res = evaluate_market_data_integrity(
        strategy_id=strategy_id,
        batch_id="batch-1",
        run_id=f"run-{strategy_id}",
        bars=bars,
        as_of_utc=datetime(2026, 1, 5, 20, tzinfo=timezone.utc),
        snapshot=None,
        provider_id=provider_id,
        license_scope="research_only",
        trust_level="provider_snapshot",
        adjusted_status=adjusted_status,
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(res.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")


def test_market_data_integrity_projection_scans_filters_and_counts(tmp_path: Path) -> None:
    root = tmp_path / "artifacts" / "strategy_runs"
    _write_result(
        root / "run-a" / "strategy-a" / "market_data_integrity_result.json",
        strategy_id="strategy-a",
        provider_id="provider-a",
        adjusted_status="ADJUSTED",
        bars=[_bar("SPY", 2, 100), _bar("SPY", 5, 101)],
    )
    _write_result(
        root / "run-b" / "strategy-b" / "market_data_integrity_result.json",
        strategy_id="strategy-b",
        provider_id="provider-b",
        adjusted_status="UNKNOWN",
        bars=[_bar("QQQ", 2, 100), _bar("QQQ", 5, 200)],
    )

    payload = build_ui_market_data_integrity_payload(scan_root=root, gate_status=(MarketDataIntegrityGateStatus.WARNING.value,))

    assert payload["schema_version"] == "ui_market_data_integrity/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_provider_calls"] is True
    assert payload["artifact_count"] == 2
    assert payload["filtered_artifact_count"] == 1
    assert payload["returned_artifact_count"] == 1
    assert payload["entries"][0]["strategy_id"] == "strategy-b"
    assert payload["entries"][0]["corporate_action_warning_count"] == 1
    assert payload["gate_counts"] == {"WARNING": 1}
    assert payload["summary"]["worst_gate_status"] == "WARNING"
    assert "No strategy promotion" in " ".join(payload["guardrails"])


def test_market_data_integrity_projection_reports_missing_and_invalid_artifacts(tmp_path: Path) -> None:
    missing_payload = build_ui_market_data_integrity_payload(scan_root=tmp_path / "missing")
    assert missing_payload["degraded"] == ["SCAN_ROOT_MISSING"]
    assert missing_payload["summary"]["worst_gate_status"] == "NOT_APPLICABLE"

    root = tmp_path / "runs"
    bad = root / "run" / "strategy" / "market_data_integrity_result.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{not json", encoding="utf-8")

    payload = build_ui_market_data_integrity_payload(scan_root=root)
    assert payload["invalid_artifact_count"] == 1
    assert "INVALID_MARKET_DATA_INTEGRITY_ARTIFACTS" in payload["degraded"]
    assert payload["artifact_count"] == 0
