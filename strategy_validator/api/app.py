from __future__ import annotations

from fastapi import FastAPI

from strategy_validator.api.probes import register_api_probes, register_api_root_banner
from strategy_validator.api.route_registry import register_api_routes
from strategy_validator.api.security import install_security_envelope, install_ui_cors_middleware_if_configured


def create_app() -> FastAPI:
    """Create a freshly wired FastAPI application instance.

    Tests, OpenAPI snapshot generation, and production entrypoints all use the
    same factory so the route/security envelope cannot drift from the exported
    module-level ASGI app.
    """

    app = FastAPI(title='strategy-validator-api')
    install_security_envelope(app)
    install_ui_cors_middleware_if_configured(app)
    register_api_probes(app)
    register_api_root_banner(app)
    register_api_routes(app)
    return app


app = create_app()
