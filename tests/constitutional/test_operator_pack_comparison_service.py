from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_comparison_request, materialize_operator_pack_comparison
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report


@pytest.mark.constitutional
def test_operator_pack_comparison_detects_recent_briefing_changes(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older briefing summary', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': '2026-04-14T07:00:00Z'})
    newer = _build_briefing_report(tmp_path, summary_line='Newer briefing summary', trust_status='TRUSTED').model_copy(update={'generated_at_utc': '2026-04-14T08:00:00Z'})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    comparison = materialize_operator_pack_comparison(
        build_operator_pack_comparison_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
        )
    )

    assert comparison.schema_version == 'oracle_operator_pack_comparison/v1'
    assert comparison.total_comparison_count == 1
    item = comparison.items[0]
    assert item.pack_kind == 'briefing_pack'
    assert item.latest_summary_line == 'Newer briefing summary'
    assert item.previous_summary_line == 'Older briefing summary'
    assert 'summary_line' in item.changed_fields
    assert 'trust_status' in item.changed_fields


@pytest.mark.constitutional
def test_briefing_pack_markdown_renders_operator_pack_comparison(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older briefing summary', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': '2026-04-14T07:00:00Z'})
    newer = _build_briefing_report(tmp_path, summary_line='Newest briefing summary', trust_status='TRUSTED').model_copy(update={'generated_at_utc': '2026-04-14T08:00:00Z'})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    rendered = render_oracle_briefing_pack_markdown(newer.model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)}))

    assert '## Operator Pack Changes' in rendered
    assert 'Newest briefing summary' in rendered
    assert 'Older briefing summary' in rendered


@pytest.mark.constitutional
def test_oracle_operator_pack_comparison_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='CLI older summary', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': '2026-04-14T07:00:00Z'})
    newer = _build_briefing_report(tmp_path, summary_line='CLI newer summary', trust_status='TRUSTED').model_copy(update={'generated_at_utc': '2026-04-14T08:00:00Z'})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_COMPARISON.json'
    exit_code = main([
        'oracle-operator-pack-comparison',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--current-pack-kind', 'briefing_pack',
        '--pack-kind', 'briefing_pack',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_comparison/v1'
    assert payload['total_comparison_count'] == 1
    assert payload['items'][0]['latest_summary_line'] == 'CLI newer summary'
    assert 'summary_line' in payload['items'][0]['changed_fields']
