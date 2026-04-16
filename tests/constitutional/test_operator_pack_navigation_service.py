from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_navigation_request, materialize_operator_pack_navigation
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle, materialize_status_pack_bundle
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_navigation_selects_latest_relevant_packs(tmp_path: Path) -> None:
    briefing_old = _build_briefing_report(tmp_path, summary_line='Older briefing summary', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    briefing_new = _build_briefing_report(tmp_path, summary_line='Newest briefing summary', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)}
    )
    status_report = _status_report(tmp_path)

    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', briefing_old, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', briefing_new, markdown='new', html='<p>new</p>')
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_current', status_report, markdown='status', html='<p>status</p>')

    navigation = materialize_operator_pack_navigation(
        build_operator_pack_navigation_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='status_pack',
            preferred_pack_kinds=('briefing_pack', 'status_pack'),
            max_items=2,
        )
    )

    assert navigation.schema_version == 'oracle_operator_pack_navigation/v1'
    assert navigation.primary_item is not None
    assert navigation.primary_item.pack_kind == 'briefing_pack'
    assert navigation.primary_item.summary_line == 'Newest briefing summary'
    assert [item.pack_kind for item in navigation.items] == ['briefing_pack', 'status_pack']


@pytest.mark.constitutional
def test_status_pack_markdown_renders_related_operator_packs_from_navigation_service(tmp_path: Path) -> None:
    related_briefing = _build_briefing_report(tmp_path, summary_line='Linked briefing summary', trust_status='TRUSTED')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'related_briefing', related_briefing, markdown='brief', html='<p>brief</p>')

    status_report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    markdown = render_oracle_status_pack_markdown(status_report)

    assert '## Related Operator Packs' in markdown
    assert 'Linked briefing summary' in markdown
    assert 'briefing_pack' in markdown


@pytest.mark.constitutional
def test_oracle_operator_pack_navigation_cli_emits_selected_items(tmp_path: Path) -> None:
    briefing_report = _build_briefing_report(tmp_path, summary_line='Navigation CLI briefing summary', trust_status='TRUSTED')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_cli', briefing_report, markdown='brief', html='<p>brief</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_NAVIGATION.json'
    exit_code = main([
        'oracle-operator-pack-navigation',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--preferred-pack-kind', 'briefing_pack',
        '--max-items', '1',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_navigation/v1'
    assert payload['item_count'] == 1
    assert payload['primary_item']['pack_kind'] == 'briefing_pack'
    assert payload['primary_item']['summary_line'] == 'Navigation CLI briefing summary'
