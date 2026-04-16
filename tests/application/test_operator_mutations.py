from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from strategy_validator.application.operator_mutations import build_ui_operator_command_receipt_payload


def test_claim_item_receipt_uses_governed_claim_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.append_operator_command_event',
        lambda **_: {'event_id': 'evt-1', 'log_path': 'operator-log.jsonl', 'schema_version': 'operator_command_event/v1'},
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_workboard_payload',
        lambda **_: {
            'entries': [
                {
                    'work_item_key': 'w1',
                    'queue_key': 'queue:governance',
                    'review_target': 'operator_review',
                    'priority_band': 'HIGH',
                    'action_owner_lane': 'research_ops',
                }
            ]
        },
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_pack_claim_lease_payload',
        lambda **_: {
            'items': [
                {
                    'pack_kind': 'briefing_pack',
                    'claim_state': 'CLAIM_PENDING',
                    'lease_state': 'LEASE_PENDING_ACQUISITION',
                    'lease_action': 'ACQUIRE_LEASE',
                    'lease_key': 'lease-1',
                    'latest_manifest_path': 'packs/briefing.json',
                    'recommended_actions': ['acquire governed lease'],
                }
            ]
        },
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_pack_claim_lifecycle_payload',
        lambda **_: {
            'items': [
                {
                    'pack_kind': 'briefing_pack',
                    'lifecycle_state': 'PENDING_ACQUISITION',
                    'renewal_action': 'ACQUIRE_AND_RENEW',
                    'expiry_action': 'HOLD_PENDING_CLAIM',
                    'recommended_actions': ['acquire before renew'],
                }
            ]
        },
    )

    payload = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='w1',
        pack_kind='briefing_pack',
        manifest_path='packs/briefing.json',
    )

    assert payload['accepted'] is True
    assert payload['execution_mode'] == 'GOVERNED_COMMAND_RECORDED'
    assert payload['event_source']['event_id'] == 'evt-1'
    assert payload['governance']['surface'] == 'claim_lease'
    assert payload['governance']['lease_action'] == 'ACQUIRE_LEASE'


def test_renew_lease_receipt_withholds_when_lifecycle_says_no_renewal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.append_operator_command_event',
        lambda **_: {'event_id': 'evt-2', 'log_path': 'operator-log.jsonl', 'schema_version': 'operator_command_event/v1'},
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_workboard_payload',
        lambda **_: {
            'entries': [
                {
                    'work_item_key': 'w1',
                    'queue_key': 'queue:governance',
                    'review_target': 'operator_review',
                    'priority_band': 'HIGH',
                    'action_owner_lane': 'research_ops',
                }
            ]
        },
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_pack_claim_lease_payload',
        lambda **_: {
            'items': [
                {
                    'pack_kind': 'briefing_pack',
                    'claim_state': 'CLAIM_ACTIVE',
                    'lease_state': 'LEASE_ACTIVE',
                    'lease_action': 'MAINTAIN_LEASE',
                    'lease_key': 'lease-1',
                    'latest_manifest_path': 'packs/briefing.json',
                    'recommended_actions': ['maintain lease'],
                }
            ]
        },
    )
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.build_pack_claim_lifecycle_payload',
        lambda **_: {
            'items': [
                {
                    'pack_kind': 'briefing_pack',
                    'lifecycle_state': 'UNCLAIMED_EXPIRABLE',
                    'renewal_action': 'NO_RENEWAL_ACTION',
                    'expiry_action': 'ALLOW_EXPIRY',
                    'recommended_actions': ['allow expiry'],
                }
            ]
        },
    )

    payload = build_ui_operator_command_receipt_payload(
        action='renew-lease',
        operator_id='jp',
        work_item_key='w1',
        pack_kind='briefing_pack',
        manifest_path='packs/briefing.json',
    )

    assert payload['accepted'] is False
    assert payload['governance']['surface'] == 'claim_lifecycle'
    assert payload['governance']['renewal_action'] == 'NO_RENEWAL_ACTION'


def test_acknowledge_reentry_receipt_uses_reentry_acceptance_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.append_operator_command_event',
        lambda **_: {'event_id': 'evt-3', 'log_path': 'operator-log.jsonl', 'schema_version': 'operator_command_event/v1'},
    )
    monkeypatch.setattr('strategy_validator.application.operator_mutations.build_queue_snapshot', lambda **_: object())
    monkeypatch.setattr('strategy_validator.application.operator_mutations.query_operator_queue', lambda **_: object())
    monkeypatch.setattr('strategy_validator.application.operator_mutations.build_operator_reentry_acceptance_request', lambda **kwargs: kwargs)
    monkeypatch.setattr(
        'strategy_validator.application.operator_mutations.materialize_operator_reentry_acceptance',
        lambda *_, **__: SimpleNamespace(
            items=(
                SimpleNamespace(
                    work_item_key='reentry-1',
                    acknowledgement_state='ACKNOWLEDGED_ACCEPTED',
                    acknowledgement_reason_code='CLAIM_SPECIALIST_REQUIRED',
                    ownership_status='ASSIGNED_PENDING_ACCEPTANCE',
                    acceptance_posture='ACCEPTANCE_REQUIRED',
                    handoff_required=True,
                ),
            )
        ),
    )

    payload = build_ui_operator_command_receipt_payload(
        action='acknowledge-reentry',
        operator_id='jp',
        work_item_key='reentry-1',
    )

    assert payload['accepted'] is True
    assert payload['governance']['surface'] == 'reentry_acceptance'
    assert payload['governance']['acknowledgement_state'] == 'ACKNOWLEDGED_ACCEPTED'


def test_append_operator_command_event_persists_append_only_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.application.operator_event_log import append_operator_command_event

    log_path = tmp_path / 'operator' / 'ORACLE_OPERATOR_COMMAND_EVENT_LOG.jsonl'
    monkeypatch.setenv('STRATEGY_VALIDATOR_OPERATOR_EVENT_LOG_PATH', str(log_path))

    receipt = {
        'command_id': 'cmd-1',
        'generated_at_utc': '2026-04-16T00:00:00+00:00',
        'action': 'claim-item',
        'accepted': True,
        'operator_id': 'jp',
        'target': {'work_item_key': 'w1'},
        'governance': {'surface': 'claim_lease'},
        'summary_line': 'test summary',
    }

    event_source = append_operator_command_event(receipt=receipt)

    assert event_source['log_path'] == str(log_path.resolve())
    lines = log_path.read_text(encoding='utf-8').splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event['command_id'] == 'cmd-1'
    assert event['action'] == 'claim-item'
    assert event['governance']['surface'] == 'claim_lease'
