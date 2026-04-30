from __future__ import annotations

from typing import Any

from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest

_ALLOWED_ACTIONS = frozenset({'claim-item', 'acknowledge-reentry', 'renew-lease'})
_TARGET_REQUIRED_FOR_ALL_ACTIONS = frozenset({'work_item_key', 'review_target', 'manifest_path'})
_ACTION_LIFECYCLE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    'claim-item': ('target_identity', 'operator:command:write'),
    'acknowledge-reentry': ('target_identity', 'operator:command:write'),
    'renew-lease': ('target_identity', 'operator:command:write'),
}
_REQUIRED_WRITE_SCOPE = 'operator:command:write'


def _target_fields(request: UiOperatorCommandRequest) -> dict[str, str | None]:
    return {
        'work_item_key': request.work_item_key,
        'review_target': request.review_target,
        'pack_kind': request.pack_kind,
        'manifest_path': request.manifest_path,
    }


def _present_fields(target_fields: dict[str, str | None]) -> list[str]:
    return sorted(key for key, value in target_fields.items() if value)


def _target_identity_present(target_fields: dict[str, str | None]) -> bool:
    return any(target_fields.get(field) for field in _TARGET_REQUIRED_FOR_ALL_ACTIONS)


def build_ui_operator_command_policy(
    *,
    action: str,
    request: UiOperatorCommandRequest,
    auth_context: UiMutationAuthContext,
) -> dict[str, Any]:
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f'unsupported ui operator action: {action}')

    target_fields = _target_fields(request)
    target_fields_present = _present_fields(target_fields)
    blocking_reasons: list[str] = []
    if not request.operator_id or not str(request.operator_id).strip():
        blocking_reasons.append('operator_id is required')
    if not _target_identity_present(target_fields):
        blocking_reasons.append('at least one governed target field is required: work_item_key, review_target, or manifest_path')
    if request.idempotency_key is not None and not str(request.idempotency_key).strip():
        blocking_reasons.append('idempotency_key must be non-empty when provided')
    if auth_context.runtime_mode == 'PRODUCTION' and auth_context.authorization_mode != 'TOKEN':
        blocking_reasons.append('production operator commands require token authorization')
    if auth_context.authorization_mode == 'TOKEN' and not auth_context.token_configured:
        blocking_reasons.append('token authorization selected but no mutation token is configured')
    if auth_context.authorization_mode == 'TOKEN' and auth_context.token_source == 'none':
        blocking_reasons.append('token authorization selected but no token source was recorded')
    scopes = set(auth_context.scopes)
    if auth_context.authorization_mode == 'TOKEN' and not scopes:
        scopes = {_REQUIRED_WRITE_SCOPE}
    if auth_context.runtime_mode != 'PRODUCTION' and not scopes:
        scopes = {_REQUIRED_WRITE_SCOPE}
    if _REQUIRED_WRITE_SCOPE not in scopes:
        blocking_reasons.append(f'mutation auth context is missing required scope: {_REQUIRED_WRITE_SCOPE}')

    is_allowed = not blocking_reasons
    schema_version = (
        'ui_operator_command_policy/v2'
        if request.work_item_key and request.review_target
        else 'ui_operator_command_policy/v3'
    )
    return {
        'schema_version': schema_version,
        'action': action,
        'is_supported_action': True,
        'is_allowed': is_allowed,
        'lifecycle_state': 'ALLOWED' if is_allowed else 'BLOCKED',
        'blocking_reasons': blocking_reasons,
        'requirements': list(_ACTION_LIFECYCLE_REQUIREMENTS[action]),
        'requires_mutation_auth': True,
        'authorization_mode': auth_context.authorization_mode,
        'runtime_mode': auth_context.runtime_mode,
        'token_configured': auth_context.token_configured,
        'token_source': auth_context.token_source,
        'principal_id': auth_context.principal_id,
        'principal_source': auth_context.principal_source,
        'role': auth_context.role,
        'scopes': sorted(scopes),
        'required_scope': _REQUIRED_WRITE_SCOPE,
        'target_fields_present': target_fields_present,
        'operator_scope': {
            'operator_id': request.operator_id,
            'review_target': request.review_target,
        },
    }


def assert_ui_operator_command_allowed(policy: dict[str, Any]) -> None:
    if policy.get('is_allowed') is True:
        return
    reasons = policy.get('blocking_reasons') or ['operator command policy blocked the request']
    raise ValueError('; '.join(str(reason) for reason in reasons))


__all__ = ['assert_ui_operator_command_allowed', 'build_ui_operator_command_policy']
