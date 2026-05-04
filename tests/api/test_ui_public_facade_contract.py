from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_ui_public_facade_route_is_backed_by_application_inventory():
    route=(ROOT/"strategy_validator/api/routes/ui.py").read_text()
    app=(ROOT/"strategy_validator/application/ui_public_facade.py").read_text()
    assert "@router.get('/facade')" in route or '@router.get("/facade")' in route
    assert "build_ui_public_facade_inventory" in route
    assert "def build_ui_public_facade_inventory" in app
    assert "strategy_validator.validator" not in route
