from __future__ import annotations

from datetime import UTC, datetime

from strategy_validator.application.ui_views import (
    build_ui_workboard_export_document,
    build_ui_workboard_export_document_headers,
    build_ui_workboard_export_freshness_headers,
    build_ui_workboard_export_allow_headers,
    build_ui_workboard_export_representation_headers,
    build_ui_workboard_export_profile_headers,
    build_ui_workboard_export_location_headers,
    build_ui_workboard_export_disposition_headers,
    build_ui_workboard_export_response_class_headers,
    export_etag_matches,
    export_last_modified_matches,
    build_ui_workboard_export_index_headers,
    build_ui_workboard_export_index,
    build_ui_workboard_export_payload,
    build_ui_workboard_payload,
    serialize_ui_workboard_export_document,
)
from strategy_validator.application.ui_workboard_intelligence import build_workboard_intelligence


NOW = datetime(2026, 4, 16, 12, 0, tzinfo=UTC)


SAMPLE_WORKBOARD = {
    'schema_version': 'oracle_operator_workboard/v1',
    'board_label': 'operator',
    'queue_key': 'governance-main',
    'review_target': 'operator_review',
    'priority_band': 'CRITICAL_PRIORITY',
    'review_due_by_utc': NOW.isoformat(),
    'review_sort_key': '001',
    'work_item_count': 2,
    'summary_line': 'Two items require review.',
    'queue_summary_line': 'Queue mixes degraded and routine items.',
    'recommended_next_actions': ['Claim highest urgency item.'],
    'entries': [
        {
            'work_item_key': 'wk-incident',
            'queue_key': 'governance-main',
            'review_target': 'incident_pack_review',
            'priority_band': 'CRITICAL_PRIORITY',
            'review_due_by_utc': NOW.isoformat(),
            'review_sort_key': '001',
            'action_owner_lane': 'incident_response',
            'claim_operability': 'CLAIM_OPERABLE',
            'dispatch_posture': 'IMMEDIATE_OPERATOR_REVIEW',
            'urgency': 'HIGH',
            'score': 91,
            'summary_line': 'Incident pack trust degraded and needs action.',
            'recommended_actions': ['Claim item under governed handling.'],
        },
        {
            'work_item_key': 'wk-status',
            'queue_key': 'governance-main',
            'review_target': 'status_pack_review',
            'priority_band': 'NORMAL_PRIORITY',
            'review_due_by_utc': NOW.isoformat(),
            'review_sort_key': '002',
            'action_owner_lane': 'governance_ops',
            'claim_operability': 'CLAIM_INOPERABLE',
            'dispatch_posture': 'DISPATCH_BLOCKED',
            'urgency': 'MEDIUM',
            'score': 52,
            'summary_line': 'Status pack cannot be dispatched directly.',
            'recommended_actions': ['Escalate to supervisor.'],
        },
    ],
}

SAMPLE_WORKBENCH = {
    'schema_version': 'oracle_operator_pack_workbench/v1',
    'search_root': '/tmp/repo/docs/artifacts',
    'total_item_count': 3,
    'column_count': 2,
    'columns': [
        {
            'pack_kind': 'incident_pack',
            'item_count': 2,
            'latest_generated_at_utc': '2026-04-16T10:00:00+00:00',
            'trust_statuses': ['TRUSTED', 'UNTRUSTED'],
            'items': [
                {
                    'pack_kind': 'incident_pack',
                    'trust_status': 'UNTRUSTED',
                    'summary_line': 'Incident pack publication is degraded.',
                    'generated_at_utc': '2026-04-16T10:00:00+00:00',
                    'manifest_path': '/tmp/repo/docs/artifacts/incident/manifest.json',
                    'pack_root': '/tmp/repo/docs/artifacts/incident',
                    'primary_output_artifact_path': '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md',
                    'output_artifact_labels': ['markdown'],
                    'output_artifact_paths': ['/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md'],
                },
                {
                    'pack_kind': 'incident_pack',
                    'trust_status': 'TRUSTED',
                    'summary_line': 'Incident pack publication was previously stable.',
                    'generated_at_utc': '2026-04-15T09:00:00+00:00',
                    'manifest_path': '/tmp/repo/docs/artifacts/incident/manifest-prev.json',
                    'pack_root': '/tmp/repo/docs/artifacts/incident-prev',
                    'primary_output_artifact_path': '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK_PREV.md',
                    'output_artifact_labels': ['markdown'],
                    'output_artifact_paths': ['/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK_PREV.md'],
                },
            ],
        },
        {
            'pack_kind': 'status_pack',
            'item_count': 1,
            'latest_generated_at_utc': '2026-04-11T08:00:00+00:00',
            'trust_statuses': ['TRUSTED'],
            'items': [
                {
                    'pack_kind': 'status_pack',
                    'trust_status': 'TRUSTED',
                    'summary_line': 'Status pack publication is stable.',
                    'generated_at_utc': '2026-04-11T08:00:00+00:00',
                    'manifest_path': '/tmp/repo/docs/artifacts/status/manifest.json',
                    'pack_root': '/tmp/repo/docs/artifacts/status',
                    'primary_output_artifact_path': '/tmp/repo/docs/artifacts/status/ORACLE_STATUS_PACK.md',
                    'output_artifact_labels': ['markdown'],
                    'output_artifact_paths': ['/tmp/repo/docs/artifacts/status/ORACLE_STATUS_PACK.md'],
                }
            ],
        },
    ],
}


def test_build_workboard_intelligence_ranks_links_and_surfaces_state_history() -> None:
    intelligence = build_workboard_intelligence(workboard=SAMPLE_WORKBOARD, workbench=SAMPLE_WORKBENCH, now_utc=NOW)

    assert intelligence['schema_version'] == 'ui_workboard_intelligence/v1'
    assert intelligence['summary']['ranked_count'] == 2
    assert intelligence['summary']['blocked_count'] == 1
    assert intelligence['summary']['linked_count'] == 2
    assert intelligence['summary']['stale_link_count'] == 1
    assert intelligence['ranked_items'][0]['work_item_key'] == 'wk-incident'
    assert intelligence['ranked_items'][0]['attention_state'] == 'ESCALATE'
    assert intelligence['ranked_items'][0]['linked_pack']['pack_kind'] == 'incident_pack'
    assert intelligence['ranked_items'][0]['linked_pack']['pack_root'] == '/tmp/repo/docs/artifacts/incident'
    assert intelligence['ranked_items'][0]['linked_pack']['linkage_basis']['matched_terms'] == ['incident']
    assert intelligence['ranked_items'][0]['state_history']['current_state_label'] == 'UNTRUSTED'
    assert intelligence['ranked_items'][0]['state_history']['prior_state_label'] == 'TRUSTED'
    assert 'TRUSTED → UNTRUSTED' in intelligence['ranked_items'][0]['state_history']['transition_summary_line']
    assert intelligence['ranked_items'][0]['state_history']['item_count'] == 2
    assert intelligence['ranked_items'][0]['command_readiness']['caution_count'] >= 1
    assert intelligence['ranked_items'][0]['action_provenance']['summary_line'].startswith('Commands on this item will anchor to incident_pack evidence rooted at')
    assert 'incident_pack' in intelligence['ranked_items'][0]['action_provenance']['linkage_basis_line']
    assert intelligence['ranked_items'][0]['action_provenance']['command_targets'][0]['target_path'].endswith('manifest.json')
    assert intelligence['ranked_items'][0]['action_provenance']['command_targets'][1]['target_path'].endswith('ORACLE_INCIDENT_PACK.md')
    assert intelligence['ranked_items'][0]['command_readiness']['items'][0]['action'] == 'claim-item'
    assert intelligence['ranked_items'][0]['command_readiness']['items'][0]['state'] == 'CAUTION'
    assert 'UNTRUSTED' in str(intelligence['ranked_items'][0]['command_readiness']['items'][0]['reason'])
    assert intelligence['ranked_items'][0]['operator_brief']['safest_next_action'] == 'claim-item'
    assert intelligence['ranked_items'][0]['operator_brief']['safest_next_action_state'] == 'CAUTION'
    assert 'incident_pack_review' in intelligence['ranked_items'][0]['operator_brief']['summary_line']
    assert intelligence['ranked_items'][0]['policy_recommendation']['lawful_next_action'] == 'claim-item'
    assert intelligence['ranked_items'][0]['policy_recommendation']['lawful_next_action_state'] == 'CAUTION'
    assert 'TRUST_SHIFT' in intelligence['ranked_items'][0]['policy_recommendation']['drift_flags']
    assert 'DOWNWARD_TRUST_SHIFT' in intelligence['ranked_items'][0]['policy_recommendation']['drift_flags']
    assert 'RECOMMENDED_ACTION_DRIFT' in intelligence['ranked_items'][0]['policy_recommendation']['drift_flags']
    assert 'TRUST_ALERT' in intelligence['ranked_items'][0]['policy_recommendation']['anomaly_flags']
    assert intelligence['ranked_items'][0]['policy_recommendation']['drift_signals'][0]['kind'] == 'TRUST_SHIFT'
    assert intelligence['ranked_items'][0]['policy_recommendation']['drift_signals'][1]['kind'] == 'DOWNWARD_TRUST_SHIFT'
    assert intelligence['ranked_items'][0]['policy_recommendation']['anomaly_details'][0]['kind'] == 'TRUST_ALERT'
    assert 'renew-lease' in intelligence['ranked_items'][0]['policy_recommendation']['blocked_actions']
    assert 'claim-item' in intelligence['ranked_items'][0]['policy_recommendation']['unsafe_actions']
    assert intelligence['board_operator_brief']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_governance_snapshot']['contradiction_count'] == 0
    assert intelligence['board_governance_snapshot']['drift_count'] == 4
    assert intelligence['board_governance_snapshot']['anomaly_count'] == 1
    assert intelligence['board_governance_snapshot']['high_severity_count'] == 3
    assert intelligence['board_governance_snapshot']['medium_severity_count'] == 2
    assert intelligence['board_governance_snapshot']['top_anomaly_flags'] == ['TRUST_ALERT']
    assert intelligence['board_operator_brief']['focus_action'] == 'claim-item'
    assert 'Fastest safe lane is claim item on wk-incident (CAUTION)' in intelligence['board_operator_brief']['throughput_line']
    assert intelligence['ranked_items'][0]['evidence_backed_briefing']['summary_line'] == 'Evidence-backed briefing: incident_pack_review should stay on claim item (CAUTION) while lineage checks remain in scope.'
    assert intelligence['ranked_items'][0]['evidence_backed_briefing']['action_line'] == 'Action lane: claim item is the current lawful next move at CAUTION state.'
    assert intelligence['ranked_items'][0]['evidence_backed_briefing']['source_paths'] == [
        '/tmp/repo/docs/artifacts/incident/manifest.json',
        '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md',
    ]
    assert intelligence['ranked_items'][0]['evidence_backed_briefing']['watch_items'][0] == 'incident_pack_review moved from TRUSTED to UNTRUSTED across recent indexed issuances.'
    assert intelligence['board_evidence_briefing']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_evidence_briefing']['summary_line'] == 'Board evidence-backed briefing: wk-incident is the current focus because it combines the highest queue pressure with the most actionable lineage-backed next step.'
    assert 'Board pressure combines 0 contradiction(s), 4 drift detail(s), and 1 anomaly detail(s) across 2 ranked item(s).' in intelligence['board_evidence_briefing']['pressure_line']
    assert intelligence['board_governance_clusters']['cluster_count'] == 5
    assert intelligence['board_governance_clusters']['summary_line'] == 'Board governance clusters group 5 pressure class(es) across 2 ranked item(s).'
    assert intelligence['board_governance_clusters']['pressure_line'] == 'Most repeated cluster is TRUST_ALERT (1 item(s), HIGH severity).'
    assert intelligence['board_governance_clusters']['clusters'][0]['signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_governance_clusters']['clusters'][0]['affected_work_item_keys'] == ['wk-incident']
    assert intelligence['board_governance_clusters']['clusters'][0]['source_paths'] == [
        '/tmp/repo/docs/artifacts/incident/manifest.json',
        '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md',
    ]
    assert intelligence['board_governance_digest']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_governance_digest']['focus_action'] == 'claim-item'
    assert intelligence['board_governance_digest']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_governance_digest']['summary_line'] == 'Board governance digest: keep wk-incident on claim item (CAUTION) while TRUST_ALERT remains the top governance pressure.'
    assert intelligence['board_governance_digest']['action_line'] == 'Action posture: wk-incident is the current lawful focus on claim item (CAUTION); 1 blocked lane(s) and 1 stale linkage(s) still need follow-up.'
    assert intelligence['board_governance_digest']['cluster_line'] == 'Cluster pressure: TRUST_ALERT pressure is affecting 1 ranked item(s): incident_pack_review. Keep this item in the focused governance lane because TRUST_ALERT is isolated but still HIGH severity.'
    assert intelligence['board_governance_digest']['watch_items'][0] == 'Contradiction watch: no direct queue-vs-lineage contradiction is currently surfaced.'
    assert intelligence['board_governance_digest']['watch_items'][2] == 'incident_pack_review is anchored to a UNTRUSTED lineage; operator commands should be treated as investigation-grade rather than routine.'
    assert intelligence['board_publication_surface']['schema_version'] == 'oracle_operator_board_publication_surface/v1'
    assert intelligence['board_publication_surface']['export_state'] == 'EXPORT_READY'
    assert intelligence['board_publication_surface']['bundle_root'] == 'generated/publications/operator/governance-main'
    assert intelligence['board_publication_surface']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert intelligence['board_publication_surface']['generated_member_count'] == 4
    assert intelligence['board_publication_surface']['published_member_count'] == 0
    assert intelligence['board_publication_surface']['source_backed_member_count'] == 4
    assert intelligence['board_publication_surface']['artifact_class_summary_line'] == 'Artifact-class posture: 4 generated member(s), 0 published member(s), and 4 source-backed member(s) are currently tracked.'
    assert intelligence['board_publication_surface']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_publication_surface']['focus_action'] == 'claim-item'
    assert intelligence['board_publication_surface']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_publication_surface']['embedded_payload_count'] == 4
    assert intelligence['board_publication_surface']['normalized_members'][0]['relative_publication_path'] == 'generated/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_surface']['normalized_members'][0]['generated_relative_path'] == 'generated/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_surface']['normalized_members'][0]['published_relative_path'] == 'published/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_surface']['normalized_members'][0]['artifact_class'] == 'GENERATED'
    assert intelligence['board_publication_surface']['normalized_members'][0]['publication_stage'] == 'GENERATED_READY'
    assert intelligence['board_publication_surface']['normalized_members'][0]['source_backing_state'] == 'SOURCE_BACKED'
    assert intelligence['board_publication_surface']['normalized_members'][0]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_surface']['normalized_members'][0]['payload_object']['focus_action'] == 'claim-item'
    assert intelligence['board_publication_surface']['normalized_members'][1]['schema_version'] == 'oracle_operator_board_evidence_briefing/v1'
    assert intelligence['board_publication_surface']['normalized_members'][1]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_surface']['normalized_members'][1]['payload_object']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_publication_surface']['normalized_members'][2]['summary_line'] == 'TRUST_ALERT pressure is affecting 1 ranked item(s): incident_pack_review.'
    assert intelligence['board_publication_surface']['normalized_members'][2]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_surface']['normalized_members'][2]['payload_object']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_publication_surface']['normalized_members'][2]['payload_object']['affected_item_count'] == 1
    assert intelligence['board_publication_surface']['normalized_members'][3]['summary_line'] == 'Fastest safe lane is claim item on wk-incident (CAUTION); use the item brief before submitting it.'
    assert intelligence['board_publication_surface']['normalized_members'][3]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_surface']['normalized_members'][3]['payload_object']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_publication_surface']['normalized_members'][3]['payload_object']['focus_action'] == 'claim-item'
    assert intelligence['board_publication_surface']['canonical_source_paths'] == [
        '/tmp/repo/docs/artifacts/incident/manifest.json',
        '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md',
    ]
    assert intelligence['board_publication_bundle_manifest']['schema_version'] == 'oracle_operator_board_publication_bundle_manifest/v1'
    assert intelligence['board_publication_bundle_manifest']['bundle_root'] == 'generated/publications/operator/governance-main'
    assert intelligence['board_publication_bundle_manifest']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert intelligence['board_publication_bundle_manifest']['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert intelligence['board_publication_bundle_manifest']['member_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['embedded_member_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['metadata_only_member_count'] == 0
    assert intelligence['board_publication_bundle_manifest']['embedded_export_keys'] == ['board_governance_digest', 'board_evidence_briefing', 'board_cluster_summary', 'board_focus_action_posture']
    assert intelligence['board_publication_bundle_manifest']['metadata_only_export_keys'] == []
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['export_key'] == 'board_governance_digest'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['generated_relative_path'] == 'generated/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['published_relative_path'] == 'published/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['artifact_class'] == 'GENERATED'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['publication_stage'] == 'GENERATED_READY'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['source_backing_state'] == 'SOURCE_BACKED'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][0]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][3]['relative_publication_path'] == 'generated/publications/operator/governance-main/board_focus_action_posture.json'
    assert intelligence['board_publication_bundle_manifest']['bundle_members'][3]['payload_state'] == 'EMBEDDED'
    assert intelligence['board_publication_bundle_manifest']['canonical_source_paths'] == [
        '/tmp/repo/docs/artifacts/incident/manifest.json',
        '/tmp/repo/docs/artifacts/incident/ORACLE_INCIDENT_PACK.md',
    ]
    assert intelligence['board_publication_bundle_manifest']['generated_member_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['published_member_count'] == 0
    assert intelligence['board_publication_bundle_manifest']['source_backed_member_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['artifact_class_summary_line'] == 'Artifact-class posture: 4 generated member(s), 0 published member(s), and 4 source-backed member(s) are currently tracked.'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['schema_version'] == 'oracle_operator_board_publication_bundle_verification/v1'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['verification_state'] == 'VERIFIABLE'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_member_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['schema_inventory_count'] == 4
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['source_path_count'] == 2
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['fingerprint_input_count'] == 9
    assert len(intelligence['board_publication_bundle_manifest']['verification_envelope']['bundle_fingerprint_sha256']) == 64
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['export_key'] == 'board_governance_digest'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['generated_relative_path'] == 'generated/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['published_relative_path'] == 'published/publications/operator/governance-main/board_governance_digest.json'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['artifact_class'] == 'GENERATED'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['publication_stage'] == 'GENERATED_READY'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['source_backing_state'] == 'SOURCE_BACKED'
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['payload_state'] == 'EMBEDDED'
    assert len(intelligence['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['payload_sha256']) == 64
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['schema_inventory'] == [
        'oracle_operator_board_cluster_summary/v1',
        'oracle_operator_board_evidence_briefing/v1',
        'oracle_operator_board_focus_action_posture/v1',
        'oracle_operator_board_governance_digest/v1',
    ]
    assert intelligence['board_publication_bundle_manifest']['verification_envelope']['fingerprint_inputs'][0] == 'bundle_root=generated/publications/operator/governance-main'
    assert intelligence['board_export_payload']['schema_version'] == 'oracle_operator_board_export_payload/v1'
    assert intelligence['board_export_payload']['export_family'] == 'oracle_operator_board_export_payload'
    assert intelligence['board_export_payload']['export_state'] == 'EXPORT_READY'
    assert intelligence['board_export_payload']['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert intelligence['board_export_payload']['verification_state'] == 'VERIFIABLE'
    assert intelligence['board_export_payload']['bundle_root'] == 'generated/publications/operator/governance-main'
    assert intelligence['board_export_payload']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert intelligence['board_export_payload']['focus_work_item_key'] == 'wk-incident'
    assert intelligence['board_export_payload']['focus_action'] == 'claim-item'
    assert intelligence['board_export_payload']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_export_payload']['embedded_payload_count'] == 4
    assert intelligence['board_export_payload']['member_count'] == 4
    assert intelligence['board_export_payload']['payload_keys'] == ['board_governance_digest', 'board_evidence_briefing', 'board_cluster_summary', 'board_focus_action_posture']
    assert intelligence['board_export_payload']['publication_payloads']['board_governance_digest']['payload_state'] == 'EMBEDDED'
    assert intelligence['board_export_payload']['publication_payloads']['board_governance_digest']['payload_object']['focus_action'] == 'claim-item'
    assert intelligence['board_export_payload']['publication_payloads']['board_cluster_summary']['payload_object']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert intelligence['board_export_payload']['bundle_manifest']['schema_version'] == 'oracle_operator_board_publication_bundle_manifest/v1'
    assert intelligence['board_export_payload']['bundle_manifest']['embedded_export_keys'] == ['board_governance_digest', 'board_evidence_briefing', 'board_cluster_summary', 'board_focus_action_posture']
    assert intelligence['board_export_payload']['verification_envelope']['verification_state'] == 'VERIFIABLE'
    assert intelligence['board_export_payload']['verification_envelope']['content_member_count'] == 4
    assert intelligence['ranked_items'][1]['attention_state'] == 'BLOCKED'
    assert intelligence['ranked_items'][1]['projection_recency']['state'] == 'STALE'
    assert intelligence['ranked_items'][1]['command_readiness']['blocked_count'] >= 2
    assert intelligence['ranked_items'][1]['command_readiness']['items'][0]['state'] == 'BLOCKED'
    assert intelligence['ranked_items'][1]['policy_recommendation']['lawful_next_action'] is None
    assert 'STALE_LINKAGE' in intelligence['ranked_items'][1]['policy_recommendation']['drift_flags']
    assert intelligence['ranked_items'][1]['policy_recommendation']['drift_signals'][0]['kind'] == 'STALE_LINKAGE'
    assert intelligence['ranked_items'][1]['policy_recommendation']['blocked_actions'] == ['claim-item', 'acknowledge-reentry', 'renew-lease']


def test_serialize_ui_workboard_export_document_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )

    export_payload = build_ui_workboard_export_payload(board_label='operator', search_root='/tmp/repo')
    first = serialize_ui_workboard_export_document(export_payload)
    second = serialize_ui_workboard_export_document(export_payload)

    assert first['schema_version'] == 'oracle_operator_board_export_document/v1'
    assert first['document_media_type'] == 'application/json'
    assert first['relative_document_path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert first['published_relative_document_path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert first['document_sha256'] == second['document_sha256']
    assert first['canonical_json'] == second['canonical_json']
    assert first['canonical_payload']['board_label'] == 'operator'
    assert first['canonical_payload']['generated_at_utc'] == export_payload['generated_at_utc']
    assert second['canonical_payload']['generated_at_utc'] == export_payload['generated_at_utc']
    assert 'source_surface' not in first['canonical_payload']
    assert first['canonical_payload']['publication_payloads']['board_governance_digest']['payload_object']['focus_action'] == 'claim-item'
    assert first['canonical_json'].endswith('\n')


def test_build_ui_workboard_export_document_wraps_canonical_export(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )

    document = build_ui_workboard_export_document(board_label='operator', search_root='/tmp/repo')

    assert document['schema_version'] == 'oracle_operator_board_export_document/v1'
    assert document['export_state'] == 'EXPORT_READY'
    assert document['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert document['verification_state'] == 'VERIFIABLE'
    assert document['line_count'] > 0
    assert document['byte_count'] > 0
    assert len(document['document_sha256']) == 64
    assert document['canonical_payload']['payload_keys'] == ['board_governance_digest', 'board_evidence_briefing', 'board_cluster_summary', 'board_focus_action_posture']



def test_build_ui_workboard_export_index_headers_are_cross_linked(monkeypatch) -> None:
    monkeypatch.setattr('strategy_validator.application.ui_views.build_ui_workboard_export_payload', lambda **_: {
        'schema_version': 'oracle_operator_board_export_payload/v1',
        'export_family': 'oracle_operator_board_export_payload',
        'generated_at_utc': NOW.isoformat(),
        'summary_line': 'Export-ready board payload.',
        'export_line': 'Board export remains fully embedded and verifiable.',
        'export_state': 'EXPORT_READY',
        'export_completeness_state': 'FULLY_EMBEDDED',
        'verification_state': 'VERIFIABLE',
        'bundle_root': 'generated/publications/operator/governance-main',
        'published_bundle_root': 'published/publications/operator/governance-main',
        'bundle_fingerprint_sha256': 'abc123',
        'member_count': 4,
        'embedded_payload_count': 4,
        'payload_keys': ['board_governance_digest'],
        'schema_versions': ['oracle_operator_board_governance_digest/v1'],
        'canonical_source_paths': ['/tmp/repo/docs/artifacts/incident/manifest.json'],
        'publication_payloads': {'board_governance_digest': {
            'schema_version': 'oracle_operator_board_governance_digest/v1',
            'title': 'Board governance digest',
            'payload_state': 'EMBEDDED',
            'relative_publication_path': 'generated/publications/operator/governance-main/board_governance_digest.json',
            'generated_relative_path': 'generated/publications/operator/governance-main/board_governance_digest.json',
            'published_relative_path': 'published/publications/operator/governance-main/board_governance_digest.json',
            'artifact_class': 'GENERATED',
            'publication_stage': 'GENERATED_READY',
            'source_backing_state': 'SOURCE_BACKED',
            'source_paths': ['/tmp/repo/docs/artifacts/incident/manifest.json'],
        }},
        'verification_envelope': {'summary_line': 'Verifiable bundle.'},
    })

    index_payload = build_ui_workboard_export_index(board_label='operator', search_root='/tmp/repo')
    headers = build_ui_workboard_export_index_headers(index_payload)

    assert headers['ETag'] == f'"sha256:{index_payload["document_sha256"]}"'
    assert headers['X-Board-Export-Index-Route'] == '/ui/workboard/export/index'
    assert headers['X-Board-Export-Document-Route'] == '/ui/workboard/export/document'
    assert headers['X-Board-Export-Document-SHA256'] == index_payload['document_sha256']
    assert headers['X-Board-Export-Bundle-Fingerprint-SHA256'] == 'abc123'
    assert headers['Cache-Control'] == 'no-cache'
    assert headers['X-Board-Export-Generated-At'] == index_payload['generated_at_utc']
    assert headers['X-Board-Export-Freshness-State'] == 'CURRENT'
    assert headers['X-Board-Export-Freshness-Basis'] == 'generated_at_utc'
    assert headers['Last-Modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert headers['X-Board-Export-Relative-Path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert headers['X-Board-Export-Published-Relative-Path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert headers['Cache-Control'] == 'no-cache'
    assert headers['X-Board-Export-Generated-At'] == NOW.isoformat()
    assert headers['X-Board-Export-Freshness-State'] == 'CURRENT'
    assert headers['X-Board-Export-Freshness-Basis'] == 'generated_at_utc'
    assert headers['Last-Modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert headers['X-Board-Export-State'] == 'EXPORT_READY'
    assert headers['X-Board-Export-Completeness'] == 'FULLY_EMBEDDED'
    assert headers['X-Board-Export-Verification'] == 'VERIFIABLE'
    assert headers['Content-Disposition'] == 'inline; filename="board_export_index.json"'
    assert headers['X-Board-Export-Disposition-State'] == 'INLINE_INSPECTION'
    assert headers['X-Board-Export-Attachment-Disposition'] == 'attachment; filename="board_export_index.json"'
    assert headers['X-Board-Export-Export-Intent'] == 'INSPECT_INLINE_OR_DOWNLOAD'
    assert headers['X-Board-Export-Response-Class'] == 'INDEX_DOCUMENT'
    assert headers['X-Board-Export-Body-Role'] == 'EXPORT_CATALOG'
    assert headers['Link'].startswith('</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"')
    assert 'rel="profile"' in headers['Link']
    assert headers['X-Board-Export-Schema-Version'] == 'oracle_operator_board_export_index/v1'
    assert headers['X-Board-Export-Schema-Family'] == 'oracle_operator_board_export_index'
    assert headers['X-Board-Export-Schema-Revision'] == 'v1'
    assert headers['X-Board-Export-Profile'] == 'urn:strategy-validator:schema:oracle_operator_board_export_index:v1'
    assert headers['X-Board-Export-Profile-State'] == 'DECLARED'
    assert headers['Digest'].startswith('sha-256=')

def test_export_etag_matches_exact_and_wildcard() -> None:
    assert export_etag_matches('\"sha256:abc\"', '\"sha256:abc\"') is True
    assert export_etag_matches('W/\"sha256:abc\", \"sha256:def\"', '\"sha256:def\"') is True
    assert export_etag_matches('*', '\"sha256:def\"') is True
    assert export_etag_matches('\"sha256:abc\"', '\"sha256:def\"') is False
    assert export_etag_matches(None, '\"sha256:def\"') is False


def test_build_ui_workboard_export_location_headers_include_canonical_paths() -> None:
    headers = build_ui_workboard_export_location_headers({
        'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
        'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
    })

    assert headers['Content-Location'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert headers['X-Board-Export-Canonical-Relative-Path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert headers['X-Board-Export-Published-Canonical-Relative-Path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert headers['X-Board-Export-Location-State'] == 'DECLARED'
    assert headers['X-Board-Export-Published-Location-State'] == 'DECLARED'


def test_build_ui_workboard_export_disposition_headers_distinguish_inline_and_download() -> None:
    document_headers = build_ui_workboard_export_disposition_headers({
        'schema_version': 'oracle_operator_board_export_document/v1',
        'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
    })
    assert document_headers['Content-Disposition'] == 'inline; filename="board_export_payload.json"'
    assert document_headers['X-Board-Export-Disposition-State'] == 'INLINE_INSPECTION'
    assert document_headers['X-Board-Export-Attachment-Disposition'] == 'attachment; filename="board_export_payload.json"'
    assert document_headers['X-Board-Export-Export-Intent'] == 'INSPECT_INLINE_OR_DOWNLOAD'
    assert document_headers['X-Board-Export-Filename'] == 'board_export_payload.json'

    index_headers = build_ui_workboard_export_disposition_headers({
        'schema_version': 'oracle_operator_board_export_index/v1',
        'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
    })
    assert index_headers['Content-Disposition'] == 'inline; filename="board_export_index.json"'
    assert index_headers['X-Board-Export-Attachment-Disposition'] == 'attachment; filename="board_export_index.json"'
    assert index_headers['X-Board-Export-Filename'] == 'board_export_index.json'


def test_build_ui_workboard_export_freshness_headers_include_last_modified() -> None:
    headers = build_ui_workboard_export_freshness_headers({'generated_at_utc': NOW.isoformat()})

    assert headers['Cache-Control'] == 'no-cache'
    assert headers['X-Board-Export-Generated-At'] == NOW.isoformat()
    assert headers['X-Board-Export-Freshness-State'] == 'CURRENT'
    assert headers['X-Board-Export-Freshness-Basis'] == 'generated_at_utc'
    assert headers['Last-Modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'


def test_build_ui_workboard_export_response_class_headers_distinguish_catalog_and_payload() -> None:
    document_headers = build_ui_workboard_export_response_class_headers({
        'schema_version': 'oracle_operator_board_export_document/v1',
    })
    assert document_headers['X-Board-Export-Response-Class'] == 'CANONICAL_EXPORT_DOCUMENT'
    assert document_headers['X-Board-Export-Body-Role'] == 'EXPORT_PAYLOAD'
    assert document_headers['X-Board-Export-Response-Class-State'] == 'DECLARED'

    index_headers = build_ui_workboard_export_response_class_headers({
        'schema_version': 'oracle_operator_board_export_index/v1',
    })
    assert index_headers['X-Board-Export-Response-Class'] == 'INDEX_DOCUMENT'
    assert index_headers['X-Board-Export-Body-Role'] == 'EXPORT_CATALOG'
    assert index_headers['X-Board-Export-Response-Class-State'] == 'DECLARED'


def test_build_ui_workboard_export_document_headers_are_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )

    document = build_ui_workboard_export_document(board_label='operator', search_root='/tmp/repo')
    headers = build_ui_workboard_export_document_headers(document)

    assert headers['ETag'] == f'"sha256:{document["document_sha256"]}"'
    assert headers['X-Board-Export-Document-SHA256'] == document['document_sha256']
    assert headers['X-Board-Export-Bundle-Fingerprint-SHA256'] == document['canonical_payload']['bundle_fingerprint_sha256']
    assert headers['X-Board-Export-Relative-Path'] == document['relative_document_path']
    assert headers['X-Board-Export-Published-Relative-Path'] == document['published_relative_document_path']
    assert headers['Content-Location'] == document['relative_document_path']
    assert headers['X-Board-Export-Canonical-Relative-Path'] == document['relative_document_path']
    assert headers['X-Board-Export-Published-Canonical-Relative-Path'] == document['published_relative_document_path']
    assert 'rel="canonical"' in headers['Link']
    assert headers['X-Board-Export-State'] == 'EXPORT_READY'
    assert headers['X-Board-Export-Completeness'] == 'FULLY_EMBEDDED'
    assert headers['X-Board-Export-Verification'] == 'VERIFIABLE'
    assert headers['Content-Disposition'] == 'inline; filename="board_export_payload.json"'
    assert headers['X-Board-Export-Disposition-State'] == 'INLINE_INSPECTION'
    assert headers['X-Board-Export-Attachment-Disposition'] == 'attachment; filename="board_export_payload.json"'
    assert headers['X-Board-Export-Export-Intent'] == 'INSPECT_INLINE_OR_DOWNLOAD'
    assert headers['X-Board-Export-Byte-Count'] == str(document['byte_count'])
    assert headers['X-Board-Export-Line-Count'] == str(document['line_count'])
    assert headers['Digest'].startswith('sha-256=')


def test_build_ui_workboard_export_index_catalogs_export_document_and_members(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )

    index_payload = build_ui_workboard_export_index(board_label='operator', search_root='/tmp/repo')

    assert index_payload['schema_version'] == 'oracle_operator_board_export_index/v1'
    assert index_payload['index_family'] == 'oracle_operator_board_export_index'
    assert index_payload['source_surface'] == 'ui/workboard/export/index'
    assert index_payload['export_state'] == 'EXPORT_READY'
    assert index_payload['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert index_payload['verification_state'] == 'VERIFIABLE'
    assert index_payload['relative_document_path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert index_payload['published_relative_document_path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert index_payload['document_media_type'] == 'application/json'
    assert len(index_payload['document_sha256']) == 64
    assert index_payload['member_count'] == 4
    assert index_payload['embedded_payload_count'] == 4
    assert 'operational_truth' in index_payload
    assert index_payload['operational_truth']['queue_provenance']['materialization_state'] == index_payload['queue_provenance']['materialization_state']
    assert index_payload['normalized_members'][0]['export_key'] == 'board_governance_digest'
    assert index_payload['normalized_members'][0]['payload_state'] == 'EMBEDDED'
    assert index_payload['normalized_members'][0]['artifact_class'] == 'GENERATED'
    assert index_payload['normalized_members'][0]['source_backing_state'] == 'SOURCE_BACKED'
    assert index_payload['normalized_members'][0]['payload_sha256']
    headers = build_ui_workboard_export_index_headers(index_payload)
    assert headers['X-Board-Export-Response-Class'] == 'INDEX_DOCUMENT'
    assert headers['X-Board-Export-Body-Role'] == 'EXPORT_CATALOG'


def test_build_ui_workboard_export_payload_returns_standalone_export_object(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )

    payload = build_ui_workboard_export_payload(board_label='operator', search_root='/tmp/repo')

    assert payload['schema_version'] == 'oracle_operator_board_export_payload/v1'
    assert 'mutation_safety' in payload
    assert 'operational_truth' in payload
    assert payload['export_state'] == 'EXPORT_READY'
    assert payload['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert payload['verification_state'] == 'VERIFIABLE'
    assert payload['board_label'] == 'operator'
    assert payload['source_surface'] == 'ui/workboard/export'
    assert payload['queue_work_item_count'] == 2
    assert payload['pack_item_count'] == 3
    assert payload['pack_column_count'] == 2
    assert payload['payload_keys'] == ['board_governance_digest', 'board_evidence_briefing', 'board_cluster_summary', 'board_focus_action_posture']
    assert payload['publication_payloads']['board_governance_digest']['payload_object']['focus_action'] == 'claim-item'
    assert payload['bundle_manifest']['summary_line'].startswith('Board publication bundle manifest: 4 normalized publication member(s)')
    assert payload['verification_envelope']['verification_state'] == 'VERIFIABLE'
    assert payload['generated_at_utc']


def test_build_ui_workboard_payload_embeds_intelligence_counts_and_history(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_workboard_payload',
        lambda **_: SAMPLE_WORKBOARD,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_operator_pack_workbench_payload',
        lambda **_: SAMPLE_WORKBENCH,
    )
    monkeypatch.setattr(
        'strategy_validator.application.ui_views.build_transition_policy_payload',
        lambda **_: {'schema_version': 'oracle_operator_transition_policy/v1', 'items': []},
    )

    payload = build_ui_workboard_payload(board_label='operator', search_root='/tmp/repo')

    assert payload['schema_version'] == 'ui_workboard_dashboard/v1'
    assert payload['intelligence']['summary']['ranked_count'] == 2
    assert payload['stats']['blocked_count'] == 1
    assert payload['stats']['linked_count'] == 2
    assert payload['stats']['stale_link_count'] == 1
    assert payload['intelligence']['ranked_items'][0]['linked_pack']['primary_output_artifact_path'].endswith('ORACLE_INCIDENT_PACK.md')
    assert payload['intelligence']['ranked_items'][0]['state_history']['entries'][0]['is_latest'] is True
    assert payload['intelligence']['ranked_items'][0]['state_history']['entries'][1]['trust_status'] == 'TRUSTED'
    assert payload['intelligence']['ranked_items'][0]['action_provenance']['evidence_anchor_count'] == 2
    assert payload['intelligence']['ranked_items'][0]['action_provenance']['command_targets'][0]['anchor_kind'] == 'PACK_MANIFEST'
    assert payload['intelligence']['ranked_items'][0]['command_readiness']['items'][0]['action'] == 'claim-item'
    assert payload['intelligence']['ranked_items'][0]['policy_recommendation']['lawful_next_action'] == 'claim-item'
    assert payload['intelligence']['board_governance_snapshot']['drift_count'] == 4
    assert payload['intelligence']['board_governance_snapshot']['anomaly_count'] == 1
    assert payload['intelligence']['board_governance_snapshot']['high_severity_count'] == 3
    assert payload['intelligence']['board_governance_snapshot']['medium_severity_count'] == 2
    assert payload['intelligence']['ranked_items'][0]['command_readiness']['items'][0]['state'] == 'CAUTION'
    assert payload['intelligence']['ranked_items'][0]['operator_brief']['safest_next_action'] == 'claim-item'
    assert payload['intelligence']['ranked_items'][0]['evidence_backed_briefing']['summary_line'].startswith('Evidence-backed briefing: incident_pack_review should stay on claim item')
    assert payload['intelligence']['board_operator_brief']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_operator_brief']['focus_action'] == 'claim-item'
    assert payload['intelligence']['board_governance_clusters']['cluster_count'] == 5
    assert payload['intelligence']['board_governance_clusters']['clusters'][0]['signal_kind'] == 'TRUST_ALERT'
    assert payload['intelligence']['board_evidence_briefing']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_governance_digest']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_governance_digest']['focus_action'] == 'claim-item'
    assert payload['intelligence']['board_governance_digest']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert payload['intelligence']['board_publication_surface']['export_state'] == 'EXPORT_READY'
    assert payload['intelligence']['board_publication_surface']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert payload['intelligence']['board_publication_surface']['embedded_payload_count'] == 4
    assert payload['intelligence']['board_publication_surface']['generated_member_count'] == 4
    assert payload['intelligence']['board_publication_surface']['published_member_count'] == 0
    assert payload['intelligence']['board_publication_surface']['source_backed_member_count'] == 4
    assert payload['intelligence']['board_publication_surface']['normalized_members'][0]['export_key'] == 'board_governance_digest'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][0]['artifact_class'] == 'GENERATED'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][0]['publication_stage'] == 'GENERATED_READY'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][0]['source_backing_state'] == 'SOURCE_BACKED'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][0]['payload_object']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][1]['payload_object']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][2]['payload_object']['top_cluster_signal_kind'] == 'TRUST_ALERT'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][3]['export_key'] == 'board_focus_action_posture'
    assert payload['intelligence']['board_publication_surface']['normalized_members'][3]['payload_object']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_publication_bundle_manifest']['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert payload['intelligence']['board_publication_bundle_manifest']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert payload['intelligence']['board_publication_bundle_manifest']['bundle_members'][1]['export_key'] == 'board_evidence_briefing'
    assert payload['intelligence']['board_publication_bundle_manifest']['bundle_members'][1]['payload_state'] == 'EMBEDDED'
    assert payload['intelligence']['board_publication_bundle_manifest']['bundle_members'][2]['payload_state'] == 'EMBEDDED'
    assert payload['intelligence']['board_publication_bundle_manifest']['bundle_members'][3]['payload_state'] == 'EMBEDDED'
    assert payload['intelligence']['board_publication_bundle_manifest']['verification_envelope']['verification_state'] == 'VERIFIABLE'
    assert payload['intelligence']['board_publication_bundle_manifest']['verification_envelope']['content_member_count'] == 4
    assert payload['intelligence']['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][0]['artifact_class'] == 'GENERATED'
    assert payload['intelligence']['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][2]['export_key'] == 'board_cluster_summary'
    assert payload['intelligence']['board_publication_bundle_manifest']['verification_envelope']['content_inventory'][3]['payload_state'] == 'EMBEDDED'
    assert payload['intelligence']['board_export_payload']['export_state'] == 'EXPORT_READY'
    assert payload['intelligence']['board_export_payload']['export_completeness_state'] == 'FULLY_EMBEDDED'
    assert payload['intelligence']['board_export_payload']['verification_state'] == 'VERIFIABLE'
    assert payload['intelligence']['board_export_payload']['bundle_root'] == 'generated/publications/operator/governance-main'
    assert payload['intelligence']['board_export_payload']['published_bundle_root'] == 'published/publications/operator/governance-main'
    assert payload['intelligence']['board_export_payload']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_export_payload']['focus_action'] == 'claim-item'
    assert payload['intelligence']['board_export_payload']['payload_keys'][0] == 'board_governance_digest'
    assert payload['intelligence']['board_export_payload']['publication_payloads']['board_evidence_briefing']['payload_object']['focus_work_item_key'] == 'wk-incident'
    assert payload['intelligence']['board_export_payload']['publication_payloads']['board_focus_action_posture']['payload_object']['focus_action'] == 'claim-item'
    assert payload['intelligence']['board_export_payload']['bundle_manifest']['summary_line'].startswith('Board publication bundle manifest: 4 normalized publication member(s)')
    assert payload['intelligence']['board_export_payload']['verification_envelope']['bundle_fingerprint_sha256']


def test_export_last_modified_matches_current_and_stale() -> None:
    assert export_last_modified_matches('Thu, 16 Apr 2026 12:00:00 GMT', 'Thu, 16 Apr 2026 12:00:00 GMT') is True
    assert export_last_modified_matches('Thu, 16 Apr 2026 12:30:00 GMT', 'Thu, 16 Apr 2026 12:00:00 GMT') is True
    assert export_last_modified_matches('Thu, 16 Apr 2026 11:59:59 GMT', 'Thu, 16 Apr 2026 12:00:00 GMT') is False
    assert export_last_modified_matches('invalid', 'Thu, 16 Apr 2026 12:00:00 GMT') is False
    assert export_last_modified_matches(None, 'Thu, 16 Apr 2026 12:00:00 GMT') is False
