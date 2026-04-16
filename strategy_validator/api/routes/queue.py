from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.application import build_governance_queue, query_operator_queue

router = APIRouter(prefix='/queue', tags=['queue'])


@router.get('/health')
def queue_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'queue',
        'entrypoints': [build_governance_queue.__name__, query_operator_queue.__name__],
    }
