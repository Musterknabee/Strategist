from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    materialize_governance_work_queue_state,
    materialize_operator_queue_snapshot,
    run_operator_queue_query,
)
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.contracts.oracle import OracleDerivedViewReport


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode='json') if hasattr(payload, 'model_dump') else payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def test_operator_queue_query_service_emits_explicit_work_item_state() -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_NONE',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='queue query surface test',
    )
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
    )
    result = run_operator_queue_query(
        operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state)
    )

    assert result.work_item_count == 1
    assert result.work_items[0].queue_key == result.queue_key
    assert result.work_items[0].dispatch_posture
    assert result.recommended_next_actions


def test_rollout_ops_oracle_operator_queue_query_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_QUEUE_QUERY_REPORT.json'
    rc = main([
        'oracle-operator-queue-query',
        '--issued-at-utc', '2026-04-14T12:00:00+00:00',
        '--surface-label', 'operator queue cli test',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_queue_query_report/v1'
    assert payload['work_item_count'] == 1
    assert payload['work_items'][0]['queue_key'] == payload['queue_key']


def test_briefing_pack_renders_explicit_operator_queue_section(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    now = datetime(2026, 4, 14, 12, 0, tzinfo=UTC)
    _write_json(
        search_root / 'ORACLE_DERIVED_VIEW.json',
        OracleDerivedViewReport(
            generated_at_utc=now,
            lane_id='ORACLE_EVENT_LOG',
            view_label='weekly',
            window_entry_count=2,
            window_start_sequence_number=1,
            window_end_sequence_number=2,
            first_input_timestamp_utc=now,
            last_input_timestamp_utc=now,
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
    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=search_root)
    operator_queue_section = next(section for section in report.sections if section.section_id == 'operator_queue')
    assert operator_queue_section.status == report.governance_plane_status
    assert any(fact.startswith('queue_key=') for fact in operator_queue_section.facts)
    assert any(fact.startswith('primary_work_item_key=') for fact in operator_queue_section.facts)
