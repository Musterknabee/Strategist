from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    build_operator_chronic_origin_restoration_provenance_request,
    build_operator_converged_normalization_attestation_request,
    build_operator_chronic_watch_audit_convergence_request,
    build_operator_monitored_rejoin_normalization_bridge_request,
    build_operator_normalization_bridge_activation_request,
    materialize_operator_chronic_origin_restoration_provenance,
    materialize_operator_converged_normalization_attestation,
    materialize_operator_chronic_watch_audit_convergence,
    materialize_operator_monitored_rejoin_normalization_bridge,
    materialize_operator_normalization_bridge_activation,
)
from tests.constitutional.test_operator_monitored_rejoin_normalization_bridge import _watch_outcome


@pytest.mark.constitutional
def test_operator_chronic_origin_restoration_provenance_materializes_typed_surface(tmp_path: Path) -> None:
    outcome = _watch_outcome(tmp_path)
    bridge = materialize_operator_monitored_rejoin_normalization_bridge(
        build_operator_monitored_rejoin_normalization_bridge_request(bridge_root=tmp_path/'bridge', board_label='ops_board', bridged_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        chronic_watch_outcome=outcome,
        board_label='ops_board',
    )
    activation = materialize_operator_normalization_bridge_activation(
        build_operator_normalization_bridge_activation_request(activation_root=tmp_path/'activation', board_label='ops_board', activated_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC), monitoring_started_at_utc=datetime(2026,4,17,8,0,tzinfo=UTC)),
        monitored_rejoin_normalization_bridge=bridge,
        board_label='ops_board',
    )
    convergence = materialize_operator_chronic_watch_audit_convergence(
        build_operator_chronic_watch_audit_convergence_request(convergence_root=tmp_path/'convergence', board_label='ops_board', converged_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        normalization_bridge_activation=activation,
        board_label='ops_board',
    )
    attestation = materialize_operator_converged_normalization_attestation(
        build_operator_converged_normalization_attestation_request(attestation_root=tmp_path/'attestation', board_label='ops_board', attested_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        chronic_watch_audit_convergence=convergence,
        board_label='ops_board',
    )
    report = materialize_operator_chronic_origin_restoration_provenance(
        build_operator_chronic_origin_restoration_provenance_request(provenance_root=tmp_path/'provenance', board_label='ops_board', recorded_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        converged_normalization_attestation=attestation,
        board_label='ops_board',
    )
    assert report.schema_version == 'oracle_operator_chronic_origin_restoration_provenance/v1'
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['provenance_state'] in {'CHRONIC_ORIGIN_PROVENANCE_RECORDED','CHRONIC_ORIGIN_PROVENANCE_HELD'}
    assert 'chronic_watch_handoff' in payload['items'][0]['provenance_chain']


@pytest.mark.constitutional
def test_oracle_operator_chronic_origin_restoration_provenance_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path/'report.json'
    rc = main([
        'oracle-operator-chronic-origin-restoration-provenance',
        '--issued-at-utc','2026-04-17T10:40:00Z',
        '--surface-label','status pack',
        '--board-label','ops_board',
        '--provenance-root', str(tmp_path/'provenance'),
        '--monitoring-started-at-utc','2026-04-17T08:00:00Z',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_chronic_origin_restoration_provenance/v1'
