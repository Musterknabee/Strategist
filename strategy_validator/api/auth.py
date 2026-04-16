from __future__ import annotations

import os
from secrets import compare_digest

from fastapi import Header, HTTPException, status

from strategy_validator.core.config import load_config
from strategy_validator.core.enums import RuntimeMode

_ENV_API_TOKEN = 'STRATEGY_VALIDATOR_API_TOKEN'


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ''
    prefix = 'Bearer '
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return authorization.strip()


def require_mutation_auth(
    authorization: str | None = Header(default=None),
    x_strategy_validator_token: str | None = Header(default=None),
) -> None:
    cfg = load_config()
    expected = os.environ.get(_ENV_API_TOKEN, '').strip()

    if cfg.mode != RuntimeMode.PRODUCTION and not expected:
        return

    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='MUTATION_AUTH_NOT_CONFIGURED',
        )

    provided = (x_strategy_validator_token or _extract_bearer(authorization)).strip()
    if not provided or not compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='INVALID_MUTATION_TOKEN',
            headers={'WWW-Authenticate': 'Bearer'},
        )
