from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.operational import (
    ControlledRolloutBundle,
    DailyOperationsChecklist,
    KeyedHostFingerprint,
    RolloutScope,
    RuntimeEvidenceReview,
)
from strategy_validator.contracts.oracle import (
    OracleConstitutionalGateReport,
    OracleDerivedViewReport,
)
from strategy_validator.validator.rollout_ops import (
    build_closure_snapshot,
    generate_snapshot_signing_keypair,
)


_NOW = datetime(2026, 4, 13, tzinfo=timezone.utc)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(mode="json")
    else:
        data = payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


@pytest.mark.constitutional
def test_oracle_diagnose_cli_explains_restricted_and_blocked_reports(tmp_path: Path) -> None:
    derived_report = OracleDerivedViewReport(
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
        latest_epistemic_status='ELEVATED',
        derived_classification='EVIDENCE_GAP',
        classification_counts={'EVIDENCE_GAP': 3},
        regime_counts={'RISK_ON_LOW_VOL': 3},
        global_action_counts={'OBSERVE': 3},
        epistemic_counts={'ELEVATED': 3},
        evidence_gap_count=2,
        elevated_or_unknown_count=2,
        defensive_posture_count=0,
        retrain_pressure_count=1,
        average_posterior_edge_confidence=0.31,
        observed_entry_ids=['evt-1', 'evt-2', 'evt-3'],
        operator_actions=['repair evidence gaps before relying on this view'],
        summary_line='Derived view has unresolved evidence gaps.',
    )
    derived_path = tmp_path / 'ORACLE_DERIVED_VIEW.json'
    _write_json(derived_path, derived_report)

    diagnostic_json = tmp_path / 'ORACLE_OPERATOR_DIAGNOSTIC_REPORT.json'
    diagnostic_md = tmp_path / 'ORACLE_OPERATOR_DIAGNOSTIC_REPORT.md'
    rc = main([
        'oracle-diagnose',
        '--report', str(derived_path),
        '--output', str(diagnostic_json),
        '--markdown-output', str(diagnostic_md),
    ])
    assert rc == 0
    diagnostic = json.loads(diagnostic_json.read_text(encoding='utf-8'))
    assert diagnostic['schema_version'] == 'oracle_operator_diagnostic_report/v1'
    assert diagnostic['diagnostic_kind'] == 'why_restricted'
    assert diagnostic['trust_status'] == 'UNTRUSTED'
    assert any('evidence gaps' in reason.lower() for reason in diagnostic['reasons'])
    assert 'Oracle Operator Diagnostic' in diagnostic_md.read_text(encoding='utf-8')

    gate_report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root='.',
        search_root='./docs/artifacts',
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='CONSTITUTIONALLY_REPLAYABLE',
        lineage_completeness_percent=82,
        constitutional_digest_classification='CONSTITUTIONAL_HEIGHTENED_WATCH',
        manifest_verification_status='VERIFIED',
        trust_status='TRUST_RESTRICTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status CONSTITUTIONALLY_REPLAYABLE is below required threshold FULLY_SEALED'],
        operator_actions=['repair doctrine coverage before constitutional use'],
        summary_line='Constitutional gate remains blocked pending seal repair.',
    )
    gate_path = tmp_path / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    _write_json(gate_path, gate_report)
    rc = main([
        'oracle-diagnose',
        '--report', str(gate_path),
        '--output', str(diagnostic_json),
    ])
    assert rc == 0
    diagnostic = json.loads(diagnostic_json.read_text(encoding='utf-8'))
    assert diagnostic['diagnostic_kind'] == 'why_blocked'
    assert diagnostic['blocked'] is True
    assert any('below required threshold' in reason for reason in diagnostic['reasons'])


@pytest.mark.constitutional
def test_oracle_status_pack_cli_summarizes_lineage_oracle_and_closure_state(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts_root / 'oracle'
    closure_root = artifacts_root / 'release_closure_2026-04-13'
    oracle_root.mkdir(parents=True)
    closure_root.mkdir(parents=True)

    derived_report = OracleDerivedViewReport(
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
        operator_actions=['maintain heightened watch while doctrine lineage is incomplete'],
        summary_line='Oracle posture is elevated but replayable.',
    )
    derived_path = oracle_root / 'ORACLE_DERIVED_VIEW.json'
    _write_json(derived_path, derived_report)

    gate_report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root=str(repo_root),
        search_root=str(artifacts_root),
        preferred_strategic_backing_source='constitutional_lane',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        exact_evidence_support_score=1.0,
        exact_feedback_confirmation_count=4,
        exact_feedback_relief_count=0,
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='ADVISORY_ONLY_INCOMPLETE',
        lineage_completeness_percent=40,
        constitutional_digest_classification='CONSTITUTIONAL_HEIGHTENED_WATCH',
        manifest_verification_status='UNVERIFIED',
        trust_status='UNTRUSTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status ADVISORY_ONLY_INCOMPLETE is below required threshold FULLY_SEALED'],
        operator_actions=['repair doctrine lineage before constitutional use'],
        summary_line='Constitutional gate is untrusted.',
    )
    gate_path = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    _write_json(gate_path, gate_report)

    fingerprint = KeyedHostFingerprint(
        generated_at_utc=_NOW,
        host_kind='KEYED_OPERATOR_HOST',
        host_label='ops-host-1',
        interface_freeze_id='0.1.0rc1',
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        git_commit='abc123',
        git_tag=None,
        env_presence={'APCA_API_KEY_ID': True},
        env_value_sha256={'APCA_API_KEY_ID': 'b' * 64},
    )
    _write_json(closure_root / 'KEYED_HOST_FINGERPRINT.json', fingerprint)

    bundle = ControlledRolloutBundle(
        generated_at_utc=_NOW,
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        interface_freeze_id='0.1.0rc1',
        release_commit='abc123',
        release_tag=None,
        provider_source_policy_summary='allow_snapshot=True',
        keyed_host_fingerprint_path='docs/artifacts/release_closure_2026-04-13/KEYED_HOST_FINGERPRINT.json',
        burnin_artifact_paths=['docs/artifacts/release_closure_2026-04-13/pilot_followup.jsonl'],
        scope=RolloutScope(
            environment='paper',
            provider='alpaca_data_v2',
            symbols=['SPY'],
            allowed_actions=['observe'],
            operator_signoff_required=True,
        ),
    )
    _write_json(closure_root / 'ROLLOUT_BUNDLE.json', bundle)
    (closure_root / 'pilot_followup.jsonl').write_text('{"round":1}\n', encoding='utf-8')

    checklist = DailyOperationsChecklist(
        generated_at_utc=_NOW,
        startup_check_passed=True,
        readiness_status='READY',
        provider_availability_ok=False,
        freshness_anomaly_count=60,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=['freshness_anomaly_threshold_crossed'],
    )
    _write_json(closure_root / 'DAILY_CHECKLIST.json', checklist)

    review = RuntimeEvidenceReview(
        generated_at_utc=_NOW,
        decision='CANDIDATE_RC2',
        reasons=['Observed thresholds crossed; evidence supports policy adjustment discussion.'],
        observe_only_flags=[],
        must_fix_flags=[],
        primary_classification='ENVIRONMENTAL_NONCONFORMANCE',
        secondary_classifications=['POLICY_MISMATCH'],
        governed_exception_codes=['freshness_nonconformance_without_runtime_failure'],
        signoff_status='WITHHELD',
    )
    _write_json(closure_root / 'RUNTIME_REVIEW.json', review)

    private_key = repo_root / 'keys' / 'closure_snapshot_private.pem'
    public_key = repo_root / 'keys' / 'closure_snapshot_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)
    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_root,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    snapshot_path = closure_root / 'CLOSURE_SNAPSHOT.json'
    dsse_path = closure_root / 'CLOSURE_SNAPSHOT.dsse.json'
    _write_json(snapshot_path, manifest)
    assert envelope is not None
    _write_json(dsse_path, envelope)

    status_json = oracle_root / 'ORACLE_STATUS_PACK_REPORT.json'
    status_md = oracle_root / 'ORACLE_STATUS_PACK_REPORT.md'
    status_root = oracle_root / 'status_pack'
    rc = main([
        'oracle-status-pack',
        '--repo-root', str(repo_root),
        '--derived-view-report', str(derived_path),
        '--constitutional-gate-report', str(gate_path),
        '--closure-snapshot', str(snapshot_path),
        '--closure-dsse', str(dsse_path),
        '--closure-public-key', str(public_key),
        '--pack-root', str(status_root),
        '--output', str(status_json),
        '--markdown-output', str(status_md),
    ])
    assert rc == 0
    pack = json.loads(status_json.read_text(encoding='utf-8'))
    assert pack['schema_version'] == 'oracle_status_pack_report/v1'
    assert pack['trust_status'] == 'UNTRUSTED'
    assert len(pack['provenance_digest_sha256']) == 64
    assert pack['exact_cadence_signal_classification'] == 'EXACT_CONFIRMED_PRESSURE'
    assert pack['exact_feedback_confirmation_count'] == 4
    assert 'repeated exact sealed confirmations (4)' in pack['summary_line']
    section_ids = {section['section_id'] for section in pack['sections']}
    assert {'lineage', 'oracle_posture', 'constitutional_gate', 'closure_attestation'} <= section_ids
    closure_section = next(section for section in pack['sections'] if section['section_id'] == 'closure_attestation')
    assert closure_section['status'] == 'WITHHELD'
    assert 'Oracle Status Pack' in status_md.read_text(encoding='utf-8')
    assert (status_root / 'ORACLE_STATUS_PACK_REPORT.json').exists()
    assert (status_root / 'ORACLE_STATUS_PACK_REPORT.md').exists()


@pytest.mark.constitutional
def test_oracle_incident_pack_cli_materializes_bundle_with_artifact_copies(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts_root / 'oracle'
    closure_root = artifacts_root / 'release_closure_2026-04-13'
    oracle_root.mkdir(parents=True)
    closure_root.mkdir(parents=True)

    derived_report = OracleDerivedViewReport(
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
        operator_actions=['maintain heightened watch while doctrine lineage is incomplete'],
        summary_line='Oracle posture is elevated but replayable.',
    )
    derived_path = oracle_root / 'ORACLE_DERIVED_VIEW.json'
    _write_json(derived_path, derived_report)

    gate_report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root=str(repo_root),
        search_root=str(artifacts_root),
        preferred_strategic_backing_source='constitutional_lane',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        exact_evidence_support_score=1.0,
        exact_feedback_confirmation_count=4,
        exact_feedback_relief_count=0,
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='CONSTITUTIONALLY_REPLAYABLE',
        lineage_completeness_percent=82,
        constitutional_digest_classification='CONSTITUTIONAL_HEIGHTENED_WATCH',
        manifest_verification_status='VERIFIED',
        trust_status='TRUST_RESTRICTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status CONSTITUTIONALLY_REPLAYABLE is below required threshold FULLY_SEALED'],
        operator_actions=['repair doctrine coverage before constitutional use'],
        summary_line='Constitutional gate remains blocked pending seal repair.',
    )
    gate_path = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    _write_json(gate_path, gate_report)

    private_key = repo_root / 'keys' / 'closure_snapshot_private.pem'
    public_key = repo_root / 'keys' / 'closure_snapshot_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    fingerprint = KeyedHostFingerprint(
        generated_at_utc=_NOW,
        host_kind='KEYED_OPERATOR_HOST',
        host_label='ops-host-1',
        interface_freeze_id='0.1.0rc1',
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        git_commit='abc123',
        git_tag=None,
        env_presence={'APCA_API_KEY_ID': True},
        env_value_sha256={'APCA_API_KEY_ID': 'b' * 64},
    )
    _write_json(closure_root / 'KEYED_HOST_FINGERPRINT.json', fingerprint)
    bundle = ControlledRolloutBundle(
        generated_at_utc=_NOW,
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        interface_freeze_id='0.1.0rc1',
        release_commit='abc123',
        release_tag=None,
        provider_source_policy_summary='allow_snapshot=True',
        keyed_host_fingerprint_path='docs/artifacts/release_closure_2026-04-13/KEYED_HOST_FINGERPRINT.json',
        burnin_artifact_paths=['docs/artifacts/release_closure_2026-04-13/pilot_followup.jsonl'],
        scope=RolloutScope(
            environment='paper',
            provider='alpaca_data_v2',
            symbols=['SPY'],
            allowed_actions=['observe'],
            operator_signoff_required=True,
        ),
    )
    _write_json(closure_root / 'ROLLOUT_BUNDLE.json', bundle)
    (closure_root / 'pilot_followup.jsonl').write_text('{"round":1}\n', encoding='utf-8')
    checklist = DailyOperationsChecklist(
        generated_at_utc=_NOW,
        startup_check_passed=True,
        readiness_status='READY',
        provider_availability_ok=False,
        freshness_anomaly_count=60,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=['freshness_anomaly_threshold_crossed'],
    )
    _write_json(closure_root / 'DAILY_CHECKLIST.json', checklist)
    review = RuntimeEvidenceReview(
        generated_at_utc=_NOW,
        decision='CANDIDATE_RC2',
        reasons=['Observed thresholds crossed; evidence supports policy adjustment discussion.'],
        observe_only_flags=[],
        must_fix_flags=[],
        primary_classification='ENVIRONMENTAL_NONCONFORMANCE',
        secondary_classifications=['POLICY_MISMATCH'],
        governed_exception_codes=['freshness_nonconformance_without_runtime_failure'],
        signoff_status='WITHHELD',
    )
    _write_json(closure_root / 'RUNTIME_REVIEW.json', review)
    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_root,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    snapshot_path = closure_root / 'CLOSURE_SNAPSHOT.json'
    dsse_path = closure_root / 'CLOSURE_SNAPSHOT.dsse.json'
    _write_json(snapshot_path, manifest)
    assert envelope is not None
    _write_json(dsse_path, envelope)

    incident_json = oracle_root / 'ORACLE_INCIDENT_PACK_REPORT.json'
    incident_md = oracle_root / 'ORACLE_INCIDENT_PACK_REPORT.md'
    incident_root = oracle_root / 'incident_pack'
    rc = main([
        'oracle-incident-pack',
        '--repo-root', str(repo_root),
        '--derived-view-report', str(derived_path),
        '--constitutional-gate-report', str(gate_path),
        '--closure-snapshot', str(snapshot_path),
        '--closure-dsse', str(dsse_path),
        '--closure-public-key', str(public_key),
        '--pack-root', str(incident_root),
        '--output', str(incident_json),
        '--markdown-output', str(incident_md),
    ])
    assert rc == 0
    pack = json.loads(incident_json.read_text(encoding='utf-8'))
    assert pack['schema_version'] == 'oracle_incident_pack_report/v1'
    assert pack['incident_kind'] == 'blocked'
    assert pack['blocked'] is True
    assert len(pack['provenance_digest_sha256']) == 64
    assert pack['primary_diagnostic']['diagnostic_kind'] == 'why_blocked'
    assert pack['exact_cadence_signal_classification'] == 'EXACT_CONFIRMED_PRESSURE'
    assert pack['exact_feedback_confirmation_count'] == 4
    assert 'repeated exact sealed confirmations (4)' in pack['summary_line']
    assert any(artifact['pack_path'] for artifact in pack['artifacts'])
    assert (incident_root / 'ORACLE_INCIDENT_PACK_REPORT.json').exists()
    assert (incident_root / 'ORACLE_INCIDENT_PACK_REPORT.md').exists()
    copied = [incident_root / artifact['pack_path'] for artifact in pack['artifacts'] if artifact['pack_path']]
    assert copied and all(path.exists() for path in copied)
    assert 'Oracle Incident Pack' in incident_md.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_briefing_pack_cli_emits_json_markdown_and_html(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts_root / 'oracle'
    closure_root = artifacts_root / 'release_closure_2026-04-13'
    oracle_root.mkdir(parents=True)
    closure_root.mkdir(parents=True)

    derived_report = OracleDerivedViewReport(
        generated_at_utc=_NOW,
        lane_id='ORACLE_EVENT_LOG',
        view_label='weekly',
        window_entry_count=3,
        window_start_sequence_number=1,
        window_end_sequence_number=3,
        first_input_timestamp_utc=_NOW,
        last_input_timestamp_utc=_NOW,
        latest_event_id='evt-3',
        latest_dominant_regime='TRANSITION',
        latest_global_action='CANARY_REVIEW',
        latest_epistemic_status='ELEVATED',
        derived_classification='HEIGHTENED_WATCH',
        classification_counts={'HEIGHTENED_WATCH': 3},
        regime_counts={'TRANSITION': 3},
        global_action_counts={'CANARY_REVIEW': 3},
        epistemic_counts={'ELEVATED': 3},
        evidence_gap_count=0,
        elevated_or_unknown_count=3,
        defensive_posture_count=0,
        retrain_pressure_count=1,
        average_posterior_edge_confidence=0.57,
        observed_entry_ids=['evt-1', 'evt-2', 'evt-3'],
        operator_actions=['maintain heightened watch while doctrine lineage remains replayable'],
        summary_line='Oracle posture is elevated but replayable.',
    )
    derived_path = oracle_root / 'ORACLE_DERIVED_VIEW.json'
    _write_json(derived_path, derived_report)

    gate_report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root=str(repo_root),
        search_root=str(artifacts_root),
        preferred_strategic_backing_source='constitutional_lane',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        exact_evidence_support_score=1.0,
        exact_feedback_confirmation_count=4,
        exact_feedback_relief_count=0,
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='CONSTITUTIONALLY_REPLAYABLE',
        lineage_completeness_percent=82,
        constitutional_digest_classification='CONSTITUTIONAL_HEIGHTENED_WATCH',
        manifest_verification_status='VERIFIED',
        trust_status='TRUST_RESTRICTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status CONSTITUTIONALLY_REPLAYABLE is below required threshold FULLY_SEALED'],
        operator_actions=['repair doctrine coverage before constitutional use'],
        summary_line='Constitutional gate remains blocked pending seal repair.',
    )
    gate_path = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    _write_json(gate_path, gate_report)

    private_key = repo_root / 'keys' / 'closure_snapshot_private.pem'
    public_key = repo_root / 'keys' / 'closure_snapshot_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    fingerprint = KeyedHostFingerprint(
        generated_at_utc=_NOW,
        host_kind='KEYED_OPERATOR_HOST',
        host_label='ops-host-1',
        interface_freeze_id='0.1.0rc1',
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        git_commit='abc123',
        git_tag=None,
        env_presence={'APCA_API_KEY_ID': True},
        env_value_sha256={'APCA_API_KEY_ID': 'b' * 64},
    )
    _write_json(closure_root / 'KEYED_HOST_FINGERPRINT.json', fingerprint)
    bundle = ControlledRolloutBundle(
        generated_at_utc=_NOW,
        runtime_mode='DEV',
        config_fingerprint='cfg-1234',
        policy_sha256='a' * 64,
        interface_freeze_id='0.1.0rc1',
        release_commit='abc123',
        release_tag=None,
        provider_source_policy_summary='allow_snapshot=True',
        keyed_host_fingerprint_path='docs/artifacts/release_closure_2026-04-13/KEYED_HOST_FINGERPRINT.json',
        burnin_artifact_paths=['docs/artifacts/release_closure_2026-04-13/pilot_followup.jsonl'],
        scope=RolloutScope(
            environment='paper',
            provider='alpaca_data_v2',
            symbols=['SPY'],
            allowed_actions=['observe'],
            operator_signoff_required=True,
        ),
    )
    _write_json(closure_root / 'ROLLOUT_BUNDLE.json', bundle)
    (closure_root / 'pilot_followup.jsonl').write_text('{"round":1}\n', encoding='utf-8')
    checklist = DailyOperationsChecklist(
        generated_at_utc=_NOW,
        startup_check_passed=True,
        readiness_status='READY',
        provider_availability_ok=False,
        freshness_anomaly_count=60,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=['freshness_anomaly_threshold_crossed'],
    )
    _write_json(closure_root / 'DAILY_CHECKLIST.json', checklist)
    review = RuntimeEvidenceReview(
        generated_at_utc=_NOW,
        decision='CANDIDATE_RC2',
        reasons=['Observed thresholds crossed; evidence supports policy adjustment discussion.'],
        observe_only_flags=[],
        must_fix_flags=[],
        primary_classification='ENVIRONMENTAL_NONCONFORMANCE',
        secondary_classifications=['POLICY_MISMATCH'],
        governed_exception_codes=['freshness_nonconformance_without_runtime_failure'],
        signoff_status='WITHHELD',
    )
    _write_json(closure_root / 'RUNTIME_REVIEW.json', review)
    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_root,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    snapshot_path = closure_root / 'CLOSURE_SNAPSHOT.json'
    dsse_path = closure_root / 'CLOSURE_SNAPSHOT.dsse.json'
    _write_json(snapshot_path, manifest)
    assert envelope is not None
    _write_json(dsse_path, envelope)

    briefing_json = oracle_root / 'ORACLE_BRIEFING_PACK_REPORT.json'
    briefing_md = oracle_root / 'ORACLE_BRIEFING_PACK_REPORT.md'
    briefing_html = oracle_root / 'ORACLE_BRIEFING_PACK_REPORT.html'
    briefing_root = oracle_root / 'briefing_pack'
    rc = main([
        'oracle-briefing-pack',
        '--repo-root', str(repo_root),
        '--derived-view-report', str(derived_path),
        '--constitutional-gate-report', str(gate_path),
        '--closure-snapshot', str(snapshot_path),
        '--closure-dsse', str(dsse_path),
        '--closure-public-key', str(public_key),
        '--pack-root', str(briefing_root),
        '--output', str(briefing_json),
        '--markdown-output', str(briefing_md),
        '--html-output', str(briefing_html),
    ])
    assert rc == 0
    report = json.loads(briefing_json.read_text(encoding='utf-8'))
    assert report['schema_version'] == 'oracle_briefing_pack_report/v1'
    assert report['trust_status'] in {'TRUST_RESTRICTED', 'UNTRUSTED'}
    assert report['preferred_strategic_backing_source'] == 'constitutional_lane'
    assert report['preferred_strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert report['exact_cadence_signal_classification'] == 'EXACT_CONFIRMED_PRESSURE'
    assert report['exact_feedback_confirmation_count'] == 4
    assert len(report['provenance_digest_sha256']) == 64
    assert len(report['status_pack_digest_sha256']) == 64
    assert len(report['incident_pack_digest_sha256']) == 64
    section_ids = {section['section_id'] for section in report['sections']}
    assert {'trust_banner', 'regime_state', 'strategy_health', 'doctrine_posture', 'closure_posture', 'open_risks', 'active_exceptions'} <= section_ids
    trust_banner = next(section for section in report['sections'] if section['section_id'] == 'trust_banner')
    assert trust_banner['preferred_strategic_backing_source'] == 'constitutional_lane'
    assert trust_banner['preferred_strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert trust_banner['exact_cadence_signal_classification'] == 'EXACT_CONFIRMED_PRESSURE'
    assert trust_banner['exact_feedback_confirmation_count'] == 4
    briefing_markdown = briefing_md.read_text(encoding='utf-8')
    assert 'Oracle Briefing Pack' in briefing_markdown
    assert 'Preferred strategic backing source' in briefing_markdown
    assert 'Exact cadence signal' in briefing_markdown
    assert 'Exact feedback confirmations: `4`' in briefing_markdown
    html = briefing_html.read_text(encoding='utf-8')
    assert '<html>' in html
    assert 'Trust Banner' in html
    assert 'constitutional_lane' in html
    assert report['status_pack_digest_sha256'] in html


@pytest.mark.constitutional
def test_oracle_diagnostic_surfaces_preferred_strategic_backing_source(tmp_path: Path) -> None:
    gate_report = OracleConstitutionalGateReport(
        generated_at_utc=_NOW,
        repo_root='.',
        search_root='./docs/artifacts',
        preferred_strategic_backing_source='constitutional_lane',
        preferred_strategic_backing_classification='SEALED_STRATEGIC_STACK_BACKED',
        exact_evidence_support_score=1.0,
        exact_feedback_confirmation_count=4,
        exact_feedback_relief_count=0,
        manifest_path='docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        minimum_required_seal_status='FULLY_SEALED',
        lineage_seal_status='CONSTITUTIONALLY_REPLAYABLE',
        lineage_completeness_percent=82,
        constitutional_digest_classification='CONSTITUTIONAL_HEIGHTENED_WATCH',
        manifest_verification_status='VERIFIED',
        trust_status='TRUST_RESTRICTED',
        trusted_for_constitutional_use=False,
        blocking_reasons=['lineage seal status CONSTITUTIONALLY_REPLAYABLE is below required threshold FULLY_SEALED'],
        operator_actions=['repair doctrine coverage before constitutional use'],
        summary_line='Constitutional gate remains blocked pending seal repair.',
    )
    gate_path = tmp_path / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    _write_json(gate_path, gate_report)
    diagnostic_json = tmp_path / 'ORACLE_OPERATOR_DIAGNOSTIC_REPORT.json'
    rc = main([
        'oracle-diagnose',
        '--report', str(gate_path),
        '--output', str(diagnostic_json),
    ])
    assert rc == 0
    diagnostic = json.loads(diagnostic_json.read_text(encoding='utf-8'))
    assert diagnostic['preferred_strategic_backing_source'] == 'constitutional_lane'
    assert diagnostic['preferred_strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert diagnostic['explanation']['preferred_strategic_backing_source'] == 'constitutional_lane'
