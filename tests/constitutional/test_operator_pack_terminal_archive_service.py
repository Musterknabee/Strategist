from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_terminal_archive_request, materialize_operator_pack_terminal_archive
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_terminal_archive_materializes(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    archive = materialize_operator_pack_terminal_archive(build_operator_pack_terminal_archive_request(search_root=tmp_path, repo_root=tmp_path, current_pack_kind='briefing_pack', pack_kinds=('briefing_pack',), max_items=2))

    assert archive.items
    assert archive.items[0].retention_posture in {'ARCHIVE_MANIFEST_READY', 'RETAIN_CLOSURE_RECORD', 'RETAIN_OPEN_CASE'}


@pytest.mark.constitutional
def test_oracle_operator_pack_terminal_archive_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    output_path = tmp_path / 'terminal_archive.json'
    assert main(['oracle-operator-pack-terminal-archive', '--search-root', str(tmp_path), '--repo-root', str(tmp_path), '--current-pack-kind', 'briefing_pack', '--pack-kind', 'briefing_pack', '--output', str(output_path)]) == 0
    payload = json.loads(output_path.read_text())
    assert payload['schema_version'] == 'oracle_operator_pack_terminal_archive/v1'


@pytest.mark.constitutional
def test_render_oracle_briefing_pack_markdown_includes_terminal_archive_section(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc), 'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    assert '## Operator Pack Terminal Archive' in render_oracle_briefing_pack_markdown(newer)


@pytest.mark.constitutional
def test_render_oracle_status_pack_markdown_includes_terminal_archive_section(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    assert '## Operator Pack Terminal Archive' in render_oracle_status_pack_markdown(report)
