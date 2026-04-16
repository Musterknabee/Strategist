from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_timeline_request, materialize_operator_pack_timeline
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle, materialize_status_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from tests.constitutional.test_operator_pack_headers import _briefing_pack, _status_pack


def test_operator_pack_timeline_orders_recent_activity(tmp_path: Path) -> None:
    status_old = _status_pack().__class__(**{**_status_pack().__dict__, 'generated_at_utc': '2026-01-01T00:00:00Z'})
    status_new = _status_pack().__class__(**{**_status_pack().__dict__, 'generated_at_utc': '2026-01-03T00:00:00Z'})
    briefing = _briefing_pack().__class__(**{**_briefing_pack().__dict__, 'generated_at_utc': '2026-01-02T00:00:00Z'})
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_old', status_old, markdown='old', html='<p>old</p>')
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_new', status_new, markdown='new', html='<p>new</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_mid', briefing, markdown='brief', html='<p>brief</p>')

    timeline = materialize_operator_pack_timeline(
        build_operator_pack_timeline_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('status_pack', 'briefing_pack'),
            max_items=3,
        )
    )

    assert timeline.schema_version == 'oracle_operator_pack_timeline/v1'
    assert timeline.total_match_count == 3
    assert len(timeline.items) == 3
    assert {item.pack_kind for item in timeline.items} == {'status_pack', 'briefing_pack'}
    assert any(item.is_current_pack_kind for item in timeline.items if item.pack_kind == 'briefing_pack')


def test_briefing_pack_markdown_renders_operator_pack_timeline(tmp_path: Path) -> None:
    briefing_report = _briefing_pack().__class__(**{**_briefing_pack().__dict__, 'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    related_status = _status_pack().__class__(**{**_status_pack().__dict__, 'generated_at_utc': '2026-01-03T00:00:00Z'})
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_related', related_status, markdown='status', html='<p>status</p>')
    markdown = render_oracle_briefing_pack_markdown(briefing_report)
    assert '## Operator Pack Timeline' in markdown
    assert 'status_pack' in markdown


def test_oracle_operator_pack_timeline_cli_emits_timeline_payload(tmp_path: Path) -> None:
    briefing_report = _briefing_pack().__class__(**{**_briefing_pack().__dict__, 'generated_at_utc': '2026-01-02T00:00:00Z'})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_cli', briefing_report, markdown='brief', html='<p>brief</p>')
    output_path = tmp_path / 'timeline.json'

    exit_code = main([
        'oracle-operator-pack-timeline',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--pack-kind', 'briefing_pack',
        '--max-items', '2',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_timeline/v1'
    assert payload['item_count'] == 1
    assert payload['items'][0]['pack_kind'] == 'briefing_pack'
