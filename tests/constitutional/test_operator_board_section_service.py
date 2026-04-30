from datetime import datetime, timezone

from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_queue_briefing_section,
    build_operator_workboard_report,
    materialize_operator_queue_snapshot,
    materialize_operator_workboard,
    render_operator_workboard_markdown_lines,
)
from strategy_validator.validator.oracle_diagnostics import _status_pack_workboard_from_trust


def test_operator_workboard_report_builder_and_markdown_renderer_share_boundary() -> None:
    issued_at = datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc)
    report = _status_pack_workboard_from_trust(
        trust_status='TRUSTED',
        issued_at_utc=issued_at,
        surface_label='test surface',
    )
    lines = render_operator_workboard_markdown_lines(workboard=report)
    assert lines[0] == '## Operator Workboard'
    assert any('Recommended next actions:' in line for line in lines)
    assert any('Work item `' in line for line in lines)

    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='test surface',
    )
    raw_workboard = materialize_operator_workboard(
        governance_plane=governance_plane,
        issued_at_utc=issued_at,
        board_label='status_pack_workboard',
    )
    rebuilt = build_operator_workboard_report(workboard=raw_workboard)
    assert rebuilt.queue_key == report.queue_key
    assert rebuilt.entries[0].work_item_key == report.entries[0].work_item_key


def test_briefing_operator_queue_section_builder_emits_expected_facts() -> None:
    issued_at = datetime(2026, 4, 14, 12, 0, tzinfo=timezone.utc)
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='briefing surface',
    )
    snapshot = materialize_operator_queue_snapshot(
        issued_at_utc=issued_at,
        governance_plane=governance_plane,
    )
    section = build_operator_queue_briefing_section(
        operator_queue_snapshot=snapshot,
        governance_plane_status='TRUSTED_OPERATOR_PLANE',
        governance_claim_sha256='claimsha',
        governance_dispatch_sha256='dispatchsha',
        status_pack_provenance_digest_sha256='statussha',
    )
    assert section.section_id == 'operator_queue'
    assert any(fact.startswith('queue_key=') for fact in section.facts)
    assert any(fact.startswith('primary_work_item_key=') for fact in section.facts)
    assert section.provenance_refs == ['governance_claim:claimsha', 'governance_dispatch:dispatchsha', 'status_pack:statussha']
