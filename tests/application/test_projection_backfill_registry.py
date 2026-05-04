from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.projection_backfill import backfill_all_registered_projections, get_projection_registry


def test_projection_registry_exposes_expected_families() -> None:
    registry = get_projection_registry()
    families = {entry.projection_family for entry in registry}
    assert 'canonical_event_projection' in families
    assert 'canonical_event_checkpoint_projection' in families


def test_backfill_all_registered_projections(tmp_path: Path) -> None:
    artifact_dir = tmp_path / 'artifacts'
    artifact_dir.mkdir()
    (artifact_dir / 'projection.json').write_text(json.dumps({'ok': True}), encoding='utf-8')
    (artifact_dir / 'registry.projection.registry.json').write_text('{}', encoding='utf-8')
    (artifact_dir / 'ORACLE_PROJECTION_ARTIFACT_INDEX.json').write_text(
        json.dumps(
            {
                'entries': [
                    {
                        'projection_label': 'oracle_derived_view',
                        'projection_family': 'canonical_event_projection',
                        'projection_version': 'v1',
                        'generated_at_utc': '2026-01-01T00:00:00+00:00',
                        'registry_path': 'registry.projection.registry.json',
                        'output_artifact_paths': ['projection.json'],
                        'output_artifact_labels': ['derived-view'],
                    }
                ]
            }
        ),
        encoding='utf-8',
    )
    result = backfill_all_registered_projections(search_root=artifact_dir, repo_root=artifact_dir)
    assert result['registered_projection_count'] >= 2
    assert any(item['projection_family'] == 'canonical_event_projection' for item in result['families'])
