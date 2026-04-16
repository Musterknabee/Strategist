from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timezone
from pathlib import Path
import json

import pytest

from strategy_validator.contracts.oracle import OracleDerivedViewReport
from strategy_validator.control_plane import (
    OracleOperatorQueueSnapshot,
    OracleOperatorQueueSnapshotRequest,
    assess_governance_plane,
    build_operator_queue_snapshot_request,
    materialize_governance_work_queue_state,
    materialize_operator_queue_snapshot,
)
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack


_NOW = datetime(2026, 4, 14, tzinfo=timezone.utc)


def _sample_governance_plane():
    return assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_NONE',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='test surface',
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode='json') if hasattr(payload, 'model_dump') else payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


@pytest.mark.constitutional

def test_operator_queue_snapshot_service_matches_governance_work_queue_state() -> None:
    governance_plane = _sample_governance_plane()
    issued_at_utc = datetime(2026, 4, 14, 12, 0, tzinfo=UTC)
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=issued_at_utc,
    )

    snapshot = materialize_operator_queue_snapshot(governance_work_queue=queue_state)

    assert snapshot.queue_key == queue_state.governance_claim_envelope.governance_plane_claim_queue_key
    assert snapshot.review_target == queue_state.governance_claim_envelope.governance_plane_claim_review_target
    assert snapshot.primary_work_item.claim_summary_line == queue_state.governance_claim_envelope.governance_plane_claim_summary_line
    assert snapshot.primary_work_item.dispatch_claim_key == queue_state.governance_dispatch_envelope.governance_plane_dispatch_claim_key
    assert snapshot.primary_work_item.claim_operability == queue_state.governance_claim_envelope.governance_plane_claim_operability
    assert snapshot.recommended_next_actions


@pytest.mark.constitutional

def test_operator_queue_snapshot_service_supports_typed_request_builder() -> None:
    governance_plane = _sample_governance_plane()
    issued_at_utc = datetime(2026, 4, 14, 12, 0, tzinfo=UTC)
    request = build_operator_queue_snapshot_request(
        governance_work_queue=materialize_governance_work_queue_state(
            governance_plane=governance_plane,
            issued_at_utc=issued_at_utc,
        )
    )

    snapshot = materialize_operator_queue_snapshot(request)

    assert isinstance(snapshot, OracleOperatorQueueSnapshot)
    assert isinstance(request, OracleOperatorQueueSnapshotRequest)
    assert snapshot.primary_work_item.review_due_by_utc == request.governance_work_queue.governance_claim_envelope.governance_plane_claim_review_due_by_utc


@pytest.mark.constitutional

def test_briefing_pack_consumes_operator_queue_snapshot_surface(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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

    from strategy_validator.validator import oracle_briefing as oracle_briefing_module

    original = oracle_briefing_module.materialize_operator_queue_snapshot

    def patched_snapshot(*args, **kwargs):
        snapshot = original(*args, **kwargs)
        mutated_item = replace(
            snapshot.primary_work_item,
            claim_summary_line='Operator queue snapshot seam consumed this custom claim summary.',
        )
        return replace(snapshot, primary_work_item=mutated_item, work_items=(mutated_item,))

    monkeypatch.setattr(oracle_briefing_module, 'materialize_operator_queue_snapshot', patched_snapshot)

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=search_root)

    assert report.governance_plane_claim_summary_line == 'Operator queue snapshot seam consumed this custom claim summary.'
