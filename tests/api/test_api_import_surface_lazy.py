from __future__ import annotations

from pathlib import Path


ROUTE_PATHS = (
    Path("strategy_validator/api/routes/ui_routes_detail_runtime.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_core.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_semantic_handoff.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_clearance.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_clearance_release.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_strategy_paper.py"),
    Path("strategy_validator/api/routes/ui_routes_detail_research_os.py"),
    Path("strategy_validator/api/routes/research.py"),
    Path("strategy_validator/api/routes/research_bundle.py"),
    Path("strategy_validator/api/routes/research_handoff.py"),
    Path("strategy_validator/api/routes/research_release.py"),
    Path("strategy_validator/api/routes/research_submission.py"),
)


def test_route_modules_use_lazy_application_surface_imports() -> None:
    for route_path in ROUTE_PATHS:
        source = route_path.read_text(encoding="utf-8")
        assert ("lazy_callable(" in source or "legacy_callable(" in source)
        assert "from strategy_validator.application.research_integrity" not in source
        assert "from strategy_validator.application.api_ui_surfaces" not in source
        assert "from strategy_validator.application.paper_execution_cockpit" not in source


def test_research_routes_declare_lazy_semantic_contract_validation() -> None:
    research_paths = ROUTE_PATHS[7:]
    for route_path in research_paths:
        source = route_path.read_text(encoding="utf-8")
        assert "lazy_model(" in source
        assert "from strategy_validator.contracts.semantic" not in source
        assert "from strategy_validator.contracts.experiments" not in source
        assert "from strategy_validator.contracts.evidence" not in source


def test_lazy_import_helper_exposes_callable_and_model_proxies() -> None:
    source = Path("strategy_validator/api/routes/_lazy_imports.py").read_text(encoding="utf-8")
    assert "def lazy_callable(" in source
    assert "def lazy_model(" in source
    assert "def model_validate(" in source
