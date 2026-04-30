from __future__ import annotations

from pathlib import Path

ROUTE_IMPORTS = {
    Path('strategy_validator/api/routes/ui.py'): 'strategy_validator.application.api_ui_surfaces',
    Path('strategy_validator/api/routes/queue.py'): 'strategy_validator.application.api_queue_surfaces',
    Path('strategy_validator/api/routes/adjudication.py'): 'strategy_validator.application.api_adjudication_surfaces',
}


def test_api_routes_use_bounded_application_surfaces() -> None:
    for path, expected_import in ROUTE_IMPORTS.items():
        text = path.read_text(encoding='utf-8')
        assert expected_import in text
        assert 'from strategy_validator.application import ' not in text
