from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import (
    OracleBriefingPackReport,
    OracleIncidentPackArtifact,
    OracleIncidentPackReport,
    OracleStatusPackReport,
    OracleStatusPackSection,
)
from strategy_validator.projections.operator_pack_registry import discover_latest_operator_pack, load_operator_pack_index
from strategy_validator.projections.operator_pack_service import (
    materialize_briefing_pack_bundle,
    materialize_incident_pack_bundle,
    materialize_status_pack_bundle,
)
from strategy_validator.validator.oracle_briefing import materialize_oracle_briefing_pack
from strategy_validator.validator.oracle_diagnostics import (
    materialize_oracle_incident_pack,
    materialize_oracle_status_pack,
    render_oracle_incident_pack_markdown,
)


_NOW = datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)


def _status_report(tmp_path: Path) -> OracleStatusPackReport:
    return OracleStatusPackReport.model_construct(
        schema_version='oracle_status_pack_report/v1',
        generated_at_utc=_NOW,
        repo_root=str(tmp_path),
        search_root=str(tmp_path / 'docs' / 'artifacts'),
        trust_status='TRUST_RESTRICTED',
        preferred_strategic_backing_source='constitutional_lane',
        exact_feedback_confirmation_count=1,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='EXACT_CONFIRMED_PRESSURE',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        active_governed_exception_ids=['exc-1'],
        summary_line='Status pack summary.',
        operator_actions=['review posture'],
        sections=[
            OracleStatusPackSection.model_construct(
                section_id='oracle_posture',
                status='TRUST_RESTRICTED',
                summary_line='Derived posture requires review.',
                preferred_strategic_backing_source='constitutional_lane',
                preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
                exact_feedback_confirmation_count=1,
                exact_feedback_relief_count=0,
                exact_cadence_signal_classification='EXACT_CONFIRMED_PRESSURE',
                facts=['fact=a'],
                operator_actions=['act'],
                explanation=None,
            )
        ],
        provenance_digest_sha256='',
    )


@pytest.mark.constitutional
def test_status_pack_service_matches_validator_materialization(tmp_path: Path) -> None:
    report = _status_report(tmp_path)
    service_root = tmp_path / 'service_status'
    validator_root = tmp_path / 'validator_status'

    service_report = materialize_status_pack_bundle(service_root, report, markdown='status markdown')
    validator_report = materialize_oracle_status_pack(validator_root, report, markdown='status markdown')

    assert service_report.provenance_digest_sha256 == validator_report.provenance_digest_sha256
    assert json.loads((service_root / 'ORACLE_STATUS_PACK_REPORT.json').read_text(encoding='utf-8')) == json.loads(
        (validator_root / 'ORACLE_STATUS_PACK_REPORT.json').read_text(encoding='utf-8')
    )
    manifest = json.loads((service_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['pack_kind'] == 'status_pack'
    assert manifest['output_artifact_count'] == 2
    index = load_operator_pack_index(tmp_path / 'ORACLE_OPERATOR_PACK_INDEX.json')
    assert {entry['pack_kind'] for entry in index['entries']} >= {'status_pack'}


@pytest.mark.constitutional
def test_incident_pack_service_copies_artifacts_and_matches_validator(tmp_path: Path) -> None:
    source_artifact = tmp_path / 'ORACLE_DERIVED_VIEW.json'
    source_artifact.write_text('{"ok": true}', encoding='utf-8')
    status_pack = _status_report(tmp_path)
    report = OracleIncidentPackReport.model_construct(
        schema_version='oracle_incident_pack_report/v1',
        generated_at_utc=_NOW,
        repo_root=str(tmp_path),
        search_root=str(tmp_path / 'docs' / 'artifacts'),
        trust_status='UNTRUSTED',
        incident_kind='blocked',
        blocked=True,
        exact_feedback_confirmation_count=1,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='EXACT_CONFIRMED_PRESSURE',
        summary_line='Incident summary.',
        recommended_next_actions=['triage now'],
        primary_diagnostic=None,
        status_pack=status_pack,
        artifacts=[
            OracleIncidentPackArtifact.model_construct(
                artifact_kind='derived_view',
                source_path=str(source_artifact),
                sha256='x' * 64,
                pack_path=None,
                summary_line='Derived source',
                required=True,
            )
        ],
        provenance_digest_sha256='',
    )

    service_root = tmp_path / 'service_incident'
    validator_root = tmp_path / 'validator_incident'
    service_report = materialize_incident_pack_bundle(
        service_root,
        report,
        markdown=render_oracle_incident_pack_markdown(report),
        render_markdown=render_oracle_incident_pack_markdown,
    )
    validator_report = materialize_oracle_incident_pack(
        validator_root,
        report,
        markdown=render_oracle_incident_pack_markdown(report),
    )

    assert service_report.artifacts[0].pack_path == validator_report.artifacts[0].pack_path
    assert (service_root / service_report.artifacts[0].pack_path).exists()
    assert json.loads((service_root / 'ORACLE_INCIDENT_PACK_REPORT.json').read_text(encoding='utf-8')) == json.loads(
        (validator_root / 'ORACLE_INCIDENT_PACK_REPORT.json').read_text(encoding='utf-8')
    )
    manifest = json.loads((service_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['pack_kind'] == 'incident_pack'
    assert manifest['artifact_copy_count'] == 1


@pytest.mark.constitutional
def test_briefing_pack_service_matches_validator_materialization(tmp_path: Path) -> None:
    report = OracleBriefingPackReport.model_construct(
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
        trust_status='TRUSTED',
        preferred_strategic_backing_source='constitutional_lane',
        exact_feedback_confirmation_count=0,
        exact_feedback_relief_count=0,
        exact_cadence_signal_classification='AMBIENT_DRIFT',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        summary_line='Briefing summary.',
        status_pack_digest_sha256='6' * 64,
        incident_pack_digest_sha256=None,
        sections=[],
        operator_actions=['review'],
        provenance_digest_sha256='',
    )

    service_root = tmp_path / 'service_briefing'
    validator_root = tmp_path / 'validator_briefing'
    service_report = materialize_briefing_pack_bundle(service_root, report, markdown='brief markdown', html='<p>brief</p>')
    validator_report = materialize_oracle_briefing_pack(validator_root, report, markdown='brief markdown', html='<p>brief</p>')

    assert service_report.provenance_digest_sha256 == validator_report.provenance_digest_sha256
    assert json.loads((service_root / 'ORACLE_BRIEFING_PACK_REPORT.json').read_text(encoding='utf-8')) == json.loads(
        (validator_root / 'ORACLE_BRIEFING_PACK_REPORT.json').read_text(encoding='utf-8')
    )
    assert (service_root / 'ORACLE_BRIEFING_PACK_REPORT.html').exists()
    manifest = json.loads((service_root / 'ORACLE_OPERATOR_PACK_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['pack_kind'] == 'briefing_pack'
    latest = discover_latest_operator_pack(tmp_path, pack_kind='briefing_pack')
    assert latest is not None
    assert latest['pack_kind'] == 'briefing_pack'
