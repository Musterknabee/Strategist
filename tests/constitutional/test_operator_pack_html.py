from datetime import datetime, timezone

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleBriefingSection,
    OracleIncidentPackReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
)
from strategy_validator.control_plane import (
    build_briefing_pack_html,
    build_incident_pack_html,
    build_status_pack_html,
)
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_html
from strategy_validator.validator.oracle_diagnostics import (
    _status_pack_workboard_from_trust,
    render_oracle_incident_pack_html,
    render_oracle_status_pack_html,
)


def _status_pack():
    return OracleStatusPackReport(
        generated_at_utc=datetime.now(timezone.utc),
        repo_root='repo',
        search_root='search',
        trust_status='TRUSTED',
        summary_line='healthy',
        sections=[OracleStatusPackSection(section_id='lineage', status='VERIFIED', summary_line='lineage ok', facts=['lineage=true'])],
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
        recommended_next_actions=['triage'],
        status_pack=status_pack,
        artifacts=[],
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
        sections=[OracleBriefingSection(section_id='trust_banner', title='Trust Banner', status='TRUSTED', summary_line='ok', facts=['steady'])],
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


def test_status_pack_html_builder_and_renderer():
    report = _status_pack()
    html = build_status_pack_html(report=report)
    assert '<title>Oracle Status Pack</title>' in html
    assert 'Operator Workboard' in html
    assert render_oracle_status_pack_html(report) == html


def test_incident_pack_html_builder_and_renderer():
    report = _incident_pack(_status_pack())
    html = build_incident_pack_html(report=report)
    assert '<title>Oracle Incident Pack</title>' in html
    assert 'Embedded Status Pack' in html
    assert render_oracle_incident_pack_html(report) == html


def test_briefing_pack_html_builder_and_renderer():
    report = _briefing_pack()
    html = build_briefing_pack_html(report=report)
    assert '<title>Oracle Briefing Pack</title>' in html
    assert 'Trust Banner' in html
    assert render_oracle_briefing_pack_html(report) == html
