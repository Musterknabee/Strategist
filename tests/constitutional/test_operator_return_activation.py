from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_control_plane_bundle_request,
    build_operator_return_activation_request,
    materialize_governance_work_queue_state,
    materialize_operator_control_plane_bundle,
    materialize_operator_return_activation,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_return_activation_materializes_bundle(tmp_path: Path) -> None:
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
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
    )
    report = materialize_operator_return_activation(
        build_operator_return_activation_request(
            activation_root=tmp_path / 'return_activation',
            board_label='ops_board',
            activated_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
        ),
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state),
        board_label='ops_board',
    )
    assert report.schema_version == 'oracle_operator_return_activation/v1'
    assert report.activated_count >= 0
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_return_activation/v1'
    assert (tmp_path / 'return_activation' / 'ORACLE_OPERATOR_RETURN_ACTIVATION.json').exists()


@pytest.mark.constitutional
def test_operator_control_plane_bundle_includes_return_activation(tmp_path: Path) -> None:
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
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
    )
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(
            bundle_root=tmp_path / 'control_plane_bundle',
            board_label='ops_board',
            emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
        ),
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state),
    )
    assert 'return_activation' in bundle.bundle_sections
    payload = json.loads(Path(bundle.summary_output_path).read_text(encoding='utf-8'))
    assert 'return_activation' in payload


@pytest.mark.constitutional
def test_oracle_operator_return_activation_cli_emits_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'return_activation_report.json'
    activation_root = tmp_path / 'return_activation'
    rc = main([
        'oracle-operator-return-activation',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--activation-root', str(activation_root),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_return_activation/v1'
    assert (activation_root / 'ORACLE_OPERATOR_RETURN_ACTIVATION.json').exists()
