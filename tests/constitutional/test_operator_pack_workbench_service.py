from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_workbench_request, materialize_operator_pack_workbench
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle, materialize_status_pack_bundle
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_workbench_groups_packs_by_kind_and_recency(tmp_path: Path) -> None:
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

    request = build_operator_pack_workbench_request(search_root=tmp_path, repo_root=tmp_path)
    workbench = materialize_operator_pack_workbench(request)

    assert workbench.schema_version == 'oracle_operator_pack_workbench/v1'
    assert workbench.total_item_count == 3
    assert [column.pack_kind for column in workbench.columns] == ['status_pack', 'briefing_pack']
    briefing_column = next(column for column in workbench.columns if column.pack_kind == 'briefing_pack')
    assert briefing_column.item_count == 2
    assert briefing_column.items[0].summary_line == 'Newest briefing summary'
    assert briefing_column.items[1].summary_line == 'Older briefing summary'
    assert briefing_column.items[0].primary_output_artifact_path is not None


@pytest.mark.constitutional
def test_oracle_operator_pack_workbench_cli_emits_structured_columns(tmp_path: Path) -> None:
    briefing_report = _build_briefing_report(tmp_path, summary_line='Workbench briefing summary', trust_status='TRUSTED')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_cli', briefing_report, markdown='brief', html='<p>brief</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_WORKBENCH.json'
    exit_code = main([
        'oracle-operator-pack-workbench',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--pack-kind', 'briefing_pack',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_workbench/v1'
    assert payload['total_item_count'] == 1
    assert payload['column_count'] == 1
    assert payload['columns'][0]['pack_kind'] == 'briefing_pack'
    assert payload['columns'][0]['items'][0]['summary_line'] == 'Workbench briefing summary'
