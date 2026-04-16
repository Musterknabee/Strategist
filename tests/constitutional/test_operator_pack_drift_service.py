from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_drift_request, materialize_operator_pack_drift
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_service_boundary import _status_report
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report


@pytest.mark.constitutional
def test_operator_pack_drift_flags_worsening_pack_generations(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)}
    )
    newer = _build_briefing_report(tmp_path, summary_line='New restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    drift = materialize_operator_pack_drift(
        build_operator_pack_drift_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
        )
    )

    assert drift.schema_version == 'oracle_operator_pack_drift/v1'
    assert drift.total_alert_count == 1
    item = drift.items[0]
    assert item.pack_kind == 'briefing_pack'
    assert item.drift_state == 'WORSENING'
    assert item.latest_trust_status == 'TRUST_RESTRICTED'
    assert item.previous_trust_status == 'TRUSTED'
    assert item.severity == 'ELEVATED'
    assert 'trust_status' in item.changed_fields


@pytest.mark.constitutional
def test_operator_pack_drift_flags_sustained_degraded_generations(tmp_path: Path) -> None:
    oldest = _build_briefing_report(tmp_path, summary_line='Old restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 6, 0, tzinfo=timezone.utc)}
    )
    previous = _build_briefing_report(tmp_path, summary_line='Previous restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)}
    )
    latest = _build_briefing_report(tmp_path, summary_line='Latest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_oldest', oldest, markdown='oldest', html='<p>oldest</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_previous', previous, markdown='previous', html='<p>previous</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_latest', latest, markdown='latest', html='<p>latest</p>')

    drift = materialize_operator_pack_drift(
        build_operator_pack_drift_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
            sustained_degraded_threshold=2,
        )
    )

    assert drift.total_alert_count == 1
    item = drift.items[0]
    assert item.drift_state == 'SUSTAINED_DEGRADED'
    assert item.degraded_streak_count == 3
    assert item.latest_trust_status == 'TRUST_RESTRICTED'


@pytest.mark.constitutional
def test_briefing_pack_markdown_renders_operator_pack_drift(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)}
    )
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc), 'search_root': str(tmp_path), 'repo_root': str(tmp_path)}
    )
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    rendered = render_oracle_briefing_pack_markdown(newer)

    assert '## Operator Pack Drift Alerts' in rendered
    assert 'WORSENING' in rendered
    assert 'Newest restricted briefing' in rendered


@pytest.mark.constitutional
def test_oracle_operator_pack_drift_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='CLI older trusted', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)}
    )
    newer = _build_briefing_report(tmp_path, summary_line='CLI newer restricted', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_DRIFT.json'
    exit_code = main([
        'oracle-operator-pack-drift',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--current-pack-kind', 'briefing_pack',
        '--pack-kind', 'briefing_pack',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_drift/v1'
    assert payload['total_alert_count'] == 1
    assert payload['items'][0]['drift_state'] == 'WORSENING'
    assert payload['items'][0]['latest_summary_line'] == 'CLI newer restricted'


@pytest.mark.constitutional
def test_status_pack_markdown_renders_operator_pack_drift(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)}
    )
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(
        update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)}
    )
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    status_report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    rendered = render_oracle_status_pack_markdown(status_report)

    assert '## Operator Pack Drift Alerts' in rendered
    assert 'Newest restricted briefing' in rendered
