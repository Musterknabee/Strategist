from __future__ import annotations

from datetime import UTC, datetime

from strategy_validator.application.ui_command_actions import build_ui_operator_command_receipt_payload
from strategy_validator.application.ui_views import (
    build_ui_workboard_export_payload,
    build_ui_workboard_payload,
)
from strategy_validator.application.ui_workboard_intelligence import build_workboard_intelligence
from strategy_validator.control_plane import (
    assess_governance_plane,
    materialize_governance_work_queue_state,
    materialize_operator_workboard,
)


def _queue_state() -> object:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='incident pack',
    )
    return materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 16, 12, 0, tzinfo=UTC),
    )


def _patch_context(monkeypatch, *, queue_state) -> str:
    review_target = queue_state.governance_claim_envelope.governance_plane_claim_review_target
    workboard = materialize_operator_workboard(governance_work_queue=queue_state, board_label='ops').to_payload()
    workbench = {
        'total_item_count': 0,
        'column_count': 0,
        'columns': [],
    }
    intelligence = build_workboard_intelligence(workboard=workboard, workbench=workbench)
    monkeypatch.setattr(
        'strategy_validator.application.ui_views._build_ui_workboard_context',
        lambda **_: {
            'workboard': workboard,
            'workbench': workbench,
            'intelligence': intelligence,
        },
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_transition_policy_payload',
        lambda **_: {'board_label': 'ops', 'schema_version': 'oracle_operator_transition_policy/v1'},
    )
    return review_target


def test_ui_workboard_payload_exposes_materialization_status(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    queue_state = _queue_state()
    review_target = queue_state.governance_claim_envelope.governance_plane_claim_review_target

    build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='ops',
        work_item_key='wk-1',
        review_target=review_target,
    )
    _patch_context(monkeypatch, queue_state=queue_state)

    payload = build_ui_workboard_payload(board_label='ops')

    assert payload['materialization']['journaled_work_item_count'] == 1
    assert payload['materialization']['journal_operator_count'] == 1
    assert payload['materialization']['journal_action_count'] == 1
    assert payload['materialization']['journal_primary_merge_pending_count'] == 0
    assert payload['materialization']['journal_auxiliary_merge_pending_count'] == 1
    assert payload['materialization']['journal_post_merge_ready_count'] == 1
    assert payload['materialization']['journal_post_merge_ready_count'] == 1
    assert payload['materialization']['journal_post_merge_review_required_count'] == 0
    assert payload['materialization']['journal_post_merge_stale_count'] == 0
    assert payload['materialization']['journal_downstream_closure_ready_count'] == 1
    assert payload['materialization']['journal_downstream_closure_review_required_count'] == 0
    assert payload['materialization']['journal_downstream_closure_blocked_count'] == 0
    assert payload['materialization']['journal_primary_merge_pending_count'] == 0
    assert payload['materialization']['journal_auxiliary_merge_pending_count'] == 1
    assert payload['materialization']['projection_summary_line']
    assert payload['intelligence']['summary']['closure_ready_count'] == 1
    assert payload['intelligence']['summary']['closure_review_required_count'] == 0
    assert payload['intelligence']['summary']['closure_blocked_count'] == 0
    assert payload['intelligence']['board_governance_digest']['journal_downstream_closure_ready_count'] == 1
    assert payload['intelligence']['board_governance_digest']['journal_downstream_closure_review_required_count'] == 0
    assert payload['intelligence']['board_governance_digest']['journal_downstream_closure_blocked_count'] == 0
    assert payload['intelligence']['board_governance_digest']['focus_projection_downstream_closure_state'] == 'AUXILIARY_DOWNSTREAM_CLOSURE_READY'
    assert payload['intelligence']['board_governance_digest']['closure_line']
    assert payload['intelligence']['board_operator_brief']['closure_follow_up_line']
    assert payload['stats']['governed_count'] == 1
    assert payload['stats']['journaled_count'] == 1
    assert payload['stats']['freshness_state'] in {'UNKNOWN', 'STALE', 'CURRENT'}
    queue_entries = payload['queue']['entries']
    assert any(entry['source_kind'] == 'GOVERNED_PRIMARY' for entry in queue_entries)
    assert any(entry['source_kind'] == 'JOURNALED_PENDING' for entry in queue_entries)
    journal_entry = next(entry for entry in queue_entries if entry['source_kind'] == 'JOURNALED_PENDING')
    assert journal_entry['projected_operator_id'] == 'ops'
    assert journal_entry['projected_action_name'] == 'claim-item'
    assert journal_entry['projection_freshness_state'] in {'CURRENT', 'AGING', 'STALE'}
    assert journal_entry['projection_summary_line']
    assert journal_entry['projection_governed_merge_state'] == 'AUXILIARY_GOVERNED_MERGE_PENDING'
    assert journal_entry['projection_governed_summary_line']
    assert journal_entry['projection_post_merge_lifecycle_state'] in {'PRIMARY_POST_MERGE_READY', 'AUXILIARY_POST_MERGE_READY', 'POST_MERGE_REVIEW_REQUIRED', 'POST_MERGE_STALE'}
    assert journal_entry['projection_post_merge_summary_line']
    assert journal_entry['projection_downstream_closure_state'] in {'PRIMARY_DOWNSTREAM_CLOSURE_READY', 'AUXILIARY_DOWNSTREAM_CLOSURE_READY', 'DOWNSTREAM_CLOSURE_REVIEW_REQUIRED', 'DOWNSTREAM_CLOSURE_BLOCKED'}
    assert journal_entry['projection_downstream_closure_summary_line']
    assert 'AUXILIARY_DOWNSTREAM_CLOSURE_READY' in payload['intelligence']['summary']['top_summary_line']


def test_ui_workboard_export_payload_includes_materialization_and_queue_provenance(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    queue_state = _queue_state()
    review_target = queue_state.governance_claim_envelope.governance_plane_claim_review_target

    build_ui_operator_command_receipt_payload(
        action='renew-lease',
        operator_id='ops',
        work_item_key='wk-lease-1',
        review_target=review_target,
    )
    _patch_context(monkeypatch, queue_state=queue_state)

    payload = build_ui_workboard_export_payload(board_label='ops')

    assert payload['materialization']['journaled_work_item_count'] == 1
    assert payload['materialization']['journal_operator_count'] == 1
    assert payload['materialization']['journal_action_count'] == 1
    assert payload['materialization']['journal_primary_merge_pending_count'] == 0
    assert payload['materialization']['journal_auxiliary_merge_pending_count'] == 1
    assert payload['queue_provenance']['governed_work_item_count'] == 1
    assert payload['queue_provenance']['journaled_work_item_count'] == 1
    assert payload['queue_provenance']['review_target'] == review_target
    assert payload['queue_provenance']['materialization_state']
    assert payload['mutation_safety']['authorization_mode'] in {'NON_PRODUCTION_BYPASS', 'TOKEN_PROTECTED', 'MISCONFIGURED'}
    assert payload['operational_truth']['mutation_safety'] == payload['mutation_safety']
    assert payload['operational_truth']['queue_provenance']['review_target'] == review_target
    assert payload['operational_truth']['materialization']['journaled_work_item_count'] == 1
    assert payload['operational_truth']['materialization']['journal_action_count'] == 1
    assert payload['operational_truth']['materialization']['journal_downstream_closure_ready_count'] == 1
    assert payload['operational_truth']['materialization']['journal_downstream_closure_review_required_count'] == 0
    assert payload['operational_truth']['materialization']['journal_downstream_closure_blocked_count'] == 0
    assert payload['operational_truth']['materialization']['projection_summary_line']
    assert payload['summary_line']
    assert payload['export_line']
    assert payload['journal_downstream_closure_ready_count'] == 1
    assert payload['journal_downstream_closure_review_required_count'] == 0
    assert payload['journal_downstream_closure_blocked_count'] == 0
    assert payload['focus_projection_downstream_closure_state'] == 'AUXILIARY_DOWNSTREAM_CLOSURE_READY'
    assert payload['publication_payloads']['board_governance_digest']['payload_object']['closure_line']
    assert payload['publication_payloads']['board_governance_digest']['payload_object']['journal_downstream_closure_ready_count'] == 1
    assert payload['publication_payloads']['board_focus_action_posture']['payload_object']['closure_follow_up_line']


def test_operator_action_projection_materializes_from_verified_chain(monkeypatch, tmp_path) -> None:
    from strategy_validator.ledger.operator_actions import read_operator_action_events, verify_operator_action_event_chain
    from strategy_validator.projections.operator_action_workboard import materialize_operator_action_workboard_projection

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    queue_state = _queue_state()
    claim = queue_state.governance_claim_envelope
    review_target = claim.governance_plane_claim_review_target

    build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='ops',
        work_item_key=claim.governance_plane_claim_sha256,
        review_target=review_target,
        idempotency_key='projection-primary-1',
    )
    build_ui_operator_command_receipt_payload(
        action='renew-lease',
        operator_id='ops',
        work_item_key='wk-aux-1',
        review_target=review_target,
        idempotency_key='projection-aux-1',
    )

    chain = verify_operator_action_event_chain()
    assert chain.ok is True
    assert chain.event_count == 2
    events = read_operator_action_events(review_target=review_target)
    assert [event.sequence_number for event in events] == [1, 2]
    assert events[0].previous_event_hash is None
    assert events[1].previous_event_hash == events[0].event_hash

    projection = materialize_operator_action_workboard_projection(queue_state)
    assert projection.source_event_count == 2
    assert projection.projected_work_item_count == 2
    assert projection.primary_merge_pending_count == 1
    assert projection.auxiliary_merge_pending_count == 1
    assert projection.downstream_closure_ready_count == 2
    assert projection.downstream_closure_review_required_count == 0
    assert projection.downstream_closure_blocked_count == 0
    assert projection.projection_enabled is True
    assert projection.projection_status_state == 'ENABLED'
