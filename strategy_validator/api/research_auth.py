from __future__ import annotations

import os
from secrets import compare_digest

from fastapi import Header, HTTPException, Request, status

from strategy_validator.core.config import load_config
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.core.token_policy import is_placeholder_token

_ENV_API_TOKEN = "STRATEGY_VALIDATOR_API_TOKEN"
_ENV_RESEARCH_API_TOKEN = "STRATEGY_VALIDATOR_RESEARCH_API_TOKEN"
_ENV_ALLOW_REMOTE_RESEARCH_BYPASS = "STRATEGY_VALIDATOR_ALLOW_REMOTE_RESEARCH_BYPASS"
_LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return authorization.strip()


def _is_local_request(request: Request | None) -> bool:
    if request is None or request.client is None:
        return False
    return request.client.host in _LOCAL_CLIENT_HOSTS


def require_research_api_access(
    request: Request,
    authorization: str | None = Header(default=None),
    x_strategy_validator_token: str | None = Header(default=None),
) -> dict[str, object]:
    """Guard the research/advisory API surface.

    Research routes can build release, handoff, ingress and submission artifacts.
    They are intentionally kept callable from unit tests as plain Python
    functions, but HTTP access must not be an anonymous public surface.
    """
    cfg = load_config()
    research_token = os.environ.get(_ENV_RESEARCH_API_TOKEN, "").strip()
    mutation_token = os.environ.get(_ENV_API_TOKEN, "").strip()
    expected = research_token or mutation_token
    configured_token_name = _ENV_RESEARCH_API_TOKEN if research_token else _ENV_API_TOKEN if mutation_token else None

    if expected:
        if cfg.mode == RuntimeMode.PRODUCTION and is_placeholder_token(expected):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "RESEARCH_API_TOKEN_PLACEHOLDER"
                    if configured_token_name == _ENV_RESEARCH_API_TOKEN
                    else "MUTATION_TOKEN_PLACEHOLDER"
                ),
            )
        provided = (x_strategy_validator_token or _extract_bearer(authorization)).strip()
        if not provided or not compare_digest(provided, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_RESEARCH_API_TOKEN",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "authorization_mode": "TOKEN_PROTECTED",
            "runtime_mode": cfg.mode.value,
            "token_configured": True,
            "token_name": configured_token_name,
            "token_scope": "research" if configured_token_name == _ENV_RESEARCH_API_TOKEN else "mutation_compatibility",
        }

    if cfg.mode == RuntimeMode.PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RESEARCH_API_AUTH_NOT_CONFIGURED",
        )

    if _is_local_request(request):
        return {
            "authorization_mode": "LOCAL_NON_PRODUCTION_BYPASS",
            "runtime_mode": cfg.mode.value,
            "token_configured": False,
            "token_name": None,
            "token_scope": "local_bypass",
        }

    if _env_truthy(_ENV_ALLOW_REMOTE_RESEARCH_BYPASS):
        return {
            "authorization_mode": "REMOTE_NON_PRODUCTION_BYPASS",
            "runtime_mode": cfg.mode.value,
            "token_configured": False,
            "token_name": None,
            "token_scope": "remote_non_production_bypass",
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="REMOTE_NON_PRODUCTION_RESEARCH_BYPASS_FORBIDDEN",
    )


__all__ = ["require_research_api_access"]
