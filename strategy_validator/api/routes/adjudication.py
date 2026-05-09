from __future__ import annotations
from strategy_validator.api.routes._lazy_imports import lazy_callable

from fastapi import APIRouter



# Heavy application/read-plane dependencies are lazy-loaded to keep API import fast.
run_oracle_adjudication = lazy_callable('strategy_validator.application.api_adjudication_surfaces', 'run_oracle_adjudication')

router = APIRouter(prefix='/adjudication', tags=['adjudication'])


@router.get('/health')
def adjudication_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'adjudication',
        'entrypoint': run_oracle_adjudication.__name__,
    }
