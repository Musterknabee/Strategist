from __future__ import annotations

import os
from typing import Any, Iterable, Literal

from strategy_validator.application.ui_command_policy import build_ui_operator_command_policy
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest
from strategy_validator.core.config import load_config
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.core.token_policy import DEFAULT_TOKEN_SCOPES, split_token_scopes

_SCHEMA_VERSION = "ui_operator_command_policy_projection/v1"
_ALLOWED_ACTIONS: tuple[str, ...] = ("claim-item", "acknowledge-reentry", "renew-lease")
_REQUIRED_SCOPE = "operator:command:write"
_ENV_API_TOKEN = "STRATEGY_VALIDATOR_API_TOKEN"
_ENV_API_TOKEN_SCOPES = "STRATEGY_VALIDATOR_API_TOKEN_SCOPES"
_LOCAL_BYPASS_SCOPES = ("operator:command:write", "operator:projection:read", "local:bypass")
_ALLOWED_ROLES = {"operator", "admin", "local", "legacy", "anonymous"}


def _clean(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalise_actions(actions: Iterable[str] | None) -> tuple[str, ...]:
    cleaned = tuple(dict.fromkeys(item.strip() for item in (actions or ()) if item and item.strip()))
    return cleaned or _ALLOWED_ACTIONS


def _safe_token_delivery(value: str | None) -> Literal["authorization", "x_strategy_validator_token"]:
    if value == "x_strategy_validator_token":
        return "x_strategy_validator_token"
    return "authorization"


def _safe_role(value: str | None, fallback: Literal["operator", "local", "anonymous"]) -> str:
    role = _clean(value)
    return role if role in _ALLOWED_ROLES else fallback


def build_current_ui_mutation_auth_context_for_policy_preview(
    *,
    assume_token_present: bool = False,
    token_delivery: str | None = "authorization",
    principal_id: str | None = None,
    role: str | None = None,
    scopes: Iterable[str] | None = None,
) -> UiMutationAuthContext:
    """Return a sanitized mutation-auth context for a read-only command policy preview.

    This helper intentionally never reads or returns the token value. It only exposes
    booleans/enums/scope names needed to explain whether a command shape would pass
    the same policy guard used by the mutation route.
    """

    cfg = load_config()
    runtime_mode = cfg.mode.value
    token_configured = bool(os.environ.get(_ENV_API_TOKEN, "").strip())
    explicit_scopes = tuple(sorted({str(scope).strip() for scope in (scopes or ()) if str(scope).strip()}))
    env_scopes = split_token_scopes(
        os.environ.get(_ENV_API_TOKEN_SCOPES, ""),
        default_when_empty=cfg.mode != RuntimeMode.PRODUCTION,
    )

    if token_configured:
        return UiMutationAuthContext(
            runtime_mode=runtime_mode,
            authorization_mode="TOKEN",
            token_configured=True,
            token_source=_safe_token_delivery(token_delivery) if assume_token_present else "none",
            principal_id=_clean(principal_id) or ("token-authenticated-operator" if assume_token_present else "policy-preview-no-token"),
            principal_source="token" if assume_token_present else "none",
            role=_safe_role(role, "operator"),
            scopes=explicit_scopes or env_scopes,
        )

    if cfg.mode != RuntimeMode.PRODUCTION:
        return UiMutationAuthContext(
            runtime_mode=runtime_mode,
            authorization_mode="NON_PRODUCTION_BYPASS",
            token_configured=False,
            token_source="none",
            principal_id=_clean(principal_id) or "local-non-production-operator",
            principal_source="local_bypass",
            role=_safe_role(role, "local"),
            scopes=explicit_scopes or _LOCAL_BYPASS_SCOPES,
        )

    return UiMutationAuthContext(
        runtime_mode=runtime_mode,
        authorization_mode="TOKEN",
        token_configured=False,
        token_source="none",
        principal_id=_clean(principal_id) or "policy-preview-missing-token",
        principal_source="none",
        role=_safe_role(role, "anonymous"),
        scopes=explicit_scopes,
    )


def _request_for_policy(
    *,
    operator_id: str | None,
    work_item_key: str | None,
    review_target: str | None,
    pack_kind: str | None,
    manifest_path: str | None,
    idempotency_key: str | None,
) -> UiOperatorCommandRequest:
    return UiOperatorCommandRequest(
        operator_id=_clean(operator_id) or "",
        work_item_key=_clean(work_item_key),
        review_target=_clean(review_target),
        pack_kind=_clean(pack_kind),
        manifest_path=_clean(manifest_path),
        idempotency_key=_clean(idempotency_key),
    )


def _unsupported_policy(action: str) -> dict[str, Any]:
    return {
        "schema_version": "ui_operator_command_policy/unsupported",
        "action": action,
        "is_supported_action": False,
        "is_allowed": False,
        "lifecycle_state": "BLOCKED",
        "blocking_reasons": [f"unsupported ui operator action: {action}"],
        "requirements": [],
        "requires_mutation_auth": True,
        "required_scope": _REQUIRED_SCOPE,
        "target_fields_present": [],
    }


def build_ui_operator_command_policy_projection(
    *,
    actions: Iterable[str] | None = None,
    operator_id: str = "operator",
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
    idempotency_key: str | None = None,
    auth_context: UiMutationAuthContext | None = None,
    assume_token_present: bool = False,
    token_delivery: str | None = "authorization",
    principal_id: str | None = None,
    role: str | None = None,
    scopes: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a read-only policy matrix for governed UI operator commands."""

    request = _request_for_policy(
        operator_id=operator_id,
        work_item_key=work_item_key,
        review_target=review_target,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
        idempotency_key=idempotency_key,
    )
    context = auth_context or build_current_ui_mutation_auth_context_for_policy_preview(
        assume_token_present=assume_token_present,
        token_delivery=token_delivery,
        principal_id=principal_id,
        role=role,
        scopes=scopes,
    )
    requested_actions = _normalise_actions(actions)
    policies: list[dict[str, Any]] = []
    for action in requested_actions:
        if action not in _ALLOWED_ACTIONS:
            policies.append(_unsupported_policy(action))
            continue
        policies.append(build_ui_operator_command_policy(action=action, request=request, auth_context=context))

    allowed_count = sum(1 for item in policies if item.get("is_allowed") is True)
    blocked_count = len(policies) - allowed_count
    unsupported_count = sum(1 for item in policies if item.get("is_supported_action") is False)
    target_fields_present = sorted(
        key
        for key, value in {
            "work_item_key": request.work_item_key,
            "review_target": request.review_target,
            "pack_kind": request.pack_kind,
            "manifest_path": request.manifest_path,
        }.items()
        if value
    )
    target_identity_present = any(field in {"work_item_key", "review_target", "manifest_path"} for field in target_fields_present)

    return {
        "schema_version": _SCHEMA_VERSION,
        "read_plane_only": True,
        "mutation_route": "/ui/commands/{action}",
        "mutation_authority": "POST /ui/commands/{action} with mutation auth only",
        "journal_family": "operator_action_events",
        "no_token_value_echoed": True,
        "supported_actions": list(_ALLOWED_ACTIONS),
        "required_scope": _REQUIRED_SCOPE,
        "default_token_scopes": list(DEFAULT_TOKEN_SCOPES),
        "assume_token_present": bool(assume_token_present),
        "requested_actions": list(requested_actions),
        "action_count": len(policies),
        "allowed_count": allowed_count,
        "blocked_count": blocked_count,
        "unsupported_count": unsupported_count,
        "overall_lifecycle_state": "ALLOWED" if policies and blocked_count == 0 else "BLOCKED",
        "target_identity_present": target_identity_present,
        "target_fields_present": target_fields_present,
        "request": {
            "operator_id": request.operator_id,
            "work_item_key": request.work_item_key,
            "review_target": request.review_target,
            "pack_kind": request.pack_kind,
            "manifest_path": request.manifest_path,
            "idempotency_key_present": bool(request.idempotency_key),
        },
        "auth_context": {
            "runtime_mode": context.runtime_mode,
            "authorization_mode": context.authorization_mode,
            "token_configured": context.token_configured,
            "token_source": context.token_source,
            "principal_id": context.principal_id,
            "principal_source": context.principal_source,
            "role": context.role,
            "scopes": sorted(context.scopes),
        },
        "operator_guidance": [
            "This read-plane preview never accepts or stores a mutation token.",
            "Actual command execution remains restricted to POST /ui/commands/{action}.",
            "A governed target requires at least one of work_item_key, review_target, or manifest_path.",
        ],
        "policies": policies,
    }


__all__ = [
    "build_current_ui_mutation_auth_context_for_policy_preview",
    "build_ui_operator_command_policy_projection",
]
