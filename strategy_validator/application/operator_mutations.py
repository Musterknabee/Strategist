from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

from strategy_validator.application.operator_pack_assembly import (
    build_pack_claim_lease_payload,
    build_pack_claim_lifecycle_payload,
)
from strategy_validator.application.operator_event_log import append_operator_command_event
from strategy_validator.application.operator_queue import query_operator_queue
from strategy_validator.application.operator_queue_commands import build_queue_snapshot, build_workboard_payload
from strategy_validator.control_plane.operator_reentry_acceptance import (
    build_operator_reentry_acceptance_request,
    materialize_operator_reentry_acceptance,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workboard_entry(*, work_item_key: str) -> dict[str, Any]:
    workboard = build_workboard_payload(board_label='operator')
    for entry in workboard.get('entries', []):
        if entry.get('work_item_key') == work_item_key:
            return entry
    raise ValueError(f'unknown operator work item: {work_item_key}')


def _require_target(action: str, *, work_item_key: str | None, pack_kind: str | None, manifest_path: str | None) -> tuple[str, str | None]:
    if not work_item_key:
        raise ValueError(f'{action} requires work_item_key')
    if not pack_kind and not manifest_path:
        raise ValueError(f'{action} requires pack_kind or manifest_path')
    return work_item_key, manifest_path


def _claim_context(*, action: str, work_item_key: str | None, pack_kind: str | None, manifest_path: str | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    work_item_key, manifest_path = _require_target(action, work_item_key=work_item_key, pack_kind=pack_kind, manifest_path=manifest_path)
    entry = _workboard_entry(work_item_key=work_item_key)
    root = Path.cwd()
    common = {
        'search_root': root,
        'repo_root': root,
        'current_pack_kind': pack_kind,
        'pack_kinds': [pack_kind] if pack_kind else [],
        'queue_key': entry.get('queue_key'),
        'review_target': entry.get('review_target'),
        'priority_band': entry.get('priority_band'),
        'action_owner_lane': entry.get('action_owner_lane'),
        'board_label': 'operator',
        'ack_owner_lane': entry.get('action_owner_lane'),
        'max_items': 1,
    }
    claim_lease = build_pack_claim_lease_payload(**common)
    lifecycle = build_pack_claim_lifecycle_payload(**common)
    claim_item = next(iter(claim_lease.get('items', [])), None)
    lifecycle_item = next(iter(lifecycle.get('items', [])), None)
    if claim_item is None or lifecycle_item is None:
        raise ValueError(f'no governed pack state found for {action}')
    if manifest_path and claim_item.get('latest_manifest_path') != manifest_path:
        raise ValueError(f'{action} target manifest does not match the governed claim surface')
    return entry, claim_item, lifecycle_item


def _claim_item_receipt(
    *,
    operator_id: str,
    work_item_key: str | None,
    review_target: str | None,
    pack_kind: str | None,
    manifest_path: str | None,
) -> dict[str, Any]:
    entry, claim_item, _ = _claim_context(
        action='claim-item',
        work_item_key=work_item_key,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    )
    accepted = claim_item.get('claim_state') != 'CLAIM_ACTIVE' and claim_item.get('lease_action') != 'NO_LEASE_ACTION'
    summary_line = (
        f"Governed claim-item {'accepted' if accepted else 'withheld'} for `{claim_item['pack_kind']}` "
        f"with claim_state={claim_item['claim_state']} and lease_action={claim_item['lease_action']}."
    )
    return {
        'schema_version': 'ui_operator_command_receipt/v1',
        'generated_at_utc': _utc_now(),
        'command_id': f'ui-cmd-{uuid4().hex}',
        'action': 'claim-item',
        'accepted': accepted,
        'operator_id': operator_id,
        'execution_mode': 'GOVERNED_MUTATION_PREVIEW',
        'requires_projection_refresh': False,
        'target': {
            'work_item_key': work_item_key,
            'review_target': review_target or entry.get('review_target'),
            'pack_kind': pack_kind or claim_item.get('pack_kind'),
            'manifest_path': manifest_path or claim_item.get('latest_manifest_path'),
        },
        'governance': {
            'surface': 'claim_lease',
            'claim_state': claim_item.get('claim_state'),
            'lease_state': claim_item.get('lease_state'),
            'lease_action': claim_item.get('lease_action'),
            'lease_key': claim_item.get('lease_key'),
            'recommended_actions': claim_item.get('recommended_actions', []),
        },
        'summary_line': summary_line,
        'operator_message': summary_line,
    }


def _renew_lease_receipt(
    *,
    operator_id: str,
    work_item_key: str | None,
    review_target: str | None,
    pack_kind: str | None,
    manifest_path: str | None,
) -> dict[str, Any]:
    entry, claim_item, lifecycle_item = _claim_context(
        action='renew-lease',
        work_item_key=work_item_key,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    )
    accepted = lifecycle_item.get('renewal_action') in {'RENEW_CLAIM', 'ACQUIRE_AND_RENEW'}
    summary_line = (
        f"Governed renew-lease {'accepted' if accepted else 'withheld'} for `{lifecycle_item['pack_kind']}` "
        f"with lifecycle_state={lifecycle_item['lifecycle_state']} and renewal_action={lifecycle_item['renewal_action']}."
    )
    return {
        'schema_version': 'ui_operator_command_receipt/v1',
        'generated_at_utc': _utc_now(),
        'command_id': f'ui-cmd-{uuid4().hex}',
        'action': 'renew-lease',
        'accepted': accepted,
        'operator_id': operator_id,
        'execution_mode': 'GOVERNED_MUTATION_PREVIEW',
        'requires_projection_refresh': False,
        'target': {
            'work_item_key': work_item_key,
            'review_target': review_target or entry.get('review_target'),
            'pack_kind': pack_kind or claim_item.get('pack_kind'),
            'manifest_path': manifest_path or claim_item.get('latest_manifest_path'),
        },
        'governance': {
            'surface': 'claim_lifecycle',
            'claim_state': claim_item.get('claim_state'),
            'lease_state': claim_item.get('lease_state'),
            'lifecycle_state': lifecycle_item.get('lifecycle_state'),
            'renewal_action': lifecycle_item.get('renewal_action'),
            'expiry_action': lifecycle_item.get('expiry_action'),
            'recommended_actions': lifecycle_item.get('recommended_actions', []),
        },
        'summary_line': summary_line,
        'operator_message': summary_line,
    }


def _acknowledge_reentry_receipt(
    *,
    operator_id: str,
    work_item_key: str | None,
    review_target: str | None,
    pack_kind: str | None,
    manifest_path: str | None,
) -> dict[str, Any]:
    if not work_item_key:
        raise ValueError('acknowledge-reentry requires work_item_key')
    with TemporaryDirectory(prefix='operator-reentry-acceptance-') as temp_dir:
        acceptance = materialize_operator_reentry_acceptance(
            build_operator_reentry_acceptance_request(
                acceptance_root=Path(temp_dir),
                board_label='operator',
                accepted_at_utc=datetime.now(timezone.utc),
            ),
            operator_queue_query_result=query_operator_queue(
                operator_queue_snapshot=build_queue_snapshot(
                    issued_at_utc=datetime.now(timezone.utc),
                    surface_label='ui-command',
                )
            ),
            board_label='operator',
        )
        item = next((candidate for candidate in acceptance.items if candidate.work_item_key == work_item_key), None)
    if item is None:
        raise ValueError(f'unknown reentry work item: {work_item_key}')
    accepted = item.acknowledgement_state in {'ACKNOWLEDGED_ACCEPTED', 'AUTO_ACKNOWLEDGED'}
    summary_line = (
        f"Governed acknowledge-reentry {'accepted' if accepted else 'withheld'} for `{work_item_key}` "
        f"with acknowledgement_state={item.acknowledgement_state}."
    )
    return {
        'schema_version': 'ui_operator_command_receipt/v1',
        'generated_at_utc': _utc_now(),
        'command_id': f'ui-cmd-{uuid4().hex}',
        'action': 'acknowledge-reentry',
        'accepted': accepted,
        'operator_id': operator_id,
        'execution_mode': 'GOVERNED_MUTATION_PREVIEW',
        'requires_projection_refresh': False,
        'target': {
            'work_item_key': work_item_key,
            'review_target': review_target,
            'pack_kind': pack_kind,
            'manifest_path': manifest_path,
        },
        'governance': {
            'surface': 'reentry_acceptance',
            'acknowledgement_state': item.acknowledgement_state,
            'acknowledgement_reason_code': item.acknowledgement_reason_code,
            'ownership_status': item.ownership_status,
            'acceptance_posture': item.acceptance_posture,
            'handoff_required': item.handoff_required,
        },
        'summary_line': summary_line,
        'operator_message': summary_line,
    }


def build_ui_operator_command_receipt_payload(
    *,
    action: str,
    operator_id: str = 'operator',
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, Any]:
    if action == 'claim-item':
        receipt = _claim_item_receipt(
            operator_id=operator_id,
            work_item_key=work_item_key,
            review_target=review_target,
            pack_kind=pack_kind,
            manifest_path=manifest_path,
        )
    elif action == 'renew-lease':
        receipt = _renew_lease_receipt(
            operator_id=operator_id,
            work_item_key=work_item_key,
            review_target=review_target,
            pack_kind=pack_kind,
            manifest_path=manifest_path,
        )
    elif action == 'acknowledge-reentry':
        receipt = _acknowledge_reentry_receipt(
            operator_id=operator_id,
            work_item_key=work_item_key,
            review_target=review_target,
            pack_kind=pack_kind,
            manifest_path=manifest_path,
        )
    else:
        raise ValueError(f'unsupported ui operator action: {action}')
    event_source = append_operator_command_event(receipt=receipt)
    receipt['execution_mode'] = 'GOVERNED_COMMAND_RECORDED'
    receipt['requires_projection_refresh'] = bool(receipt.get('accepted'))
    receipt['event_source'] = event_source
    return receipt


__all__ = ['build_ui_operator_command_receipt_payload']
