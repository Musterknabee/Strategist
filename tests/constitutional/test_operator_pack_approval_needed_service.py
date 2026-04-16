from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    OracleOperatorWorkboard,
    OracleOperatorWorkboardEntry,
    build_operator_pack_approval_needed_request,
    materialize_operator_pack_approval_needed,
)
from strategy_validator.projections.operator_pack_service import materialize_briefing_pack_bundle
from strategy_validator.validator.oracle_briefing import render_oracle_briefing_pack_markdown
from strategy_validator.validator.oracle_diagnostics import render_oracle_status_pack_markdown
from tests.constitutional.test_operator_pack_query_service import _build_briefing_report
from tests.constitutional.test_operator_pack_service_boundary import _status_report


@pytest.mark.constitutional
def test_operator_pack_approval_needed_materializes_approval_required_for_override_case(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    workboard = OracleOperatorWorkboard(
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

    approval_needed = materialize_operator_pack_approval_needed(
        build_operator_pack_approval_needed_request(
            search_root=tmp_path,
            repo_root=tmp_path,
            current_pack_kind='briefing_pack',
            pack_kinds=('briefing_pack',),
            queue_key='queue:governance',
            review_target='operator_review',
            priority_band='HIGH',
            action_owner_lane='research_ops',
            backup_owner_lane='governance_ops',
            ack_owner_lane='research_ops',
            board_label='triage',
            owner_label_prefix='shift-a',
            lease_label_prefix='lease-a',
            lifecycle_label_prefix='life-a',
            governance_label_prefix='gov-a',
            readiness_label_prefix='ready-a',
            dispatch_label_prefix='dispatch-a',
            outcome_label_prefix='outcome-a',
            exception_label_prefix='exception-a',
            approval_label_prefix='approval-a',
        ),
        operator_workboard=workboard,
    )

    assert approval_needed.schema_version == 'oracle_operator_pack_approval_needed/v1'
    assert approval_needed.total_approval_count == 1
    item = approval_needed.items[0]
    assert item.approval_posture == 'APPROVAL_REQUIRED'
    assert item.approval_state == 'APPROVAL_REQUIRED'
    assert item.approval_action == 'ESCALATE_FOR_APPROVAL'


@pytest.mark.constitutional
def test_briefing_pack_markdown_renders_operator_pack_approval_needed(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc), 'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    rendered = render_oracle_briefing_pack_markdown(newer)

    assert '## Operator Pack Approval Needed' in rendered
    assert 'Newest restricted briefing' in rendered


@pytest.mark.constitutional
def test_oracle_operator_pack_approval_needed_cli_emits_payload(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='CLI older trusted', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='CLI newer restricted', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    output_path = tmp_path / 'ORACLE_OPERATOR_PACK_APPROVAL_NEEDED.json'
    exit_code = main([
        'oracle-operator-pack-approval-needed',
        '--search-root', str(tmp_path),
        '--repo-root', str(tmp_path),
        '--current-pack-kind', 'briefing_pack',
        '--pack-kind', 'briefing_pack',
        '--queue-key', 'queue:governance',
        '--review-target', 'operator_review',
        '--priority-band', 'HIGH',
        '--action-owner-lane', 'research_ops',
        '--backup-owner-lane', 'governance_ops',
        '--ack-owner-lane', 'research_ops',
        '--owner-label-prefix', 'shift-a',
        '--lease-label-prefix', 'lease-a',
        '--lifecycle-label-prefix', 'life-a',
        '--governance-label-prefix', 'gov-a',
        '--readiness-label-prefix', 'ready-a',
        '--dispatch-label-prefix', 'dispatch-a',
        '--outcome-label-prefix', 'outcome-a',
        '--exception-label-prefix', 'exception-a',
        '--approval-label-prefix', 'approval-a',
        '--output', str(output_path),
    ])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_pack_approval_needed/v1'
    assert payload['total_approval_count'] == 1
    assert payload['items'][0]['approval_posture'] in {'NO_APPROVAL_NEEDED', 'APPROVAL_ELIGIBLE', 'APPROVAL_REQUIRED'}


@pytest.mark.constitutional
def test_status_pack_markdown_renders_operator_pack_approval_needed(tmp_path: Path) -> None:
    older = _build_briefing_report(tmp_path, summary_line='Older trusted briefing', trust_status='TRUSTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc)})
    newer = _build_briefing_report(tmp_path, summary_line='Newest restricted briefing', trust_status='TRUST_RESTRICTED').model_copy(update={'generated_at_utc': datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)})
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_old', older, markdown='old', html='<p>old</p>')
    materialize_briefing_pack_bundle(tmp_path / 'packs' / 'briefing_new', newer, markdown='new', html='<p>new</p>')

    status_report = _status_report(tmp_path).model_copy(update={'search_root': str(tmp_path), 'repo_root': str(tmp_path)})
    rendered = render_oracle_status_pack_markdown(status_report)

    assert '## Operator Pack Approval Needed' in rendered
    assert 'Newest restricted briefing' in rendered
