from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from strategy_validator.api.auth import require_mutation_auth
from strategy_validator.application.projection_backfill import backfill_all_registered_projections
from strategy_validator.core.path_guards import PathBoundaryError, resolve_within_root

router = APIRouter(prefix="/rebuild", tags=["rebuild"])


class ProjectionBackfillRequest(BaseModel):
    search_root: str
    repo_root: str | None = None


def _projection_rebuild_health_payload() -> dict[str, object]:
    return {
        "ok": True,
        "surface": "rebuild",
        "entrypoint": backfill_all_registered_projections.__name__,
        "mutation_route": "POST /rebuild/projection-backfill",
    }


@router.get("/health")
def projection_rebuild_health() -> dict[str, object]:
    return _projection_rebuild_health_payload()


@router.get("/projection-health")
def projection_health_compat() -> dict[str, object]:
    return _projection_rebuild_health_payload()


@router.post("/projection-backfill", dependencies=[Depends(require_mutation_auth)])
def projection_backfill(request: ProjectionBackfillRequest) -> dict[str, object]:
    repo_root = Path(request.repo_root).expanduser().resolve() if request.repo_root else Path(request.search_root).expanduser().resolve()
    try:
        search_root = resolve_within_root(request.search_root, root=repo_root, label="search_root")
    except PathBoundaryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return backfill_all_registered_projections(search_root=search_root, repo_root=repo_root)
