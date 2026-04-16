from __future__ import annotations

from pathlib import Path

ROUTES = [
    Path('strategy_validator/api/routes/adjudication.py'),
    Path('strategy_validator/api/routes/queue.py'),
    Path('strategy_validator/api/routes/rebuild.py'),
    Path('strategy_validator/api/routes/readiness.py'),
]


def test_api_routes_import_application_not_domain_internals() -> None:
    for path in ROUTES:
        text = path.read_text(encoding='utf-8')
        assert 'strategy_validator.application' in text
        assert 'strategy_validator.validator' not in text
        assert 'strategy_validator.control_plane' not in text
        assert 'strategy_validator.projections' not in text
