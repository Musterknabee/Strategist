from __future__ import annotations

from collections.abc import Iterable

from fastapi import FastAPI
from fastapi.routing import APIRouter

from strategy_validator.api.routes.adjudication import router as adjudication_router
from strategy_validator.api.routes.queue import router as queue_router
from strategy_validator.api.routes.readiness import router as readiness_router
from strategy_validator.api.routes.research import router as research_router
from strategy_validator.api.routes.rebuild import router as rebuild_router
from strategy_validator.api.routes.ui import router as ui_router

_API_ROUTERS: tuple[APIRouter, ...] = (
    adjudication_router,
    queue_router,
    rebuild_router,
    readiness_router,
    research_router,
)


def iter_api_routers() -> Iterable[APIRouter]:
    return _API_ROUTERS



def register_api_routes(app: FastAPI) -> FastAPI:
    for router in iter_api_routers():
        app.include_router(router)
    app.include_router(ui_router)
    return app
