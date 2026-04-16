from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_reentry_assignment_request,
    build_operator_reentry_queue_state_request,
    materialize_governance_work_queue_state,
    materialize_operator_reentry_assignment,
    materialize_operator_reentry_queue_state,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_reentry_assignment_materializes_ownership_and_handoff(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='HOLD_FOR_REFRESH',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
    )
    query = run_operator_queue_query(governance_work_queue=queue_state)
    reentry = materialize_operator_reentry_queue_state(
        build_operator_reentry_queue_state_request(
            reentry_root=tmp_path / 'reentry',
            board_label='ops_board',
            reopened_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
        ),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    report = materialize_operator_reentry_assignment(
        build_operator_reentry_assignment_request(
            assignment_root=tmp_path / 'assignment',
            board_label='ops_board',
            assigned_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
        ),
        reentry_queue_state=reentry,
        board_label='ops_board',
    )
    assert report.schema_version == 'oracle_operator_reentry_assignment/v1'
    assert report.assignment_count == reentry.reentry_item_count
    assert report.items[0].assignee_label
    assert report.items[0].owner_lane.endswith('_LANE')
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['acceptance_posture'] in {'ACCEPTANCE_REQUIRED', 'AUTO_ACCEPTED'}


@pytest.mark.constitutional
def test_oracle_operator_reentry_assignment_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_REENTRY_ASSIGNMENT_REPORT.json'
    assignment_root = tmp_path / 'assignment'
    rc = main([
        'oracle-operator-reentry-assignment',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--assignment-root', str(assignment_root),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_reentry_assignment/v1'
    assert payload['assignment_count'] >= 1
    assert (assignment_root / 'ORACLE_OPERATOR_REENTRY_ASSIGNMENT.json').exists()


@pytest.mark.constitutional
def test_control_plane_bundle_includes_reentry_assignment(tmp_path: Path) -> None:
    output_path = tmp_path / 'bundle.json'
    bundle_root = tmp_path / 'bundle'
    rc = main([
        'oracle-operator-control-plane-bundle',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--bundle-root', str(bundle_root),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert 'reentry_assignment' in payload
    assert payload['reentry_assignment']['schema_version'] == 'oracle_operator_reentry_assignment/v1'
    assert (bundle_root / 'reentry_assignment' / 'ORACLE_OPERATOR_REENTRY_ASSIGNMENT.json').exists()
