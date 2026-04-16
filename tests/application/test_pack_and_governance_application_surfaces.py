from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.governance_surface import (
    build_governance_queue_state,
    build_workboard_action_contract_payload,
)
from strategy_validator.application.operator_pack_queries import build_operator_pack_query_payload


def test_governance_surface_builds_queue_state_and_action_contract() -> None:
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
        surface_label='governance-surface',
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
        surface_label='governance-surface',
    )
    assert payload['schema_version'] == 'oracle_operator_workboard_action_contract/v1'


def test_operator_pack_query_payload_surface_runs_against_empty_root(tmp_path: Path) -> None:
    payload = build_operator_pack_query_payload(search_root=tmp_path)
    assert payload['schema_version'] == 'oracle_operator_pack_query_report/v1'
    assert payload['matches'] == []
