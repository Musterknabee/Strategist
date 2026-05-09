from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity


def _bar(day: int, close: float) -> StrategyBar:
    return StrategyBar(
        symbol="SPY",
        timestamp_utc=datetime(2026, 1, day, 16, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1000,
    )


def test_ui_market_data_integrity_route_and_facade_are_read_only(tmp_path: Path) -> None:
    result = evaluate_market_data_integrity(
        strategy_id="route-strategy",
        batch_id="batch-route",
        run_id="run-route",
        bars=[_bar(2, 100), _bar(5, 101)],
        as_of_utc=datetime(2026, 1, 5, 20, tzinfo=timezone.utc),
        snapshot=None,
        provider_id="local_file",
        license_scope="local_unverified",
        trust_level="local_unverified",
        adjusted_status="UNKNOWN",
    )
    artifact = tmp_path / "strategy_runs" / "run-route" / "route-strategy" / "market_data_integrity_result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(result.model_dump(mode="json")), encoding="utf-8")

    client = TestClient(create_app())
    response = client.get("/ui/market-data-integrity", params={"scan_root": str(tmp_path / "strategy_runs")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_market_data_integrity/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_network_calls"] is True
    assert payload["execution_authority"] == "none_read_plane"
    assert payload["artifact_count"] == 1
    assert payload["entries"][0]["strategy_id"] == "route-strategy"

    facade = client.get("/ui/facade").json()
    routes = {(route["method"], route["path"]): route for route in facade["routes"]}
    route = routes[("GET", "/ui/market-data-integrity")]
    assert route["kind"] == "read"
    assert route["auth_required"] is False
    assert route["payload_schema"] == "ui_market_data_integrity/v1"
