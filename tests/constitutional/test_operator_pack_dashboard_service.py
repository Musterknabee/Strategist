from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_dashboard_request, materialize_operator_pack_dashboard
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle, materialize_status_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_dashboard_materializes_overview_columns_and_navigation(tmp_path: Path) -> None:
    briefing_old = _build_briefing_report(tmp_path, summary_line='Older dashboard briefing', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    briefing_new = _build_briefing_report(tmp_path, summary_line='Newest dashboard briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)}
    )
    status_report = _status_report(tmp_path)

    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', briefing_old, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', briefing_new, markdown='new', html='<p>new</p>')
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_current', status_report, markdown='status', html='<p>status</p>')

    dashboard = materialize_operator_pack_dashboard(
        build_operator_pack_dashboard_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='status_pack',
            preferred_pack_kinds=('briefing_pack', 'status_pack'),
            max_navigation_items=2,
            max_column_items=2,
        )
    )

    assert dashboard.schema_version == 'oracle_operator_pack_dashboard/v1'
    assert dashboard.overview.total_item_count == 3
    assert dashboard.overview.pack_kind_count == 2
    assert dashboard.overview.primary_pack_kind == 'briefing_pack'
    assert [column.pack_kind for column in dashboard.columns] == ['status_pack', 'briefing_pack']
    assert dashboard.columns[1].primary_summary_line == 'Newest dashboard briefing'
    assert dashboard.navigation.primary_item is not None
    assert dashboard.navigation.primary_item.pack_kind == 'briefing_pack'


@pytest.mark.constitutional
def test_briefing_pack_markdown_renders_operator_pack_dashboard(tmp_path: Path) -> None:
    status_report = _status_report(tmp_path)
    materialize_status_pack_bundle(tmp_path / 'packs' / 'status_current', status_report, markdown='status', html='<p>status</p>')

    briefing_report = _build_briefing_report(tmp_path, summary_line='Dashboard render briefing', trust_status='TRUSTED').model_copy(
        update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)}
    )
    markdown = render_oracle_briefing_pack_markdown(briefing_report)

    assert '## Operator Pack Dashboard' in markdown
    assert '## Related Operator Packs' in markdown
    assert 'status_pack' in markdown


@pytest.mark.constitutional
def test_oracle_operator_pack_dashboard_cli_emits_dashboard_payload(tmp_path: Path) -> None:
    briefing_report = _build_briefing_report(tmp_path, summary_line='Dashboard CLI briefing', trust_status='TRUSTED')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_cli', briefing_report, markdown='brief', html='<p>brief</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_DASHBOARD.json'
    exit_code = main([
        'oracle-operator-pack-dashboard',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--preferred-pack-kind', 'briefing_pack',
        '--max-navigation-items', '1',
        '--max-column-items', '1',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_dashboard/v1'
    assert payload['overview']['total_item_count'] == 1
    assert payload['overview']['primary_pack_kind'] == 'briefing_pack'
    assert payload['navigation']['primary_item']['pack_kind'] == 'briefing_pack'
