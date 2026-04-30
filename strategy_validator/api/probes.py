from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, Response, status


def perform_readiness_check():
    """Lazily load runtime readiness so liveness probes stay lightweight.

    The module-level name is kept patchable for tests.  Importing the FastAPI
    probe registry must not eagerly import the full validator/readiness graph;
    only /readyz needs the heavy runtime self-check.
    """

    from strategy_validator.application.readiness import get_runtime_readiness_report

    return get_runtime_readiness_report()


def healthz() -> dict[str, object]:
    return {"ok": True, "service": "strategy-validator-api"}


def livez() -> dict[str, object]:
    return {"ok": True, "status": "alive"}


def readyz(response: Response) -> dict[str, object]:
    readiness = perform_readiness_check()
    payload = readiness.model_dump(mode="json") if hasattr(readiness, "model_dump") else readiness.dict() if hasattr(readiness, "dict") else dict(readiness)
    payload["ok"] = readiness.status == "READY"
    if readiness.status != "READY":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload


PROBE_ROUTES: tuple[tuple[str, Callable[..., dict[str, object]]], ...] = (
    ("/healthz", healthz),
    ("/livez", livez),
    ("/readyz", readyz),
)


def register_api_probes(app: FastAPI) -> FastAPI:
    for path, handler in PROBE_ROUTES:
        app.get(path)(handler)
    return app
