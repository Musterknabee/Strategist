from datetime import datetime, timezone

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleBriefingSection,
    OracleIncidentPackReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
)
from strategy_validator.control_plane import (
    build_briefing_pack_header,
    build_incident_pack_header,
    build_status_pack_header,
    render_operator_pack_header_markdown_lines,
)
from strategy_validator.validator.oracle_diagnostics import _status_pack_workboard_from_trust, render_oracle_incident_pack_markdown, render_oracle_status_pack_markdown
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown


def _status_pack():
    return OracleStatusPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUSTED',
        summary_line='healthy',
        sections=[OracleStatusPackSection(section_id='lineage', status='VERIFIED', summary_line='lineage ok')],
        operator_actions=['watch'],
        exact_feedback_confirmation_count=1,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='EXACT_CONFIRMED_PRESSURE',
        provenance_digest_sha256='abc',
        operator_workboard=_status_pack_workboard_from_trust(
            trust_status='TRUSTED', issued_at_utc=datetime.now(timezone.utc), surface_label='oracle status pack'
        ),
    )


def _incident_pack(status_pack: OracleStatusPackReport):
    return OracleIncidentPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUST_RESTRICTED',
        incident_kind='restricted',
        summary_line='incident',
        status_pack=status_pack,
        artifacts=[],
        recommended_next_actions=['triage'],
        exact_feedback_confirmation_count=0,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='AMBIENT_DRIFT',
        provenance_digest_sha256='y'*64,
        operator_workboard=status_pack.operator_workboard,
    )


def _briefing_pack():
    return OracleBriefingPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUSTED',
        summary_line='briefing ok',
        sections=[OracleBriefingSection(section_id='trust_banner', title='Trust Banner', status='TRUSTED', summary_line='ok')],
        operator_actions=['review'],
        operator_readiness='READY_FOR_REVIEW',
        operator_readiness_summary_line='ready',
        governance_plane_status='GOVERNANCE_READY',
        governance_plane_summary_line='governance ok',
        governance_plane_vector='vec',
        governance_plane_sha256='g'*64,
        governance_plane_priority_band='ELEVATED_PRIORITY',
        governance_plane_priority_score=25,
        governance_plane_priority_summary_line='priority ok',
        governance_plane_routing_summary_line='routing ok',
        governance_plane_routing_vector='route',
        governance_plane_routing_sha256='r'*64,
        governance_plane_queue_key='queue/trusted',
        governance_plane_primary_severity='RESTRICTING',
        control_plane_summary_line='control ok',
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


def test_status_pack_header_builder_and_renderer():
    header = build_status_pack_header(report=_status_pack())
    lines = render_operator_pack_header_markdown_lines(header=header)
    assert lines[0] == '# Oracle Status Pack'
    assert '- Trust status: `TRUSTED`' in lines
    assert 'healthy' in lines
    assert '## Sections' in lines
    markdown = render_oracle_status_pack_markdown(_status_pack())
    assert markdown.startswith('# Oracle Status Pack')


def test_incident_pack_header_builder_and_renderer():
    report = _incident_pack(_status_pack())
    header = build_incident_pack_header(report=report)
    lines = render_operator_pack_header_markdown_lines(header=header)
    assert lines[0] == '# Oracle Incident Pack'
    assert '- Incident kind: `restricted`' in lines
    assert 'incident' in lines
    markdown = render_oracle_incident_pack_markdown(report)
    assert markdown.startswith('# Oracle Incident Pack')


def test_briefing_pack_header_builder_and_renderer():
    report = _briefing_pack()
    header = build_briefing_pack_header(report=report)
    lines = render_operator_pack_header_markdown_lines(header=header)
    assert lines[0] == '# Oracle Briefing Pack'
    assert '- Governance queue key: `queue/trusted`' in lines
    assert 'Governance fingerprint:' in lines
    markdown = render_oracle_briefing_pack_markdown(report)
    assert markdown.startswith('# Oracle Briefing Pack')
    assert 'Trust reasons:' in markdown
