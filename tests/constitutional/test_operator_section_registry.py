from datetime import datetime, timezone

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleBriefingSection,
    OracleIncidentPackReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
)
from strategy_validator.control_plane import (
    OracleOperatorQueueQueryRequest,
    build_operator_queue_query_request,
    compose_briefing_pack_sections,
    compose_incident_pack_sections,
    compose_status_pack_sections,
    run_operator_queue_query,
)
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import (
    _status_pack_workboard_from_trust,
    render_oracle_incident_pack_markdown,
    render_oracle_status_pack_markdown,
)


def _status_pack():
    return OracleStatusPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUSTED',
        summary_line='healthy',
        sections=[
            OracleStatusPackSection(
                section_id='lineage',
                status='VERIFIED',
                summary_line='lineage ok',
                facts=['lineage=true'],
                operator_actions=['retain'],
            )
        ],
        operator_actions=['watch'],
        operator_workboard=_status_pack_workboard_from_trust(
            trust_status='TRUSTED',
            issued_at_utc=datetime.now(timezone.utc),
            surface_label='oracle status pack',
        ),
        exact_feedback_confirmation_count=1,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='EXACT_CONFIRMED_PRESSURE',
        provenance_digest_sha256='abc',
    )


def _briefing_pack():
    return OracleBriefingPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        oracle_policy_version='v1',
        oracle_policy_sha256='p'*64,
        trust_status='TRUSTED',
        summary_line='briefing ok',
        operator_actions=['review'],
        sections=[
            OracleBriefingSection(
                section_id='operator_queue',
                title='Operator Queue',
                status='ACTIVE',
                summary_line='queue active',
                facts=['queue_key=governance/trusted'],
                operator_actions=['open queue'],
                provenance_refs=['status_pack:abc'],
            )
        ],
        operator_readiness='READY_FOR_REVIEW',
        operator_readiness_summary_line='ready',
        governance_plane_status='GOVERNANCE_READY',
        governance_plane_summary_line='ok',
        governance_plane_vector='vec',
        governance_plane_sha256='g'*64,
        operator_reliance_posture='CAUTIOUS_ADVISORY_ONLY',
        operator_reliance_summary_line='careful',
        operator_escalation_lane='STANDARD_OPERATOR_FLOW',
        operator_escalation_summary_line='standard',
        propagation_posture='REVIEW_ONLY_PROPAGATION',
        propagation_summary_line='review',
        automation_posture='AUTOMATION_REVIEW_REQUIRED',
        automation_summary_line='review',
        evidence_freshness_status='FRESH',
        freshness_summary_line='fresh',
        evidence_integrity_status='VERIFIED',
        integrity_summary_line='verified',
        evidence_coverage_status='COMPLETE',
        evidence_coverage_summary_line='covered',
        support_verification_status='VERIFIED',
        support_verification_summary_line='verified',
        support_chain_trust_status='TRUSTED',
        support_chain_trust_summary_line='trusted',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_summary_line='none',
        trust_plane_summary_line='ok',
        exact_feedback_confirmation_count=0,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='AMBIENT_DRIFT',
        status_pack_digest_sha256='s'*64,
        provenance_digest_sha256='z'*64,
    )


def _incident_pack(status_pack):
    return OracleIncidentPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUST_RESTRICTED',
        incident_kind='restricted',
        blocked=False,
        summary_line='incident',
        recommended_next_actions=['triage'],
        status_pack=status_pack,
        artifacts=[],
        operator_workboard=status_pack.operator_workboard,
        exact_feedback_confirmation_count=0,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='AMBIENT_DRIFT',
        provenance_digest_sha256='y'*64,
    )


def test_status_pack_section_composition_includes_workboard_and_next_actions():
    composition = compose_status_pack_sections(report=_status_pack())
    keys = [entry.section_key for entry in composition.entries]
    assert keys == ['status:lineage', 'status:operator_workboard', 'status:next_actions']


def test_briefing_pack_renderer_uses_composed_sections():
    markdown = render_oracle_briefing_pack_markdown(_briefing_pack())
    assert '## Operator Queue' in markdown
    assert '## Next Actions' in markdown


def test_incident_pack_section_composition_includes_embedded_status_pack():
    report = _incident_pack(_status_pack())
    composition = compose_incident_pack_sections(report=report)
    keys = [entry.section_key for entry in composition.entries]
    assert keys[-1] == 'incident:embedded_status_pack'
    markdown = render_oracle_incident_pack_markdown(report)
    assert '## Embedded Status Pack' in markdown

