from __future__ import annotations

from pathlib import Path


def test_api_entrypoint_invokes_production_startup_guard_before_uvicorn() -> None:
    source = (Path(__file__).resolve().parents[2] / 'strategy_validator' / 'cli' / 'api.py').read_text(encoding='utf-8')
    guard_call = source.index('_fail_if_production_startup_is_not_ready()')
    uvicorn_import = source.index('import uvicorn')
    assert guard_call < uvicorn_import
    assert 'perform_readiness_check' in source
    assert 'refused to start in PRODUCTION' in source
