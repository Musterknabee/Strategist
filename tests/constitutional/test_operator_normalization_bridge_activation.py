from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    build_operator_chronic_watch_outcome_request,
    build_operator_monitored_rejoin_normalization_bridge_request,
    build_operator_normalization_bridge_activation_request,
    materialize_operator_chronic_watch_outcome,
    materialize_operator_monitored_rejoin_normalization_bridge,
    materialize_operator_normalization_bridge_activation,
)
from tests.constitutional.test_operator_monitored_rejoin_normalization_bridge import _watch_outcome


@pytest.mark.constitutional
def test_operator_normalization_bridge_activation_materializes_typed_surface(tmp_path: Path) -> None:
    outcome = _watch_outcome(tmp_path)
    bridge = materialize_operator_monitored_rejoin_normalization_bridge(
        build_operator_monitored_rejoin_normalization_bridge_request(bridge_root=tmp_path/'bridge', board_label='ops_board', bridged_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        chronic_watch_outcome=outcome,
        board_label='ops_board',
    )
    report = materialize_operator_normalization_bridge_activation(
        build_operator_normalization_bridge_activation_request(activation_root=tmp_path/'activation', board_label='ops_board', activated_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC), monitoring_started_at_utc=datetime(2026,4,17,8,0,tzinfo=UTC)),
        monitored_rejoin_normalization_bridge=bridge,
        board_label='ops_board',
    )
    assert report.schema_version == 'oracle_operator_normalization_bridge_activation/v1'
    assert report.normalization_activation_count >= 1
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['activation_state'] in {'NORMALIZATION_BRIDGE_ACTIVATED','NORMALIZATION_BRIDGE_CONTINUES_WATCH','NORMALIZATION_BRIDGE_REOPEN_REQUIRED'}


@pytest.mark.constitutional
def test_oracle_operator_normalization_bridge_activation_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path/'report.json'
    rc = main([
        'oracle-operator-normalization-bridge-activation',
        '--issued-at-utc','2026-04-17T10:40:00Z',
        '--surface-label','status pack',
        '--board-label','ops_board',
        '--activation-root', str(tmp_path/'activation'),
        '--monitoring-started-at-utc','2026-04-17T08:00:00Z',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_normalization_bridge_activation/v1'
