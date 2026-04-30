from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.application.ui_command_policy import assert_ui_operator_command_allowed, build_ui_operator_command_policy
from strategy_validator.contracts.operator_action_journal import OperatorActionEvent
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest
from strategy_validator.ledger.operator_actions import append_operator_action_event, read_operator_action_events


def _model_payload(model) -> dict[str, Any]:
    if hasattr(model, 'model_dump'):
        try:
            return model.model_dump(mode='json')
        except TypeError:
            return model.model_dump()
    if hasattr(model, 'dict'):
        return model.dict()
    return dict(model)

_ALLOWED_ACTIONS = {
    'claim-item': 'Claim item command accepted for governed operator handling.',
    'acknowledge-reentry': 'Re-entry acknowledgement command accepted and queued for projection refresh.',
    'renew-lease': 'Lease renewal command accepted for governed claim coverage handling.',
}


def _legacy_receipt_auth_context() -> UiMutationAuthContext:
    # The public receipt builder is retained for compatibility with older
    # application/tests that journal directly instead of entering through the
    # token-aware API route.  It still uses the same command policy for command
    # shape/lifecycle enforcement; only route-level token provenance is absent.
    return UiMutationAuthContext(
        runtime_mode='TEST',
        authorization_mode='NON_PRODUCTION_BYPASS',
        token_configured=False,
        token_source='none',
        principal_id='legacy-application-operator',
        principal_source='legacy_application',
        role='legacy',
        scopes=('operator:command:write', 'operator:projection:read', 'legacy:application'),
    )


def _policy_checked_request(
    *,
    action: str,
    operator_id: str,
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[UiOperatorCommandRequest, dict[str, Any]]:
    request = UiOperatorCommandRequest(
        operator_id=operator_id,
        work_item_key=work_item_key,
        review_target=review_target,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
        idempotency_key=idempotency_key,
    )
    policy = build_ui_operator_command_policy(
        action=action,
        request=request,
        auth_context=_legacy_receipt_auth_context(),
    )
    assert_ui_operator_command_allowed(policy)
    return request, policy


def _target_payload_digest(target: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(target, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')).hexdigest()


def _command_target(
    *,
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
    idempotency_key: str | None = None,
    auth_context: UiMutationAuthContext | None = None,
) -> dict[str, Any]:
    target = {
        'work_item_key': work_item_key,
        'review_target': review_target,
        'pack_kind': pack_kind,
        'manifest_path': manifest_path,
        'idempotency_key': idempotency_key,
    }
    if auth_context is not None:
        target['authorization'] = _model_payload(auth_context)
    target['payload_digest'] = _target_payload_digest(target)
    return target


def _receipt_from_event(
    *,
    event: OperatorActionEvent,
    action: str,
    idempotency_status: str,
    auth_context: UiMutationAuthContext | None = None,
    duplicate_of_command_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'schema_version': 'ui_operator_command_receipt/v1',
        'generated_at_utc': event.created_at_utc.isoformat(),
        'command_id': event.action_event_id,
        'action': event.action,
        'accepted': event.accepted,
        'operator_id': event.operator_id,
        'execution_mode': 'JOURNALED_RECEIPT',
        'status': event.status,
        'requires_projection_refresh': True,
        'journal_family': 'operator_action_events',
        'event_hash': event.event_hash,
        'sequence_number': event.sequence_number,
        'previous_event_hash': event.previous_event_hash,
        'target': event.target_payload,
        'target_payload_digest': event.target_payload.get('payload_digest'),
        'summary_line': event.summary_line,
        'idempotency_status': idempotency_status,
        'authorization': _model_payload(auth_context or _legacy_receipt_auth_context()),
        'operator_message': (
            f'Command `{action}` was journaled as append-only operator evidence. '
            'Refresh the projection-backed workboard to observe downstream state materialization.'
        ),
    }
    if duplicate_of_command_id is not None:
        payload['duplicate_of_command_id'] = duplicate_of_command_id
        payload['operator_message'] = (
            f'Command `{action}` matched an existing idempotency key and returned the original journaled receipt.'
        )
    return payload

def _journal_ui_operator_command(
    *,
    action: str,
    request: UiOperatorCommandRequest,
    auth_context: UiMutationAuthContext,
) -> dict[str, Any]:
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f'unsupported ui operator action: {action}')
    target = _command_target(
        work_item_key=request.work_item_key,
        review_target=request.review_target,
        pack_kind=request.pack_kind,
        manifest_path=request.manifest_path,
        idempotency_key=request.idempotency_key,
        auth_context=auth_context,
    )
    if request.idempotency_key:
        existing = read_operator_action_events(idempotency_key=request.idempotency_key)
        if existing:
            prior = existing[0]
            if prior.action != action or prior.operator_id != request.operator_id or prior.target_payload != target:
                raise ValueError('idempotency key is already bound to a different operator command payload')
            return _receipt_from_event(
                event=prior,
                action=action,
                idempotency_status='REPLAYED',
                auth_context=auth_context,
                duplicate_of_command_id=prior.action_event_id,
            )
    event = append_operator_action_event(
        action=action,
        operator_id=request.operator_id,
        target=target,
        summary_line=_ALLOWED_ACTIONS[action],
    )
    return _receipt_from_event(event=event, action=action, idempotency_status='RECORDED', auth_context=auth_context)


def build_ui_operator_command_receipt_payload(
    *,
    action: str,
    operator_id: str = 'operator',
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f'unsupported ui operator action: {action}')

    request, policy = _policy_checked_request(
        action=action,
        operator_id=operator_id,
        work_item_key=work_item_key,
        review_target=review_target,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
        idempotency_key=idempotency_key,
    )
    target = _command_target(
        work_item_key=request.work_item_key,
        review_target=request.review_target,
        pack_kind=request.pack_kind,
        manifest_path=request.manifest_path,
        idempotency_key=request.idempotency_key,
        auth_context=_legacy_receipt_auth_context(),
    )

    if request.idempotency_key:
        existing = read_operator_action_events(idempotency_key=request.idempotency_key)
        if existing:
            prior = existing[0]
            if prior.action != action or prior.operator_id != request.operator_id or prior.target_payload != target:
                raise ValueError('idempotency key is already bound to a different operator command payload')
            payload = _receipt_from_event(
                event=prior,
                action=action,
                idempotency_status='REPLAYED',
                auth_context=_legacy_receipt_auth_context(),
                duplicate_of_command_id=prior.action_event_id,
            )
            payload['policy'] = policy
            return payload

    event = append_operator_action_event(
        action=action,
        operator_id=request.operator_id,
        target=target,
        summary_line=_ALLOWED_ACTIONS[action],
    )
    payload = _receipt_from_event(
        event=event,
        action=action,
        idempotency_status='RECORDED',
        auth_context=_legacy_receipt_auth_context(),
    )
    payload['policy'] = policy
    return payload


def execute_ui_operator_command(
    *,
    action: str,
    request: UiOperatorCommandRequest,
    auth_context: UiMutationAuthContext,
) -> dict[str, Any]:
    policy = build_ui_operator_command_policy(action=action, request=request, auth_context=auth_context)
    assert_ui_operator_command_allowed(policy)
    payload = _journal_ui_operator_command(action=action, request=request, auth_context=auth_context)
    payload['policy'] = policy
    payload['authorization'] = _model_payload(auth_context)
    return payload


__all__ = ['build_ui_operator_command_receipt_payload', 'execute_ui_operator_command']
