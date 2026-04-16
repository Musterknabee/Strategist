from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from strategy_validator.api.auth import require_mutation_auth
from strategy_validator.application.projection_backfill import backfill_all_registered_projections

router = APIRouter(prefix='/rebuild', tags=['rebuild'])


class ProjectionBackfillRequest(BaseModel):
    search_root: str
    repo_root: str | None = None


def _projection_rebuild_health_payload() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'rebuild',
        'entrypoint': backfill_all_registered_projections.__name__,
        'mutation_route': 'POST /rebuild/projection-backfill',
    }


@router.get('/health')
def projection_rebuild_health() -> dict[str, object]:
    return _projection_rebuild_health_payload()


@router.get('/projection-health')
def projection_health_compat() -> dict[str, object]:
    return _projection_rebuild_health_payload()


@router.post('/projection-backfill', dependencies=[Depends(require_mutation_auth)])
def projection_backfill(request: ProjectionBackfillRequest) -> dict[str, object]:
    search_root = Path(request.search_root)
    repo_root = Path(request.repo_root) if request.repo_root else search_root
    return backfill_all_registered_projections(search_root=search_root, repo_root=repo_root)
