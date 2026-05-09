from __future__ import annotations

from importlib import import_module

from strategy_validator.api.routes import ui_routes_detail_runtime as legacy_runtime


FAMILY_MODULES = (
    "strategy_validator.api.routes.ui_routes_detail_core",
    "strategy_validator.api.routes.ui_routes_detail_semantic_handoff",
    "strategy_validator.api.routes.ui_routes_detail_clearance",
    "strategy_validator.api.routes.ui_routes_detail_clearance_release",
    "strategy_validator.api.routes.ui_routes_detail_strategy_paper",
    "strategy_validator.api.routes.ui_routes_detail_research_os",
)


def test_ui_detail_runtime_aggregates_family_routers_without_losing_routes() -> None:
    family_paths: set[str] = set()
    for module_name in FAMILY_MODULES:
        module = import_module(module_name)
        assert module.router.routes, module_name
        family_paths.update(route.path for route in module.router.routes)

    aggregate_paths = {route.path for route in legacy_runtime.router.routes}
    assert aggregate_paths == family_paths
    assert "/burnin" in aggregate_paths
    assert "/semantic-validator-handoff/clearance-release-disposal-board" in aggregate_paths
    assert "/research-os/status" in aggregate_paths


def test_legacy_detail_runtime_reexports_endpoint_functions_and_monkeypatch_surface(monkeypatch) -> None:
    monkeypatch.setattr(
        legacy_runtime,
        "build_ui_runtime_status_payload",
        lambda **kwargs: {
            "schema_version": "ui_runtime_status/v1",
            "persona": {"active_role": kwargs["role"]},
        },
    )

    payload = legacy_runtime.get_ui_runtime(role="auditor")

    assert payload["schema_version"] == "ui_runtime_status/v1"
    assert payload["persona"]["active_role"] == "auditor"


def test_detail_runtime_source_documents_decomposition_contract() -> None:
    source = legacy_runtime.__loader__.get_source(legacy_runtime.__name__) or ""
    assert "router.include_router(core_router)" in source
    assert "router.include_router(semantic_handoff_router)" in source
    assert "router.include_router(clearance_router)" in source
    assert "router.include_router(clearance_release_router)" in source
    assert "router.include_router(strategy_paper_router)" in source
    assert "router.include_router(research_os_router)" in source
    assert "static route-contract compatibility only" in source
