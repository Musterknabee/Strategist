from __future__ import annotations
from strategy_validator.api.routes._lazy_imports import lazy_callable

from fastapi import APIRouter



# Heavy application/read-plane dependencies are lazy-loaded to keep API import fast.
build_governance_queue = lazy_callable('strategy_validator.application.api_queue_surfaces', 'build_governance_queue')
query_operator_queue = lazy_callable('strategy_validator.application.api_queue_surfaces', 'query_operator_queue')

router = APIRouter(prefix='/queue', tags=['queue'])


@router.get('/health')
def queue_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'queue',
        'entrypoints': [build_governance_queue.__name__, query_operator_queue.__name__],
    }
