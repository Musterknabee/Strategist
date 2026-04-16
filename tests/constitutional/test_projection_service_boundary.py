from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.oracle_projection_commands import cmd_oracle_projection_artifact_query
from strategy_validator.projections.service import (
    CANONICAL_EVENT_PROJECTION_FAMILY,
    CANONICAL_EVENT_PROJECTION_LABELS,
    build_projection_artifact_query,
    run_projection_artifact_operator_query,
    select_latest_canonical_event_projection,
)


def _write_index(root: Path, *, label: str, output_name: str, generated_at_utc: str) -> None:
    artifacts = root / 'artifacts'
    artifacts.mkdir(parents=True, exist_ok=True)
    output_path = artifacts / output_name
    output_path.write_text(json.dumps({'view_label': label}), encoding='utf-8')
    index = {
        'schema_version': 'oracle_projection_artifact_index/v1',
        'generated_at_utc': generated_at_utc,
        'entry_count': 1,
        'entries': [
            {
                'registry_path': str((artifacts / output_name.replace('.json', '.projection.registry.json')).resolve()),
                'projection_label': label,
                'projection_family': CANONICAL_EVENT_PROJECTION_FAMILY,
                'projection_version': 'v1',
                'generated_at_utc': generated_at_utc,
                'projection_digest_sha256': 'abc123',
                'source_artifact_count': 1,
                'output_artifact_count': 1,
                'source_artifact_labels': ['event_log'],
                'output_artifact_labels': ['primary_report'],
                'output_artifact_paths': [str(output_path.resolve())],
            }
        ],
    }
    (root / 'ORACLE_PROJECTION_ARTIFACT_INDEX.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')


def test_projection_service_selects_latest_canonical_event_projection(tmp_path: Path) -> None:
    _write_index(tmp_path / 'one', label='oracle_horizon_view', output_name='ORACLE_HORIZON_VIEW_custom.json', generated_at_utc='2026-04-14T10:00:00Z')
    _write_index(tmp_path / 'two', label='oracle_rolling_review', output_name='ORACLE_ROLLING_REVIEW_custom.json', generated_at_utc='2026-04-14T09:00:00Z')

    selection = select_latest_canonical_event_projection(search_root=tmp_path, repo_root=tmp_path)
    assert selection is not None
    assert selection.match is not None
    assert selection.match.projection_label == 'oracle_rolling_review'
    assert selection.output_artifact_path.name == 'ORACLE_ROLLING_REVIEW_custom.json'


def test_projection_service_operator_query_payload_round_trips(tmp_path: Path) -> None:
    _write_index(tmp_path, label='oracle_horizon_view', output_name='ORACLE_HORIZON_VIEW_custom.json', generated_at_utc='2026-04-14T10:00:00Z')
    query = build_projection_artifact_query(
        search_root=tmp_path,
        repo_root=tmp_path,
        projection_labels=CANONICAL_EVENT_PROJECTION_LABELS,
        projection_family=CANONICAL_EVENT_PROJECTION_FAMILY,
    )
    result = run_projection_artifact_operator_query(query)
    payload = result.to_payload()
    assert payload['match_count'] == 1
    assert payload['matches'][0]['projection_label'] == 'oracle_horizon_view'


def test_oracle_projection_artifact_query_cli_uses_service_boundary(tmp_path: Path) -> None:
    _write_index(tmp_path, label='oracle_horizon_view', output_name='ORACLE_HORIZON_VIEW_custom.json', generated_at_utc='2026-04-14T10:00:00Z')
    output_path = tmp_path / 'query.json'

    class NS:
        search_root = str(tmp_path)
        repo_root = str(tmp_path)
        projection_label = ['oracle_horizon_view']
        projection_family = CANONICAL_EVENT_PROJECTION_FAMILY
        output_artifact_label_contains = 'primary'
        output = str(output_path)

    rc = cmd_oracle_projection_artifact_query(NS())
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['match_count'] == 1
    assert payload['matches'][0]['projection_label'] == 'oracle_horizon_view'
