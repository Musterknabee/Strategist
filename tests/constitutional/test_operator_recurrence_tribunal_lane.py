from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_recurrence_tribunal_lane_request,
    build_operator_reopen_lineage_request,
    build_operator_reopen_recurrence_policy_request,
    build_operator_chronic_instability_packet_request,
    materialize_governance_work_queue_state,
    materialize_operator_recurrence_tribunal_lane,
    materialize_operator_reopen_lineage,
    materialize_operator_reopen_recurrence_policy,
    materialize_operator_chronic_instability_packet,
    render_operator_control_plane_bundle_markdown_lines,
    build_operator_control_plane_bundle_request,
    materialize_operator_control_plane_bundle,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_recurrence_tribunal_lane_materializes_review_lane(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    reopen_lineage = materialize_operator_reopen_lineage(
        build_operator_reopen_lineage_request(
            lineage_root=tmp_path / 'reopen_lineage',
            board_label='ops_board',
            analyzed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC),
            prior_reopen_counts={'work:status_pack:release_readiness': 3},
        ),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    recurrence_policy = materialize_operator_reopen_recurrence_policy(
        build_operator_reopen_recurrence_policy_request(
            policy_root=tmp_path / 'reopen_recurrence_policy',
            board_label='ops_board',
            evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC),
        ),
        reopen_lineage=reopen_lineage,
        board_label='ops_board',
    )
    packet = materialize_operator_chronic_instability_packet(
        build_operator_chronic_instability_packet_request(
            packet_root=tmp_path / 'chronic_instability_packet',
            board_label='ops_board',
            emitted_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC),
        ),
        reopen_recurrence_policy=recurrence_policy,
        board_label='ops_board',
    )
    report = materialize_operator_recurrence_tribunal_lane(
        build_operator_recurrence_tribunal_lane_request(
            tribunal_root=tmp_path / 'recurrence_tribunal_lane',
            board_label='ops_board',
            reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC),
        ),
        chronic_instability_packet=packet,
        board_label='ops_board',
    )
    assert report.schema_version == 'oracle_operator_recurrence_tribunal_lane/v1'
    assert report.tribunal_review_required_count >= 1
    assert Path(report.summary_output_path).exists()


@pytest.mark.constitutional
def test_operator_control_plane_bundle_includes_recurrence_escalation_layers(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=tmp_path / 'bundle', board_label='ops_board', emitted_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)),
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state),
    )
    rendered = '\n'.join(render_operator_control_plane_bundle_markdown_lines(bundle))
    assert 'Chronic instability packets:' in rendered
    assert 'Recurrence tribunal lane:' in rendered
    payload = json.loads(Path(bundle.summary_output_path).read_text(encoding='utf-8'))
    assert 'chronic_instability_packet' in payload
    assert 'recurrence_tribunal_lane' in payload


@pytest.mark.constitutional
def test_oracle_operator_recurrence_tribunal_lane_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'tribunal_report.json'
    tribunal_root = tmp_path / 'tribunal'
    rc = main([
        'oracle-operator-recurrence-tribunal-lane',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--tribunal-root', str(tribunal_root),
        '--prior-reopen-count', 'work:status_pack:release_readiness=3',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_recurrence_tribunal_lane/v1'
    assert payload['chronic_lane_count'] >= 1
