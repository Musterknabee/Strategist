from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.operator_queue import (
    build_governance_queue_state,
    build_workboard_action_contract_payload,
)


def test_operator_queue_surface_exposes_canonical_governance_builders() -> None:
    queue_state = build_governance_queue_state(
        issued_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_NONE',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='operator-queue-surface',
    )
    assert queue_state.governance_plane.governance_plane_status == 'GOVERNANCE_READY'

    payload = build_workboard_action_contract_payload(
        board_label='default',
        issued_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_NONE',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='operator-queue-surface',
    )
    assert payload['schema_version'] == 'oracle_operator_workboard_action_contract/v1'
