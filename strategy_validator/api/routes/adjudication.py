from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.application import run_oracle_adjudication

router = APIRouter(prefix='/adjudication', tags=['adjudication'])


@router.get('/health')
def adjudication_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'adjudication',
        'entrypoint': run_oracle_adjudication.__name__,
    }
