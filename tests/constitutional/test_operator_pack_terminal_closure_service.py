from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    OracleOperatorWorkboard,
    OracleOperatorWorkboardEntry,
    build_operator_pack_terminal_closure_request,
    materialize_operator_pack_terminal_closure,
)
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


def _workboard() -> OracleOperatorWorkboard:
    return OracleOperatorWorkboard(
        board_label='triage',
        queue_key='queue:governance',
        review_target='operator_review',
        priority_band='HIGH',
        review_due_by_utc=datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc),
        review_sort_key='HIGH:2026-04-14T09:00:00+00:00',
        work_item_count=1,
        summary_line='triage board',
        queue_summary_line='queue summary',
        recommended_next_actions=('review now',),
        entries=(
            OracleOperatorWorkboardEntry(
                work_item_key='work-1',
                queue_key='queue:governance',
                review_target='operator_review',
                priority_band='HIGH',
                review_due_by_utc=datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc),
                review_sort_key='HIGH:2026-04-14T09:00:00+00:00',
                action_owner_lane='research_ops',
                claim_operability='READY',
                dispatch_posture='EXPEDITED',
                urgency='HIGH',
                score=90,
                summary_line='claim summary',
                recommended_actions=('act now',),
            ),
        ),
    )


@pytest.mark.constitutional
def test_operator_pack_terminal_closure_materializes(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    closure = materialize_operator_pack_terminal_closure(build_operator_pack_terminal_closure_request(search_root=tmp_path, repo_root=tmp_path, current_pack_kind='briefing_pack', pack_kinds=('briefing_pack',), max_items=2), operator_workboard=_workboard())

    assert closure.items
    assert closure.items[0].closure_posture in {'CLOSE_READY', 'RETAIN_OPEN', 'ARCHIVE_READY'}


@pytest.mark.constitutional
def test_oracle_operator_pack_terminal_closure_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    output_path = tmp_path / 'terminal_closure.json'
    assert main(['oracle-operator-pack-terminal-closure', '--search-root', str(tmp_path), '--repo-root', str(tmp_path), '--current-pack-kind', 'briefing_pack', '--pack-kind', 'briefing_pack', '--output', str(output_path)]) == 0
    payload = json.loads(output_path.read_text())
    assert payload['schema_version'] == 'oracle_operator_pack_terminal_closure/v1'


@pytest.mark.constitutional
def test_render_oracle_briefing_pack_markdown_includes_terminal_closure_section(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc), 'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    assert '## Operator Pack Terminal Closure' in render_oracle_briefing_pack_markdown(newer)


@pytest.mark.constitutional
def test_render_oracle_status_pack_markdown_includes_terminal_closure_section(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')
    report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path), 'operator_workboard': _workboard()})
    assert '## Operator Pack Terminal Closure' in render_oracle_status_pack_markdown(report)
