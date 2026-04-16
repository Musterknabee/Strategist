from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.ledger.event_store import AppendOnlyLedgerEventStore
from strategy_validator.ledger.projection_store import FilesystemProjectionStore
from strategy_validator.ledger.publication_store import FilesystemPublicationStore


def test_projection_store_lists_indexed_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / 'artifacts'
    artifact_dir.mkdir()
    (artifact_dir / 'view.json').write_text(json.dumps({'ok': True}), encoding='utf-8')
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
                        'output_artifact_paths': ['view.json'],
                        'output_artifact_labels': ['derived-view'],
                    }
                ]
            }
        ),
        encoding='utf-8',
    )
    payload = FilesystemProjectionStore().list_projection_artifacts(
        search_root=artifact_dir,
        repo_root=artifact_dir,
        projection_labels=('oracle_derived_view',),
        projection_family='canonical_event_projection',
    )
    assert payload['match_count'] == 1


def test_publication_store_writes_manifested_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / 'publication.json'
    record = FilesystemPublicationStore().publish_json_artifact(
        publication_label='release_bundle',
        artifact_path=output_path,
        payload={'ok': True},
        source_snapshot_id='snap-1',
    )
    assert output_path.exists()
    assert record.publication_family == 'application_publication'
    assert record.source_snapshot_ids == ['snap-1']


def test_event_store_surface_is_available() -> None:
    store = AppendOnlyLedgerEventStore()
    events = store.list_events()
    assert isinstance(events, tuple)
