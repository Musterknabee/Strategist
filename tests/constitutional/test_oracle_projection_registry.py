from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.projections.briefing_pack import build_briefing_pack_projection_registry
from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.operational import (
    ControlledRolloutBundle,
    DailyOperationsChecklist,
    KeyedHostFingerprint,
    RolloutScope,
    RuntimeEvidenceReview,
)
from strategy_validator.contracts.oracle import OracleConstitutionalGateReport, OracleDerivedViewReport
from strategy_validator.validator.rollout_ops import build_closure_snapshot, generate_snapshot_signing_keypair

_NOW = datetime(2026, 4, 14, 9, 0, tzinfo=timezone.utc)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        data = payload.model_dump(mode="json")
    else:
        data = payload
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def test_build_briefing_pack_projection_registry_records_sources_and_outputs(tmp_path: Path) -> None:
    repo_root = tmp_path
    source_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_DERIVED_VIEW.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('{"schema_version":"oracle_derived_view_report/v1","ok":true}\n', encoding='utf-8')
    output_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_BRIEFING_PACK_REPORT.json"
    output_path.write_text('{"schema_version":"oracle_briefing_pack_report/v1"}\n', encoding='utf-8')

    registry = build_briefing_pack_projection_registry(
        repo_root=repo_root,
        generated_at_utc=_NOW,
        source_paths={"derived_view": source_path},
        source_payloads={"derived_view": {"schema_version": "oracle_derived_view_report/v1"}},
        output_paths=[output_path],
    )

    assert registry["schema_version"] == "oracle_projection_artifact_registry/v1"
    assert registry["projection_label"] == "oracle_briefing_pack"
    assert registry["source_artifact_count"] == 1
    assert registry["output_artifact_count"] == 1
    assert registry["source_artifacts"][0]["artifact_label"] == "derived_view"
    assert registry["source_artifacts"][0]["schema_version"] == "oracle_derived_view_report/v1"
    assert registry["output_artifacts"][0]["artifact_label"] == "output:ORACLE_BRIEFING_PACK_REPORT.json"
    assert len(registry["projection_digest_sha256"]) == 64


def test_oracle_briefing_pack_cli_emits_projection_registry_sidecar(tmp_path: Path) -> None:
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
    registry_path = briefing_json.with_suffix('.projection.registry.json')
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    assert registry['schema_version'] == 'oracle_projection_artifact_registry/v1'
    assert registry['projection_label'] == 'oracle_briefing_pack'
    labels = {item['artifact_label'] for item in registry['source_artifacts']}
    assert {'derived_view', 'constitutional_gate', 'closure_snapshot', 'closure_dsse'} <= labels
    output_labels = {item['artifact_label'] for item in registry['output_artifacts']}
    assert 'output:ORACLE_BRIEFING_PACK_REPORT.json' in output_labels
    assert 'output:ORACLE_BRIEFING_PACK_REPORT.md' in output_labels
    assert 'output:ORACLE_BRIEFING_PACK_REPORT.html' in output_labels
    assert len(registry['projection_digest_sha256']) == 64



def test_build_oracle_event_view_projection_registry_records_event_log_source_and_outputs(tmp_path: Path) -> None:
    from strategy_validator.projections.oracle_event_views import build_oracle_event_view_projection_registry

    repo_root = tmp_path
    log_path = repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text('{"schema_version":"oracle_event_log_entry/v1","entry_id":"evidence-1:1"}\n', encoding='utf-8')
    output_path = log_path.with_name('ORACLE_HORIZON_WEEKLY.json')
    output_path.write_text('{"schema_version":"oracle_derived_view_report/v1"}\n', encoding='utf-8')

    registry = build_oracle_event_view_projection_registry(
        projection_label='oracle_horizon_view',
        projection_version='oracle_derived_view_report/v1',
        lane_path=log_path,
        report_payload={"schema_version": "oracle_derived_view_report/v1"},
        output_paths=[output_path],
        repo_root=repo_root,
        generated_at_utc=_NOW,
    )

    assert registry['projection_label'] == 'oracle_horizon_view'
    assert registry['projection_family'] == 'canonical_event_projection'
    assert registry['source_artifacts'][0]['artifact_label'] == 'oracle_event_log'
    assert registry['source_artifacts'][0]['path'] == 'docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl'
    assert registry['output_artifacts'][0]['artifact_label'] == 'output:ORACLE_HORIZON_WEEKLY.json'


def test_oracle_horizon_and_rolling_cli_emit_projection_registry_sidecars(tmp_path: Path) -> None:
    repo_root = tmp_path
    log_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_EVENT_LOG.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps({
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-14T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 1,
            'entry_id': 'evidence-1:1',
            'evidence_id': 'evidence-1',
            'previous_entry_hash': None,
            'entry_hash': '9' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_1.json',
            'manifest_sha256': 'a' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-14T08:10:00Z',
            'dominant_regime': 'TRANSITION',
            'recommended_global_action': 'CANARY_REVIEW',
            'epistemic_status': 'ELEVATED',
            'average_posterior_edge_confidence': 0.58,
            'maintain_count': 0,
            'canary_count': 1,
            'hibernate_count': 0,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'watch entry',
        }) + '\n',
        encoding='utf-8',
    )

    horizon_json = log_path.with_name('ORACLE_HORIZON_WEEKLY.json')
    horizon_md = log_path.with_name('ORACLE_HORIZON_WEEKLY.md')
    rc = main([
        'oracle-horizon-view',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--output', str(horizon_json),
        '--markdown-output', str(horizon_md),
    ])
    assert rc == 0
    horizon_registry = json.loads(horizon_json.with_suffix('.projection.registry.json').read_text(encoding='utf-8'))
    assert horizon_registry['projection_label'] == 'oracle_horizon_view'
    assert horizon_registry['source_artifacts'][0]['artifact_label'] == 'oracle_event_log'
    assert any(item['artifact_label'] == 'output:ORACLE_HORIZON_WEEKLY.json' for item in horizon_registry['output_artifacts'])

    review_json = log_path.with_name('ORACLE_ROLLING_REVIEW.json')
    review_md = log_path.with_name('ORACLE_ROLLING_REVIEW.md')
    rc = main([
        'oracle-rolling-review',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--output', str(review_json),
        '--markdown-output', str(review_md),
    ])
    assert rc == 0
    review_registry = json.loads(review_json.with_suffix('.projection.registry.json').read_text(encoding='utf-8'))
    assert review_registry['projection_label'] == 'oracle_rolling_review'
    assert review_registry['source_artifacts'][0]['artifact_label'] == 'oracle_event_log'
    assert any(item['artifact_label'] == 'output:ORACLE_ROLLING_REVIEW.json' for item in review_registry['output_artifacts'])
