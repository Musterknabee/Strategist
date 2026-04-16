from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import (
    OracleConstitutionalGateReport,
    OracleDerivedViewReport,
    OracleDoctrineLineageVerification,
    OracleEventCheckpointManifest,
    OracleEventCheckpointVerification,
)
from strategy_validator.validator.oracle_explain import (
    explain_constitutional_gate,
    explain_derived_view_trust,
    explain_event_checkpoint_trust,
    explain_lineage_verification,
)


_NOW = datetime(2026, 4, 13, tzinfo=timezone.utc)


def _lineage(*, seal_status: str = 'FULLY_SEALED') -> OracleDoctrineLineageVerification:
    return OracleDoctrineLineageVerification(
        verified_at_utc=_NOW,
        repo_root='.',
        search_root='./docs/artifacts',
        seal_status=seal_status,
        completeness_score=1.0 if seal_status == 'FULLY_SEALED' else 0.82,
        completeness_percent=100 if seal_status == 'FULLY_SEALED' else 82,
        required_layer_count=10,
        valid_required_layer_count=10 if seal_status == 'FULLY_SEALED' else 8,
        layer_presence={'oracle_constitutional_digest_evidence': seal_status == 'FULLY_SEALED'},
        layer_validity={'oracle_constitutional_digest_evidence': seal_status == 'FULLY_SEALED'},
        missing_required_layers=[] if seal_status == 'FULLY_SEALED' else ['oracle_constitutional_digest_evidence'],
        missing_optional_layers=[],
        parse_failures=[],
        integrity_warnings=[],
        operator_actions=['repair missing doctrine coverage'] if seal_status != 'FULLY_SEALED' else ['continue normal review cadence'],
        summary_line=f'lineage summary {seal_status}',
    )


@pytest.mark.constitutional
def test_explain_derived_view_trust_emits_reason_tree() -> None:
    report = OracleDerivedViewReport(
        generated_at_utc=_NOW,
        lane_id='ORACLE_EVENT_LOG',
        view_label='weekly',
        window_entry_count=5,
        window_start_sequence_number=1,
        window_end_sequence_number=5,
        first_input_timestamp_utc=_NOW,
        last_input_timestamp_utc=_NOW,
        latest_event_id='evt-5',
        latest_dominant_regime='RISK_ON_LOW_VOL',
        latest_global_action='OBSERVE',
        latest_epistemic_status='NOMINAL',
        derived_classification='STABLE_BASELINE',
        classification_counts={'STABLE_BASELINE': 5},
        regime_counts={'RISK_ON_LOW_VOL': 5},
        global_action_counts={'OBSERVE': 5},
        epistemic_counts={'NOMINAL': 5},
        evidence_gap_count=0,
        elevated_or_unknown_count=0,
        defensive_posture_count=0,
        retrain_pressure_count=0,
        average_posterior_edge_confidence=0.77,
        observed_entry_ids=['evt-1', 'evt-5'],
        operator_actions=['hold current research posture'],
        summary_line='weekly stable',
    )
    explanation = explain_derived_view_trust(report, lineage_verification=_lineage())
    assert explanation.trust_status == 'TRUSTED'
    assert explanation.explanation_kind == 'derived_view'
    assert explanation.nodes[0].category == 'trust'
    assert any(node.category == 'lineage' for node in explanation.nodes)
    assert any(node.category == 'operator_action' for node in explanation.nodes)


@pytest.mark.constitutional
def test_explain_constitutional_gate_emits_policy_reason_tree() -> None:
    report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root='.',
        search_root='./docs/artifacts',
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='CONSTITUTIONALLY_REPLAYABLE',
        lineage_completeness_percent=82,
        constitutional_digest_classification='CONSTITUTIONAL_STABLE_BASELINE',
        manifest_verification_status='VERIFIED',
        trust_status='TRUST_RESTRICTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status CONSTITUTIONALLY_REPLAYABLE is below required threshold FULLY_SEALED'],
        operator_actions=['repair missing doctrine coverage'],
        summary_line='restricted constitutional gate',
    )
    explanation = explain_constitutional_gate(report)
    assert explanation.trust_status == 'TRUST_RESTRICTED'
    assert any(node.category == 'policy' and node.conclusion == 'THRESHOLD_NOT_MET' for node in explanation.nodes)
    assert any(node.category == 'policy' and node.conclusion == 'BLOCKING_REASONS' for node in explanation.nodes)


@pytest.mark.constitutional
def test_explain_event_checkpoint_emits_evidence_and_lineage_nodes() -> None:
    manifest = OracleEventCheckpointManifest(
        generated_at_utc=_NOW,
        checkpoint_id='chk-1',
        lane_id='ORACLE_EVENT_LOG',
        view_label='weekly',
        source_event_log_path='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl',
        execution_authority='ADVISORY_ONLY',
        derived_classification='STABLE_BASELINE',
        window_entry_count=5,
        window_start_sequence_number=1,
        window_end_sequence_number=5,
        last_entry_hash='a' * 64,
        latest_event_id='evt-5',
        integrity_status='VERIFIED',
        subjects=[],
        missing_artifact_paths=[],
        summary_line='checkpoint stable',
    )
    verification = OracleEventCheckpointVerification(
        verified_at_utc=_NOW,
        manifest_path='docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.json',
        status='VERIFIED',
        artifact_digests_verified=True,
        signature_verified=True,
        verified_subject_count=2,
        digest_mismatches=[],
        missing_artifact_paths=[],
        notes=[],
    )
    explanation = explain_event_checkpoint_trust(manifest, verification, lineage_verification=_lineage())
    assert explanation.trust_status == 'TRUSTED'
    assert any(node.category == 'evidence' for node in explanation.nodes)
    assert any(node.category == 'lineage' for node in explanation.nodes)


@pytest.mark.constitutional
def test_oracle_explain_cli_supports_report_and_checkpoint_inputs(tmp_path: Path) -> None:
    report_path = tmp_path / 'ORACLE_DERIVED_VIEW.json'
    report = OracleDerivedViewReport(
        generated_at_utc=_NOW,
        lane_id='ORACLE_EVENT_LOG',
        view_label='weekly',
        window_entry_count=1,
        derived_classification='EVIDENCE_GAP',
        evidence_gap_count=1,
        elevated_or_unknown_count=1,
        defensive_posture_count=0,
        retrain_pressure_count=0,
        average_posterior_edge_confidence=0.2,
        observed_entry_ids=['evt-1'],
        operator_actions=['repair evidence gap'],
        summary_line='gap',
    )
    report_path.write_text(report.model_dump_json(indent=2), encoding='utf-8')
    explanation_path = tmp_path / 'ORACLE_TRUST_EXPLANATION_REPORT.json'
    markdown_path = tmp_path / 'ORACLE_TRUST_EXPLANATION_REPORT.md'
    rc = main([
        'oracle-explain',
        '--report', str(report_path),
        '--output', str(explanation_path),
        '--markdown-output', str(markdown_path),
    ])
    assert rc == 0
    payload = json.loads(explanation_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_trust_explanation_report/v1'
    assert payload['explanation_kind'] == 'derived_view'
    assert 'Trust explanation' in markdown_path.read_text(encoding='utf-8')

    manifest_path = tmp_path / 'ORACLE_EVENT_CHECKPOINT.json'
    verification_path = tmp_path / 'ORACLE_EVENT_CHECKPOINT.verification.json'
    manifest = OracleEventCheckpointManifest(
        generated_at_utc=_NOW,
        checkpoint_id='chk-1',
        lane_id='ORACLE_EVENT_LOG',
        view_label='weekly',
        source_event_log_path='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl',
        execution_authority='ADVISORY_ONLY',
        derived_classification='STABLE_BASELINE',
        window_entry_count=1,
        window_start_sequence_number=1,
        window_end_sequence_number=1,
        last_entry_hash='a' * 64,
        latest_event_id='evt-1',
        integrity_status='VERIFIED',
        subjects=[],
        missing_artifact_paths=[],
        summary_line='checkpoint stable',
    )
    verification = OracleEventCheckpointVerification(
        verified_at_utc=_NOW,
        manifest_path=str(manifest_path),
        status='VERIFIED',
        artifact_digests_verified=True,
        signature_verified=False,
        verified_subject_count=1,
        digest_mismatches=[],
        missing_artifact_paths=[],
        notes=[],
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding='utf-8')
    verification_path.write_text(verification.model_dump_json(indent=2), encoding='utf-8')
    rc = main([
        'oracle-explain',
        '--manifest', str(manifest_path),
        '--verification', str(verification_path),
        '--output', str(explanation_path),
    ])
    assert rc == 0
    payload = json.loads(explanation_path.read_text(encoding='utf-8'))
    assert payload['explanation_kind'] == 'event_checkpoint'
    assert payload['trust_status'] == 'TRUST_RESTRICTED'


@pytest.mark.constitutional
def test_explain_lineage_verification_tracks_missing_layers() -> None:
    explanation = explain_lineage_verification(_lineage(seal_status='CONSTITUTIONALLY_REPLAYABLE'))
    assert explanation.trust_status == 'TRUST_RESTRICTED'
    assert any(node.conclusion == 'MISSING_REQUIRED_LAYERS' for node in explanation.nodes)


@pytest.mark.constitutional
def test_explain_lineage_verification_surfaces_preferred_strategic_backing_source() -> None:
    verification = _lineage()
    verification = verification.model_copy(update={
        'preferred_strategic_backing_source': 'constitutional_lane',
        'preferred_strategic_backing_classification': 'SEALED_STRATEGIC_STACK_BACKED',
        'strategic_stack_evidence_count': 2,
        'strategic_stack_requirement_met': True,
    })
    explanation = explain_lineage_verification(verification)
    assert explanation.preferred_strategic_backing_source == 'constitutional_lane'
    assert explanation.preferred_strategic_backing_classification == 'SEALED_STRATEGIC_STACK_BACKED'
    assert any(
        node.conclusion == 'STRATEGIC_BACKING_SOURCE' and 'preferred_strategic_backing_source=constitutional_lane' in node.facts
        for node in explanation.nodes
    )
