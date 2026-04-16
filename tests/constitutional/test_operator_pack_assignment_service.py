from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import build_operator_pack_assignment_request, materialize_operator_pack_assignment
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_assignment_materializes_owner_lane_and_handoff(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='New untrusted briefing', trust_status='UNTRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    assignment = materialize_operator_pack_assignment(
        build_operator_pack_assignment_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
            queue_key='queue:governance',
            review_target='operator_review',
            priority_band='HIGH',
            action_owner_lane='research_ops',
            backup_owner_lane='governance_ops',
            board_label='triage',
            owner_label_prefix='shift-a',
        )
    )

    assert assignment.schema_version == 'oracle_operator_pack_assignment/v1'
    assert assignment.total_assignment_count == 1
    item = assignment.items[0]
    assert item.ownership_posture == 'ASSIGN_IMMEDIATE_OWNER'
    assert item.owner_lane == 'research_ops'
    assert item.backup_owner_lane == 'governance_ops'
    assert item.owner_label == 'shift-a/research_ops:operator_review'
    assert item.handoff_target == 'research_ops:queue:governance'


@pytest.mark.constitutional
def test_briefing_pack_markdown_renders_operator_pack_assignments(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc), 'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    rendered = render_oracle_briefing_pack_markdown(newer)

    assert '## Operator Pack Assignments' in rendered
    assert 'Newest restricted briefing' in rendered
    assert 'ASSIGN_QUEUE_OWNER' in rendered


@pytest.mark.constitutional
def test_oracle_operator_pack_assignment_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='CLI older trusted', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='CLI newer restricted', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_ASSIGNMENT.json'
    exit_code = main([
        'oracle-operator-pack-assignment',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--current-pack-kind', 'briefing_pack',
        '--pack-kind', 'briefing_pack',
        '--queue-key', 'queue:governance',
        '--review-target', 'operator_review',
        '--priority-band', 'HIGH',
        '--action-owner-lane', 'research_ops',
        '--backup-owner-lane', 'governance_ops',
        '--owner-label-prefix', 'shift-a',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_assignment/v1'
    assert payload['total_assignment_count'] == 1
    assert payload['items'][0]['owner_lane'] == 'research_ops'


@pytest.mark.constitutional
def test_status_pack_markdown_renders_operator_pack_assignments(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    status_report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    rendered = render_oracle_status_pack_markdown(status_report)

    assert '## Operator Pack Assignments' in rendered
    assert 'Newest restricted briefing' in rendered
