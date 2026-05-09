from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory


def test_ui_pack_workbench_route_uses_read_model_service(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_build_operator_pack_workbench_payload(**kwargs):
        captured.update(kwargs)
        return {
            "schema_version": "oracle_operator_pack_workbench/v1",
            "search_root": str(kwargs["search_root"]),
            "pack_kinds": list(kwargs["pack_kinds"]),
            "trust_statuses": list(kwargs["trust_statuses"]),
            "summary_line_contains": kwargs["summary_line_contains"],
            "output_artifact_label_contains": kwargs["output_artifact_label_contains"],
            "total_item_count": 1,
            "column_count": 1,
            "columns": [],
        }

    monkeypatch.setattr(
        "strategy_validator.api.routes.ui_routes_detail_runtime.build_operator_pack_workbench_payload",
        fake_build_operator_pack_workbench_payload,
    )
    client = TestClient(app)
    response = client.get(
        "/ui/packs/workbench",
        params=[
            ("search_root", "/tmp/operator-packs"),
            ("pack_kind", "briefing_pack"),
            ("trust_status", "TRUSTED"),
            ("summary_line_contains", "daily"),
            ("output_artifact_label_contains", "markdown"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "oracle_operator_pack_workbench/v1"
    assert payload["pack_kinds"] == ["briefing_pack"]
    assert payload["trust_statuses"] == ["TRUSTED"]
    assert payload["summary_line_contains"] == "daily"
    assert payload["output_artifact_label_contains"] == "markdown"
    assert str(captured["search_root"]) == "/tmp/operator-packs"


def test_ui_facade_declares_pack_workbench_as_read_plane() -> None:
    payload = build_ui_public_facade_inventory()
    routes = {(route["method"], route["path"]): route for route in payload["routes"]}

    route = routes[("GET", "/ui/packs/workbench")]
    assert route["kind"] == "read"
    assert route["auth_required"] is False
    assert route["payload_schema"] == "oracle_operator_pack_workbench/v1"
