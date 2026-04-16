from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.oracle import OracleDerivedViewReport
from strategy_validator.projections.operator_pack_assembly import (
    assemble_oracle_briefing_pack,
    assemble_oracle_incident_pack,
    assemble_oracle_status_pack,
    build_briefing_pack_assembly_request,
    build_incident_pack_assembly_request,
    build_status_pack_assembly_request,
)
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_diagnostics import build_oracle_incident_pack, build_oracle_status_pack


_NOW = datetime(2026, 4, 14, tzinfo=timezone.utc)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode='json') if hasattr(payload, 'model_dump') else payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def _stable_report_payload(report) -> dict:
    payload = report.model_dump(mode='json')
    payload.pop('generated_at_utc', None)
    payload.pop('provenance_digest_sha256', None)
    if payload.get('status_pack'):
        payload['status_pack'].pop('generated_at_utc', None)
        payload['status_pack'].pop('provenance_digest_sha256', None)
    if payload.get('incident_pack_digest_sha256') is not None:
        payload['incident_pack_digest_sha256'] = '<digest>'
    if payload.get('status_pack_digest_sha256') is not None:
        payload['status_pack_digest_sha256'] = '<digest>'
    for section in payload.get('sections', []):
        refs = section.get('provenance_refs')
        if refs:
            section['provenance_refs'] = ['<provenance_ref>' for _ in refs]
        explanation = section.get('explanation')
        if explanation:
            explanation.pop('generated_at_utc', None)
    primary = payload.get('primary_diagnostic')
    if primary:
        primary.pop('generated_at_utc', None)
        explanation = primary.get('explanation')
        if explanation:
            explanation.pop('generated_at_utc', None)
    for artifact in payload.get('artifacts', []):
        artifact.pop('pack_path', None)
    return payload


@pytest.mark.constitutional
def test_status_pack_wrapper_delegates_to_assembly_service(tmp_path: Path) -> None:
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

    request = build_status_pack_assembly_request(repo_root=repo_root, search_root=search_root)
    service_report = assemble_oracle_status_pack(request=request)
    wrapper_report = build_oracle_status_pack(repo_root=repo_root, search_root=search_root)

    assert _stable_report_payload(wrapper_report) == _stable_report_payload(service_report)


@pytest.mark.constitutional
def test_incident_pack_wrapper_delegates_to_assembly_service(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    derived_path = search_root / 'ORACLE_DERIVED_VIEW.json'
    _write_json(
        derived_path,
        OracleDerivedViewReport(
            generated_at_utc=_NOW,
            lane_id='ORACLE_EVENT_LOG',
            view_label='weekly',
            window_entry_count=3,
            window_start_sequence_number=1,
            window_end_sequence_number=3,
            first_input_timestamp_utc=_NOW,
            last_input_timestamp_utc=_NOW,
            latest_event_id='evt-3',
            latest_dominant_regime='RISK_ON_LOW_VOL',
            latest_global_action='OBSERVE',
            latest_epistemic_status='UNKNOWN_UNKNOWNS',
            derived_classification='EVIDENCE_GAP',
            classification_counts={'EVIDENCE_GAP': 3},
            regime_counts={'RISK_ON_LOW_VOL': 3},
            global_action_counts={'OBSERVE': 3},
            epistemic_counts={'UNKNOWN': 3},
            evidence_gap_count=2,
            elevated_or_unknown_count=3,
            defensive_posture_count=0,
            retrain_pressure_count=1,
            average_posterior_edge_confidence=0.31,
            observed_entry_ids=['evt-1', 'evt-2', 'evt-3'],
            operator_actions=['repair evidence gaps before relying on this view'],
            summary_line='Derived view has unresolved evidence gaps.',
        ),
    )

    request = build_incident_pack_assembly_request(repo_root=repo_root, search_root=search_root)
    service_report = assemble_oracle_incident_pack(request=request)
    wrapper_report = build_oracle_incident_pack(repo_root=repo_root, search_root=search_root)

    assert wrapper_report.incident_kind == service_report.incident_kind
    assert wrapper_report.blocked == service_report.blocked
    assert wrapper_report.trust_status == service_report.trust_status
    assert len(wrapper_report.artifacts) == len(service_report.artifacts)
    assert wrapper_report.primary_diagnostic is not None
    assert service_report.primary_diagnostic is not None
    assert wrapper_report.primary_diagnostic.diagnostic_kind == service_report.primary_diagnostic.diagnostic_kind


@pytest.mark.constitutional
def test_briefing_pack_wrapper_delegates_to_assembly_service(tmp_path: Path) -> None:
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

    request = build_briefing_pack_assembly_request(repo_root=repo_root, search_root=search_root)
    service_report = assemble_oracle_briefing_pack(request=request)
    wrapper_report = build_oracle_briefing_pack(repo_root=repo_root, search_root=search_root)

    assert wrapper_report.trust_status == service_report.trust_status
    assert wrapper_report.operator_readiness == service_report.operator_readiness
    assert wrapper_report.governance_plane_status == service_report.governance_plane_status
    assert wrapper_report.automation_posture == service_report.automation_posture
    assert len(wrapper_report.sections) == len(service_report.sections)
    assert [section.section_id for section in wrapper_report.sections] == [section.section_id for section in service_report.sections]
    assert wrapper_report.summary_line == service_report.summary_line
