from __future__ import annotations

import os
import re
from secrets import compare_digest

from fastapi import Header, HTTPException, Request, status

from strategy_validator.contracts.operational import MutationSafetyStatus
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext
from strategy_validator.core.config import load_config
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.core.token_policy import (
    DEFAULT_TOKEN_SCOPES,
    is_placeholder_token,
    missing_required_mutation_scopes,
    split_token_scopes,
)

_ENV_API_TOKEN = "STRATEGY_VALIDATOR_API_TOKEN"
_ENV_API_TOKEN_SCOPES = "STRATEGY_VALIDATOR_API_TOKEN_SCOPES"
_ENV_ALLOW_REMOTE_NON_PROD_BYPASS = "STRATEGY_VALIDATOR_ALLOW_REMOTE_NON_PRODUCTION_MUTATION_BYPASS"
_LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
_MAX_PRINCIPAL_ID_LENGTH = 128
_PRINCIPAL_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]+$")
_DEFAULT_TOKEN_SCOPES = DEFAULT_TOKEN_SCOPES
_LOCAL_BYPASS_SCOPES = ("operator:command:write", "operator:projection:read", "local:bypass")


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _is_local_request(request: Request | None) -> bool:
    if request is None or request.client is None:
        return False
    return request.client.host in _LOCAL_CLIENT_HOSTS


def _scopes_from_env(*, default_when_empty: bool = True) -> tuple[str, ...]:
    return split_token_scopes(os.environ.get(_ENV_API_TOKEN_SCOPES, ""), default_when_empty=default_when_empty)


def get_mutation_auth_runtime_status() -> MutationSafetyStatus:
    cfg = load_config()
    expected = os.environ.get(_ENV_API_TOKEN, "").strip()
    runtime_mode = cfg.mode

    if expected:
        scopes = _scopes_from_env(default_when_empty=cfg.mode != RuntimeMode.PRODUCTION)
        if cfg.mode == RuntimeMode.PRODUCTION and is_placeholder_token(expected):
            return MutationSafetyStatus(
                runtime_mode=runtime_mode,
                authorization_mode="MISCONFIGURED",
                token_configured=True,
                mutation_routes_safe=False,
                detail_code="MUTATION_TOKEN_PLACEHOLDER",
            )
        if cfg.mode == RuntimeMode.PRODUCTION and missing_required_mutation_scopes(scopes):
            return MutationSafetyStatus(
                runtime_mode=runtime_mode,
                authorization_mode="MISCONFIGURED",
                token_configured=True,
                mutation_routes_safe=False,
                detail_code="MUTATION_TOKEN_SCOPES_MISSING",
            )
        return MutationSafetyStatus(
            runtime_mode=runtime_mode,
            authorization_mode="TOKEN_PROTECTED",
            token_configured=True,
            mutation_routes_safe=True,
            detail_code="MUTATION_TOKEN_CONFIGURED",
        )

    if cfg.mode != RuntimeMode.PRODUCTION:
        remote_bypass_enabled = _env_truthy(_ENV_ALLOW_REMOTE_NON_PROD_BYPASS)
        return MutationSafetyStatus(
            runtime_mode=runtime_mode,
            authorization_mode="NON_PRODUCTION_BYPASS",
            token_configured=False,
            mutation_routes_safe=remote_bypass_enabled,
            detail_code=(
                "REMOTE_NON_PRODUCTION_MUTATION_BYPASS_ENABLED"
                if remote_bypass_enabled
                else "LOCAL_ONLY_NON_PRODUCTION_MUTATION_BYPASS"
            ),
        )

    return MutationSafetyStatus(
        runtime_mode=runtime_mode,
        authorization_mode="MISCONFIGURED",
        token_configured=False,
        mutation_routes_safe=False,
        detail_code="MUTATION_AUTH_NOT_CONFIGURED",
    )


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return authorization.strip()


def _normalize_principal_id(value: str) -> str:
    candidate = str(value or '').strip()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_OPERATOR_PRINCIPAL")
    if len(candidate) > _MAX_PRINCIPAL_ID_LENGTH or not _PRINCIPAL_ID_RE.fullmatch(candidate):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_OPERATOR_PRINCIPAL")
    return candidate


def _principal_from_headers(
    *,
    x_strategy_validator_operator: str | None,
    token_authorized: bool,
    local_bypass: bool,
    token_scopes: tuple[str, ...] | None = None,
) -> tuple[str, str, str, tuple[str, ...]]:
    candidate = (x_strategy_validator_operator or '').strip()
    if candidate:
        return _normalize_principal_id(candidate), 'operator_header', 'operator', token_scopes or (() if token_authorized else _LOCAL_BYPASS_SCOPES)
    if token_authorized:
        return 'token-authenticated-operator', 'token', 'operator', token_scopes or ()
    if local_bypass:
        return 'local-non-production-operator', 'local_bypass', 'local', _LOCAL_BYPASS_SCOPES
    return 'anonymous', 'none', 'anonymous', ()


def require_mutation_auth(
    request: Request,
    authorization: str | None = Header(default=None),
    x_strategy_validator_token: str | None = Header(default=None),
    x_strategy_validator_operator: str | None = Header(default=None),
) -> UiMutationAuthContext:
    cfg = load_config()
    expected = os.environ.get(_ENV_API_TOKEN, "").strip()
    runtime_mode = cfg.mode.value

    if cfg.mode != RuntimeMode.PRODUCTION and not expected:
        if _is_local_request(request) or _env_truthy(_ENV_ALLOW_REMOTE_NON_PROD_BYPASS):
            principal_id, principal_source, role, scopes = _principal_from_headers(
                x_strategy_validator_operator=x_strategy_validator_operator,
                token_authorized=False,
                local_bypass=True,
            )
            return UiMutationAuthContext(
                runtime_mode=runtime_mode,
                authorization_mode="NON_PRODUCTION_BYPASS",
                token_configured=False,
                token_source="none",
                principal_id=principal_id,
                principal_source=principal_source,
                role=role,
                scopes=scopes,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="REMOTE_NON_PRODUCTION_MUTATION_BYPASS_FORBIDDEN",
        )

    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MUTATION_AUTH_NOT_CONFIGURED",
        )

    token_scopes = _scopes_from_env(default_when_empty=cfg.mode != RuntimeMode.PRODUCTION)
    if cfg.mode == RuntimeMode.PRODUCTION and is_placeholder_token(expected):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MUTATION_TOKEN_PLACEHOLDER",
        )
    if cfg.mode == RuntimeMode.PRODUCTION and missing_required_mutation_scopes(token_scopes):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MUTATION_TOKEN_SCOPES_MISSING",
        )

    token_source = "x_strategy_validator_token" if x_strategy_validator_token else "authorization" if authorization else "none"
    provided = (x_strategy_validator_token or _extract_bearer(authorization)).strip()
    if not provided or not compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_MUTATION_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    principal_id, principal_source, role, scopes = _principal_from_headers(
        x_strategy_validator_operator=x_strategy_validator_operator,
        token_authorized=True,
        local_bypass=False,
        token_scopes=token_scopes,
    )
    return UiMutationAuthContext(
        runtime_mode=runtime_mode,
        authorization_mode="TOKEN",
        token_configured=True,
        token_source=token_source,
        principal_id=principal_id,
        principal_source=principal_source,
        role=role,
        scopes=scopes,
    )
