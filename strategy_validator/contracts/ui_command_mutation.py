from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UiOperatorCommandRequest(BaseModel):
    operator_id: str = 'operator'
    work_item_key: str | None = None
    review_target: str | None = None
    pack_kind: str | None = None
    manifest_path: str | None = None
    idempotency_key: str | None = None


class UiMutationAuthContext(BaseModel):
    runtime_mode: Literal['DEV', 'TEST', 'PRODUCTION']
    authorization_mode: Literal['NON_PRODUCTION_BYPASS', 'TOKEN']
    token_configured: bool
    token_source: Literal['authorization', 'x_strategy_validator_token', 'none'] = 'none'
    principal_id: str = 'anonymous'
    principal_source: Literal['operator_header', 'token', 'local_bypass', 'legacy_application', 'none'] = 'none'
    role: Literal['operator', 'admin', 'local', 'legacy', 'anonymous'] = 'anonymous'
    scopes: tuple[str, ...] = ()


__all__ = ['UiMutationAuthContext', 'UiOperatorCommandRequest']
