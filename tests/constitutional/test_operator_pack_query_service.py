from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleBriefingPackReport
from strategy_validator.projections import build_operator_pack_query, discover_latest_operator_pack_match, run_operator_pack_query
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle


_NOW = '2026-04-14T08:00:00Z'


def _build_briefing_report(tmp_path: Path, *, summary_line: str, trust_status: str) -> OracleBriefingPackReport:
    return OracleBriefingPackReport.model_construct(
        schema_version='oracle_briefing_pack_report/v1',
        generated_at_utc=_NOW,
        repo_root=str(tmp_path),
        search_root=str(tmp_path / 'docs' / 'artifacts'),
        oracle_policy_version='v1',
        oracle_policy_sha256='a' * 64,
        oracle_policy_path='policy.json',
        operator_readiness='READY',
        operator_readiness_summary_line='ready',
        operator_readiness_reasons=[],
        evidence_freshness_status='FRESH',
        stale_artifact_count=0,
        freshness_summary_line='fresh',
        artifact_freshness=[],
        artifact_lineage_summary_line='lineage',
        artifact_lineage=[],
        evidence_integrity_status='VERIFIED',
        unverified_artifact_count=0,
        integrity_summary_line='verified',
        evidence_coverage_status='COMPLETE',
        missing_expected_artifact_count=0,
        evidence_coverage_summary_line='complete',
        missing_expected_artifact_labels=[],
        support_verification_status='VERIFIED',
        support_verification_summary_line='verified',
        support_verification_paths=[],
        support_chain_trust_status='TRUSTED',
        support_chain_trust_summary_line='trusted',
        support_chain_trust_reasons=[],
        support_chain_remediation_status='NONE_REQUIRED',
        support_chain_remediation_summary_line='none',
        support_chain_remediation_actions=[],
        trust_plane_summary_line='trusted',
        operator_reliance_posture='CAUTIOUS_ADVISORY_ONLY',
        operator_reliance_summary_line='rely carefully',
        operator_reliance_reasons=[],
        operator_escalation_lane='STANDARD_REVIEW',
        operator_escalation_summary_line='standard',
        operator_escalation_reasons=[],
        propagation_posture='REVIEW_ONLY_PROPAGATION',
        propagation_summary_line='review',
        propagation_reasons=[],
        automation_posture='AUTOMATION_REVIEW_REQUIRED',
        automation_summary_line='manual review',
        automation_reasons=[],
        control_plane_summary_line='control summary',
        governance_plane_status='GOVERNED',
        governance_plane_summary_line='governed',
        governance_plane_reasons=[],
        governance_plane_codes=[],
        governance_plane_blocking_dimensions=[],
        governance_plane_restricted_dimensions=[],
        governance_plane_actions=[],
        governance_plane_action_items=[],
        governance_plane_primary_dimension=None,
        governance_plane_primary_severity=None,
        governance_plane_primary_action_text=None,
        governance_plane_priority_band='NORMAL',
        governance_plane_priority_score=1,
        governance_plane_priority_summary_line='priority',
        governance_plane_review_target='operator',
        governance_plane_review_sla_hours=24,
        governance_plane_review_summary_line='review',
        governance_plane_review_due_by_utc=None,
        governance_plane_review_sort_key='key',
        governance_plane_review_envelope_vector='vec',
        governance_plane_review_envelope_sha256='b' * 64,
        governance_plane_routing_summary_line='route',
        governance_plane_routing_vector='vec',
        governance_plane_routing_sha256='c' * 64,
        governance_plane_dispatch_summary_line='dispatch',
        governance_plane_dispatch_vector='vec',
        governance_plane_dispatch_sha256='d' * 64,
        governance_plane_dispatch_claim_key='claim',
        governance_plane_dispatch_posture='QUEUED',
        governance_plane_dispatch_permitted=True,
        governance_plane_dispatch_reasons=[],
        governance_plane_dispatch_timeliness='ON_TIME',
        governance_plane_dispatch_claim_permitted_now=True,
        governance_plane_dispatch_timeliness_summary_line='ontime',
        governance_plane_dispatch_claim_urgency='NORMAL',
        governance_plane_dispatch_claim_score=1,
        governance_plane_dispatch_claim_summary_line='claim',
        governance_plane_claim_summary_line='claim',
        governance_plane_claim_queue_key='queue',
        governance_plane_claim_review_target='operator',
        governance_plane_claim_priority_band='NORMAL',
        governance_plane_claim_review_due_by_utc=None,
        governance_plane_claim_review_sort_key='key',
        governance_plane_claim_route_sha256='e' * 64,
        governance_plane_claim_review_envelope_sha256='f' * 64,
        governance_plane_claim_routing_envelope_sha256='1' * 64,
        governance_plane_claim_dispatch_claim_key='claim',
        governance_plane_claim_dispatch_sha256='2' * 64,
        governance_plane_claim_codes=[],
        governance_plane_claim_primary_code=None,
        governance_plane_claim_action_items=[],
        governance_plane_claim_primary_action_text=None,
        governance_plane_claim_worker_lane='worker',
        governance_plane_claim_worker_summary_line='worker',
        governance_plane_claim_worker_sort_key='worker-key',
        governance_plane_claim_lease_key='lease',
        governance_plane_claim_lease_mode='exclusive',
        governance_plane_claim_lease_ttl_seconds=60,
        governance_plane_claim_lease_expires_at_utc=None,
        governance_plane_claim_lease_active_now=True,
        governance_plane_claim_lease_summary_line='lease',
        governance_plane_claim_lease_coverage='COVERED',
        governance_plane_claim_lease_coverage_summary_line='covered',
        governance_plane_claim_lease_health='HEALTHY',
        governance_plane_claim_lease_health_summary_line='healthy',
        governance_plane_claim_lease_renewal_posture='RENEWABLE',
        governance_plane_claim_lease_renewal_permitted_now=True,
        governance_plane_claim_lease_renewal_summary_line='renew',
        governance_plane_claim_lease_action='HOLD',
        governance_plane_claim_lease_action_summary_line='hold',
        governance_plane_claim_disposition='OPEN',
        governance_plane_claim_disposition_summary_line='open',
        governance_plane_claim_process_posture='PROCESSABLE',
        governance_plane_claim_process_permitted_now=True,
        governance_plane_claim_process_summary_line='processable',
        governance_plane_claim_operability='OPERABLE',
        governance_plane_claim_operability_summary_line='operable',
        governance_plane_claim_vector='vec',
        governance_plane_claim_sha256='3' * 64,
        governance_plane_queue_key='queue',
        governance_plane_route_vector='vec',
        governance_plane_route_sha256='4' * 64,
        governance_plane_vector='vec',
        governance_plane_sha256='5' * 64,
        trust_status=trust_status,
        preferred_strategic_backing_source='constitutional_lane',
        exact_feedback_confirmation_count=0,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='AMBIENT_DRIFT',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        summary_line=summary_line,
        status_pack_digest_sha256='6' * 64,
        incident_pack_digest_sha256=None,
        sections=[],
        operator_actions=['review'],
        provenance_digest_sha256='',
    )


@pytest.mark.constitutional
def test_operator_pack_query_service_discovers_filtered_matches(tmp_path: Path) -> None:
    trusted_report = _build_briefing_report(tmp_path, summary_line='Alpha briefing summary', trust_status='TRUSTED')
    restricted_report = _build_briefing_report(tmp_path, summary_line='Beta briefing summary', trust_status='TRUST_RESTRICTED')

    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_alpha', trusted_report, markdown='alpha', html='<p>alpha</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_beta', restricted_report, markdown='beta', html='<p>beta</p>')

    query = build_operator_pack_query(
        search_root=tmp_path,
        repo_root=tmp_path,
        pack_kinds=['briefing_pack'],
        trust_statuses=['TRUSTED'],
        summary_line_contains='Alpha',
        output_artifact_label_contains='html',
    )
    result = run_operator_pack_query(query)

    assert result.report.match_count == 1
    match = result.report.matches[0]
    assert match.pack_kind == 'briefing_pack'
    assert match.trust_status == 'TRUSTED'
    assert match.summary_line == 'Alpha briefing summary'
    assert any(path.name == 'ORACLE_BRIEFING_PACK_REPORT.html' for path in match.output_artifact_paths)

    latest = discover_latest_operator_pack_match(query)
    assert latest is not None
    assert latest.summary_line == 'Alpha briefing summary'


@pytest.mark.constitutional
def test_oracle_operator_pack_query_cli_emits_indexed_matches(tmp_path: Path) -> None:
    report = _build_briefing_report(tmp_path, summary_line='CLI-discovered briefing summary', trust_status='TRUSTED')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'cli_briefing', report, markdown='brief', html='<p>brief</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_QUERY_REPORT.json'
    exit_code = main([
        'oracle-operator-pack-query',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--pack-kind', 'briefing_pack',
        '--summary-line-contains', 'CLI-discovered',
        '--output-artifact-label-contains', 'html',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_query_report/v1'
    assert payload['match_count'] == 1
    assert payload['matches'][0]['pack_kind'] == 'briefing_pack'
    assert payload['matches'][0]['summary_line'] == 'CLI-discovered briefing summary'
    assert any(path.endswith('ORACLE_BRIEFING_PACK_REPORT.html') for path in payload['matches'][0]['output_artifact_paths'])
