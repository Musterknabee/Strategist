from __future__ import annotations

import json
from datetime import UTC, datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleDerivedViewReport
from strategy_validator.control_plane import (
    OracleOperatorWorkboard,
    OracleOperatorWorkboardRequest,
    assess_governance_plane,
    build_operator_workboard_request,
    materialize_operator_workboard,
    materialize_governance_work_queue_state,
    run_operator_queue_query,
)
from strategy_validator.validator.oracle_diagnostics import build_oracle_incident_pack, build_oracle_status_pack


_NOW = datetime(2026, 4, 14, tzinfo=timezone.utc)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode='json') if hasattr(payload, 'model_dump') else payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def _sample_governance_plane():
    return assess_governance_plane(
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


@pytest.mark.constitutional
def test_operator_workboard_service_supports_typed_request_builder() -> None:
    queue_state = materialize_governance_work_queue_state(
        governance_plane=_sample_governance_plane(),
        issued_at_utc=datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
    )
    request = build_operator_workboard_request(
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state)
    )
    workboard = materialize_operator_workboard(request=request)
    assert isinstance(request, OracleOperatorWorkboardRequest)
    assert isinstance(workboard, OracleOperatorWorkboard)
    assert workboard.work_item_count == 1
    assert workboard.entries[0].queue_key == workboard.queue_key


@pytest.mark.constitutional
def test_status_and_incident_pack_embed_operator_workboard(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    derived_path = search_root / 'ORACLE_DERIVED_VIEW.json'
    _write_json(
        derived_path,
        OracleDerivedViewReport(
            generated_at_utc=_NOW,
            lane_id='ORACLE_EVENT_LOG',
            view_label='weekly',
            window_entry_count=2,
            window_start_sequence_number=1,
            window_end_sequence_number=2,
            first_input_timestamp_utc=_NOW,
            last_input_timestamp_utc=_NOW,
            latest_event_id='evt-2',
            latest_dominant_regime='TRANSITION',
            latest_global_action='CANARY_REVIEW',
            latest_epistemic_status='ELEVATED',
            derived_classification='HEIGHTENED_WATCH',
            classification_counts={'HEIGHTENED_WATCH': 2},
            regime_counts={'TRANSITION': 2},
            global_action_counts={'CANARY_REVIEW': 2},
            epistemic_counts={'ELEVATED': 2},
            evidence_gap_count=0,
            elevated_or_unknown_count=2,
            defensive_posture_count=0,
            retrain_pressure_count=0,
            average_posterior_edge_confidence=0.54,
            observed_entry_ids=['evt-1', 'evt-2'],
            operator_actions=['maintain heightened watch'],
            summary_line='Oracle posture is elevated but replayable.',
        ),
    )
    status_pack = build_oracle_status_pack(repo_root=repo_root, search_root=search_root)
    incident_pack = build_oracle_incident_pack(repo_root=repo_root, search_root=search_root)

    assert status_pack.operator_workboard is not None
    assert status_pack.operator_workboard.work_item_count >= 1
    assert status_pack.operator_workboard.entries[0].queue_key == status_pack.operator_workboard.queue_key
    assert incident_pack.operator_workboard is not None
    assert incident_pack.operator_workboard.queue_key == status_pack.operator_workboard.queue_key


@pytest.mark.constitutional
def test_operator_workboard_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_WORKBOARD.json'
    rc = main([
        'oracle-operator-workboard-query',
        '--issued-at-utc', '2026-04-14T12:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_workboard/v1'
    assert payload['board_label'] == 'ops_board'
    assert payload['work_item_count'] == 1
    assert payload['entries'][0]['queue_key'] == payload['queue_key']
