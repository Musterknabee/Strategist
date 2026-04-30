from __future__ import annotations

from pathlib import Path


def test_openapi_snapshot_contract_assets_exist() -> None:
    assert Path("scripts/openapi_contract_snapshot.py").exists()
    assert Path("docs/architecture/openapi.snapshot.json").exists()


def test_openapi_snapshot_script_targets_real_app_factory() -> None:
    app_source = Path("strategy_validator/api/app.py").read_text(encoding="utf-8")
    snapshot_source = Path("scripts/openapi_contract_snapshot.py").read_text(encoding="utf-8")

    assert "def create_app" in app_source
    assert "from strategy_validator.api.app import create_app" in snapshot_source
    assert "app = create_app()" in app_source
