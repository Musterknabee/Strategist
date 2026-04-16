from __future__ import annotations

from pathlib import Path

from strategy_validator.application.ui_views import build_ui_evidence_payload, build_ui_tribunal_payload


def test_build_ui_tribunal_payload_includes_doctrine_stats_and_provenance() -> None:
    payload = build_ui_tribunal_payload()

    assert payload['schema_version'] == 'ui_tribunal_workspace/v1'
    assert payload['doctrine_stats']['active_doctrine_count'] >= 1
    assert 'section_provenance' in payload
    assert payload['section_provenance']['thesis_graph']['projection_family'] == 'tribunal'
    assert payload['blindness']['quantitative_payloads_present'] is False


def test_build_ui_evidence_payload_includes_section_provenance() -> None:
    payload = build_ui_evidence_payload()

    assert payload['schema_version'] == 'ui_evidence_dashboard/v1'
    assert 'section_provenance' in payload
    assert payload['section_provenance']['registry']['verification_label']
    assert payload['section_provenance']['lineage']['projection_family'] == 'evidence'


def test_build_ui_evidence_payload_converges_operator_event_log_into_registry(tmp_path: Path) -> None:
    runtime_review_path = tmp_path / 'docs' / 'artifacts' / 'runtime' / 'RUNTIME_REVIEW.json'
    operator_log_path = tmp_path / 'docs' / 'artifacts' / 'operator' / 'ORACLE_OPERATOR_COMMAND_EVENT_LOG.jsonl'
    runtime_review_path.parent.mkdir(parents=True, exist_ok=True)
    operator_log_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_review_path.write_text(
        '{"schema_version":"runtime_review_record/v1","decision":"READY","signoff_status":"APPROVED"}\n',
        encoding='utf-8',
    )
    operator_log_path.write_text(
        '{"schema_version":"operator_command_event/v1","event_id":"operator-event-1","command_id":"ui-cmd-1"}\n',
        encoding='utf-8',
    )

    payload = build_ui_evidence_payload(repo_root=tmp_path, search_root=tmp_path / 'docs' / 'artifacts')

    registry_paths = [artifact['path'].replace('\\', '/') for artifact in payload['registry']['source_artifacts']]
    provenance_paths = [path.replace('\\', '/') for path in payload['section_provenance']['registry']['artifact_paths']]

    assert payload['registry']['source_artifact_count'] >= 2
    assert 'docs/artifacts/operator/ORACLE_OPERATOR_COMMAND_EVENT_LOG.jsonl' in registry_paths
    assert payload['section_provenance']['registry']['artifact_count'] == payload['registry']['source_artifact_count']
    assert 'docs/artifacts/operator/ORACLE_OPERATOR_COMMAND_EVENT_LOG.jsonl' in provenance_paths
