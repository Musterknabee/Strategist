from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from strategy_validator.api.routes.adjudication import router as adjudication_router
from strategy_validator.api.routes.queue import router as queue_router
from strategy_validator.api.routes.readiness import router as readiness_router
from strategy_validator.api.routes.ui import router as ui_router
from strategy_validator.api.routes.rebuild import router as rebuild_router
from strategy_validator.application import get_readiness_health_payload

app = FastAPI(title='strategy-validator-api')


@app.get('/healthz')
def healthz() -> dict[str, object]:
    return {'ok': True, 'service': 'strategy-validator-api'}


@app.get('/livez')
def livez() -> dict[str, object]:
    return {'ok': True, 'status': 'alive'}


@app.get('/readyz')
def readyz() -> dict[str, object]:
    payload = get_readiness_health_payload()
    status_code = 200 if payload.get('ok') else 503
    return JSONResponse(status_code=status_code, content=payload)


app.include_router(adjudication_router)
app.include_router(queue_router)
app.include_router(rebuild_router)
app.include_router(readiness_router)
app.include_router(ui_router)
