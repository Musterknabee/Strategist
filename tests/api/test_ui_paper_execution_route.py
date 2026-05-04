from __future__ import annotations

from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload


def test_ui_public_facade_declares_paper_execution_routes() -> None:
    payload = build_ui_public_facade_inventory()
    routes = {(r["method"], r["path"], r["payload_schema"]) for r in payload["routes"]}
    assert ("GET", "/ui/paper-execution", "ui_paper_execution_cockpit/v1") in routes
    assert ("GET", "/ui/paper-execution/latest", "ui_paper_execution_cockpit/v1") in routes


def test_paper_execution_payload_contract_is_safe() -> None:
    payload = build_ui_paper_execution_cockpit_payload()
    assert payload["schema_version"] == "ui_paper_execution_cockpit/v1"
    assert payload["no_browser_orders"] is True
    assert payload["paper_submission_authority"] == "CLI_ONLY"
    assert payload["execution_authority"] == "NONE"
