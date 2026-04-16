from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_terminal_record_request, materialize_operator_pack_terminal_record
from strategy_validator.projections import materialize_briefing_pack_bundle, materialize_operator_terminal_record_publication
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report


@pytest.mark.constitutional
def test_materialize_operator_terminal_record_publication_writes_bundle_and_index(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    record = materialize_operator_pack_terminal_record(
        build_operator_pack_terminal_record_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
            max_items=2,
        )
    )
    publication = materialize_operator_terminal_record_publication(tmp_path / 'terminal_records' / 'briefing', record, repo_root=tmp_path)

    assert publication.result.json_path.exists()
    assert publication.result.markdown_path.exists()
    assert publication.result.manifest_path.exists()
    assert publication.result.index_path.exists()
    assert publication.manifest['schema_version'] == 'oracle_operator_terminal_record_manifest/v1'
    assert publication.index['schema_version'] == 'oracle_operator_terminal_record_index/v1'
    assert publication.index['entry_count'] == 1


@pytest.mark.constitutional
def test_oracle_operator_pack_terminal_record_publish_cli_emits_publication_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    output_path = tmp_path / 'terminal_record_publication.json'
    publication_root = tmp_path / 'terminal_records' / 'briefing'
    assert main([
        'oracle-operator-pack-terminal-record-publish',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--current-pack-kind', 'briefing_pack',
        '--pack-kind', 'briefing_pack',
        '--publication-root', str(publication_root),
        '--output', str(output_path),
    ]) == 0
    payload = json.loads(output_path.read_text())
    assert payload['schema_version'] == 'oracle_operator_terminal_record_publication/v1'
    assert Path(payload['manifest_path']).exists()
    assert Path(payload['index_path']).exists()
