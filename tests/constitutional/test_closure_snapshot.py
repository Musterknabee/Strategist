from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.operational import (
    ControlledRolloutBundle,
    DailyOperationsChecklist,
    KeyedHostFingerprint,
    RolloutScope,
    RuntimeEvidenceReview,
)
from strategy_validator.validator.rollout_ops import (
    build_closure_release_attestation,
    build_closure_snapshot,
    build_governed_exception_memo,
    build_rollout_bundle,
    generate_host_fingerprint,
    generate_snapshot_signing_keypair,
    render_final_release_signoff_markdown,
    render_governed_exception_markdown,
    review_runtime_evidence,
    verify_closure_snapshot,
    verify_governed_exception_memo,
)


@pytest.mark.constitutional
def test_rollout_bundle_rejects_missing_burnin_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    fingerprint_path = tmp_path / "fingerprint.json"
    fingerprint_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")

    with pytest.raises(FileNotFoundError):
        build_rollout_bundle(
            policy_path=policy,
            keyed_host_fingerprint_path=fingerprint_path,
            burnin_artifact_paths=[tmp_path / "missing.jsonl"],
            scope=RolloutScope(
                environment="paper",
                provider="alpaca_data_v2",
                symbols=["SPY"],
                allowed_actions=["observe"],
                operator_signoff_required=True,
            ),
        )


@pytest.mark.constitutional
def test_closure_snapshot_signed_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    closure_dir = repo_root / "docs" / "artifacts" / "closure_a"
    closure_dir.mkdir(parents=True)
    burnin_path = repo_root / "pilot_followup_alpaca_long.jsonl"
    burnin_path.write_text('{"round":1}\n', encoding="utf-8")
    policy = repo_root / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("APCA_API_KEY_ID", "abc")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "xyz")

    fingerprint = generate_host_fingerprint(
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-1",
        policy_path=policy,
        now_utc=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc),
    )
    fingerprint_path = closure_dir / "KEYED_HOST_FINGERPRINT.json"
    fingerprint_path.write_text(json.dumps(fingerprint.model_dump(mode="json"), indent=2), encoding="utf-8")

    bundle = build_rollout_bundle(
        policy_path=policy,
        keyed_host_fingerprint_path=fingerprint_path,
        burnin_artifact_paths=[burnin_path],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["SPY"],
            allowed_actions=["observe", "archive", "recommend"],
            operator_signoff_required=True,
        ),
        now_utc=datetime(2026, 4, 13, 8, 1, tzinfo=timezone.utc),
    )
    (closure_dir / "ROLLOUT_BUNDLE.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2), encoding="utf-8")

    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 8, 2, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=True,
        freshness_anomaly_count=0,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=False,
        policy_change_reasons=[],
    )
    (closure_dir / "DAILY_CHECKLIST.json").write_text(json.dumps(checklist.model_dump(mode="json"), indent=2), encoding="utf-8")

    review = RuntimeEvidenceReview(
        generated_at_utc=datetime(2026, 4, 13, 8, 3, tzinfo=timezone.utc),
        decision="KEEP_CURRENT_RELEASE",
        reasons=["Controlled rollout evidence remains within keep-current-release bounds."],
        observe_only_flags=[],
        must_fix_flags=[],
    )
    (closure_dir / "RUNTIME_REVIEW.json").write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")

    private_key = repo_root / "keys" / "closure_snapshot_private.pem"
    public_key = repo_root / "keys" / "closure_snapshot_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_dir,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    assert envelope is not None
    snapshot_path = closure_dir / "CLOSURE_SNAPSHOT.json"
    dsse_path = closure_dir / "CLOSURE_SNAPSHOT.dsse.json"
    snapshot_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    verification = verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )

    assert verification.status == "VERIFIED"
    assert verification.artifact_digests_verified is True
    assert verification.signature_verified is True
    assert verification.verified_subject_count == len(manifest.subjects)


@pytest.mark.constitutional
def test_closure_snapshot_allow_incomplete_surfaces_missing_paths(tmp_path: Path) -> None:
    repo_root = tmp_path
    closure_dir = repo_root / "docs" / "artifacts" / "closure_b"
    closure_dir.mkdir(parents=True)

    fingerprint = KeyedHostFingerprint(
        generated_at_utc=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc),
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-2",
        interface_freeze_id="0.1.0rc1",
        runtime_mode="DEV",
        config_fingerprint="cfg-1234",
        policy_sha256="a" * 64,
        git_commit="abc123",
        git_tag=None,
        env_presence={"APCA_API_KEY_ID": True},
        env_value_sha256={"APCA_API_KEY_ID": "b" * 64},
    )
    (closure_dir / "KEYED_HOST_FINGERPRINT.json").write_text(json.dumps(fingerprint.model_dump(mode="json"), indent=2), encoding="utf-8")

    bundle = ControlledRolloutBundle(
        generated_at_utc=datetime(2026, 4, 13, 8, 1, tzinfo=timezone.utc),
        runtime_mode="DEV",
        config_fingerprint="cfg-1234",
        policy_sha256="a" * 64,
        interface_freeze_id="0.1.0rc1",
        release_commit="abc123",
        release_tag=None,
        provider_source_policy_summary="allow_snapshot=True",
        keyed_host_fingerprint_path="docs/artifacts/closure_b/KEYED_HOST_FINGERPRINT.json",
        burnin_artifact_paths=["missing_followup.jsonl"],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["QQQ"],
            allowed_actions=["observe"],
            operator_signoff_required=True,
        ),
    )
    (closure_dir / "ROLLOUT_BUNDLE.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2), encoding="utf-8")

    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 8, 2, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=False,
        freshness_anomaly_count=60,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=["freshness_anomaly_threshold_crossed"],
    )
    (closure_dir / "DAILY_CHECKLIST.json").write_text(json.dumps(checklist.model_dump(mode="json"), indent=2), encoding="utf-8")

    review = RuntimeEvidenceReview(
        generated_at_utc=datetime(2026, 4, 13, 8, 3, tzinfo=timezone.utc),
        decision="CANDIDATE_RC2",
        reasons=["Observed thresholds crossed; evidence supports policy adjustment discussion."],
        observe_only_flags=[],
        must_fix_flags=[],
    )
    (closure_dir / "RUNTIME_REVIEW.json").write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        build_closure_snapshot(closure_dir=closure_dir, repo_root=repo_root)

    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_dir,
        repo_root=repo_root,
        allow_incomplete=True,
    )
    assert envelope is None
    assert manifest.integrity_status == "INCOMPLETE"
    assert manifest.missing_artifact_paths == ["missing_followup.jsonl"]


@pytest.mark.constitutional
def test_review_classifies_environmental_nonconformance() -> None:
    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=True,
        freshness_anomaly_count=90,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=["freshness_anomaly_threshold_crossed"],
    )
    review = review_runtime_evidence(checklist=checklist, now_utc=datetime(2026, 4, 13, 9, 1, tzinfo=timezone.utc))
    assert review.decision == "CANDIDATE_RC2"
    assert review.primary_classification == "ENVIRONMENTAL_NONCONFORMANCE"
    assert review.signoff_status == "WITHHELD"
    assert review.governed_exception_eligible is True
    assert "freshness_nonconformance_without_runtime_failure" in review.governed_exception_codes
    assert "POLICY_MISMATCH" in review.secondary_classifications


@pytest.mark.constitutional
def test_closure_attestation_is_derived_from_verified_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    closure_dir = repo_root / "docs" / "artifacts" / "closure_c"
    closure_dir.mkdir(parents=True)
    burnin_path = repo_root / "pilot_followup_alpaca_long.jsonl"
    burnin_path.write_text('{"round":1}\n', encoding="utf-8")
    policy = repo_root / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("APCA_API_KEY_ID", "abc")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "xyz")

    fingerprint = generate_host_fingerprint(
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-3",
        policy_path=policy,
        now_utc=datetime(2026, 4, 13, 9, 2, tzinfo=timezone.utc),
    )
    fingerprint_path = closure_dir / "KEYED_HOST_FINGERPRINT.json"
    fingerprint_path.write_text(json.dumps(fingerprint.model_dump(mode="json"), indent=2), encoding="utf-8")

    bundle = build_rollout_bundle(
        policy_path=policy,
        keyed_host_fingerprint_path=fingerprint_path,
        burnin_artifact_paths=[burnin_path],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["QQQ"],
            allowed_actions=["observe", "archive", "recommend"],
            operator_signoff_required=True,
        ),
        now_utc=datetime(2026, 4, 13, 9, 3, tzinfo=timezone.utc),
    )
    (closure_dir / "ROLLOUT_BUNDLE.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2), encoding="utf-8")

    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 9, 4, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=True,
        freshness_anomaly_count=120,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=["freshness_anomaly_threshold_crossed"],
    )
    (closure_dir / "DAILY_CHECKLIST.json").write_text(json.dumps(checklist.model_dump(mode="json"), indent=2), encoding="utf-8")

    review = review_runtime_evidence(checklist=checklist, now_utc=datetime(2026, 4, 13, 9, 5, tzinfo=timezone.utc))
    (closure_dir / "RUNTIME_REVIEW.json").write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")

    private_key = repo_root / "keys" / "closure_snapshot_private.pem"
    public_key = repo_root / "keys" / "closure_snapshot_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_dir,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    assert envelope is not None
    snapshot_path = closure_dir / "CLOSURE_SNAPSHOT.json"
    dsse_path = closure_dir / "CLOSURE_SNAPSHOT.dsse.json"
    snapshot_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    verification = verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    attestation, verification = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        verification=verification,
        verification_path=closure_dir / "CLOSURE_SNAPSHOT.verification.json",
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    assert verification.status == "VERIFIED"
    assert attestation.primary_classification == "ENVIRONMENTAL_NONCONFORMANCE"
    assert attestation.governed_exception_eligible is True
    assert attestation.signoff_status == "WITHHELD"
    assert attestation.final_release_stance == "SIGNOFF_WITHHELD"
    rendered = render_final_release_signoff_markdown(
        manifest=manifest,
        verification=verification,
        attestation=attestation,
    )
    assert "Governed Exception Boundary" in rendered
    assert "environmental nonconformance" in rendered.lower()



@pytest.mark.constitutional
def test_signed_governed_exception_preserves_current_baseline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    closure_dir = repo_root / "docs" / "artifacts" / "closure_d"
    closure_dir.mkdir(parents=True)
    burnin_path = repo_root / "pilot_followup_alpaca_long.jsonl"
    burnin_path.write_text('{"round":1}\n', encoding="utf-8")
    policy = repo_root / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("APCA_API_KEY_ID", "abc")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "xyz")

    fingerprint = generate_host_fingerprint(
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-4",
        policy_path=policy,
        now_utc=datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc),
    )
    fingerprint_path = closure_dir / "KEYED_HOST_FINGERPRINT.json"
    fingerprint_path.write_text(json.dumps(fingerprint.model_dump(mode="json"), indent=2), encoding="utf-8")

    bundle = build_rollout_bundle(
        policy_path=policy,
        keyed_host_fingerprint_path=fingerprint_path,
        burnin_artifact_paths=[burnin_path],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["QQQ"],
            allowed_actions=["observe", "archive", "recommend"],
            operator_signoff_required=True,
        ),
        now_utc=datetime(2026, 4, 13, 10, 1, tzinfo=timezone.utc),
    )
    (closure_dir / "ROLLOUT_BUNDLE.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2), encoding="utf-8")

    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 10, 2, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=True,
        freshness_anomaly_count=120,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=["freshness_anomaly_threshold_crossed"],
    )
    (closure_dir / "DAILY_CHECKLIST.json").write_text(json.dumps(checklist.model_dump(mode="json"), indent=2), encoding="utf-8")

    review = review_runtime_evidence(checklist=checklist, now_utc=datetime(2026, 4, 13, 10, 3, tzinfo=timezone.utc))
    (closure_dir / "RUNTIME_REVIEW.json").write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")

    private_key = repo_root / "keys" / "closure_private.pem"
    public_key = repo_root / "keys" / "closure_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_dir,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    snapshot_path = closure_dir / "CLOSURE_SNAPSHOT.json"
    dsse_path = closure_dir / "CLOSURE_SNAPSHOT.dsse.json"
    snapshot_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    snapshot_verification = verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    verification_path = closure_dir / "CLOSURE_SNAPSHOT.verification.json"
    verification_path.write_text(json.dumps(snapshot_verification.model_dump(mode="json"), indent=2), encoding="utf-8")

    memo, memo_envelope = build_governed_exception_memo(
        snapshot_path=snapshot_path,
        verification_path=verification_path,
        exception_code="freshness_nonconformance_without_runtime_failure",
        requested_by="operator.jpk",
        approved_by="release.authority",
        valid_until_utc=datetime(2026, 4, 14, 10, 4, tzinfo=timezone.utc),
        rationale="Paper feed freshness is environmentally degraded while runtime health remains clean.",
        constraints=["Re-run burn-in before expiry."],
        repo_root=repo_root,
        signing_private_key_path=private_key,
        now_utc=datetime(2026, 4, 13, 10, 4, tzinfo=timezone.utc),
    )
    assert memo_envelope is not None
    memo_path = closure_dir / "GOVERNED_EXCEPTION_MEMO.json"
    memo_dsse_path = closure_dir / "GOVERNED_EXCEPTION_MEMO.dsse.json"
    memo_path.write_text(json.dumps(memo.model_dump(mode="json"), indent=2), encoding="utf-8")
    memo_dsse_path.write_text(json.dumps(memo_envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    memo_verification = verify_governed_exception_memo(
        memo_path=memo_path,
        repo_root=repo_root,
        dsse_path=memo_dsse_path,
        public_key_path=public_key,
        now_utc=datetime(2026, 4, 13, 10, 5, tzinfo=timezone.utc),
    )
    assert memo_verification.status == "VERIFIED"

    attestation, _ = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        verification=snapshot_verification,
        verification_path=verification_path,
        governed_exception_memo=memo,
        governed_exception_verification=memo_verification,
        now_utc=datetime(2026, 4, 13, 10, 5, tzinfo=timezone.utc),
    )
    assert attestation.signoff_status == "APPROVED"
    assert attestation.final_release_stance == "KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION"
    assert attestation.applied_governed_exception_code == "freshness_nonconformance_without_runtime_failure"
    rendered = render_governed_exception_markdown(memo=memo, verification=memo_verification)
    assert "Governed Exception Memo" in rendered
    signoff = render_final_release_signoff_markdown(manifest=manifest, verification=snapshot_verification, attestation=attestation)
    assert "Approved Governed Exception" in signoff


@pytest.mark.constitutional
def test_expired_governed_exception_does_not_approve_signoff(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    closure_dir = repo_root / "docs" / "artifacts" / "closure_e"
    closure_dir.mkdir(parents=True)
    burnin_path = repo_root / "pilot_followup_alpaca_long.jsonl"
    burnin_path.write_text('{"round":1}\n', encoding="utf-8")
    policy = repo_root / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("APCA_API_KEY_ID", "abc")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "xyz")

    fingerprint = generate_host_fingerprint(
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-5",
        policy_path=policy,
        now_utc=datetime(2026, 4, 13, 11, 0, tzinfo=timezone.utc),
    )
    fingerprint_path = closure_dir / "KEYED_HOST_FINGERPRINT.json"
    fingerprint_path.write_text(json.dumps(fingerprint.model_dump(mode="json"), indent=2), encoding="utf-8")

    bundle = build_rollout_bundle(
        policy_path=policy,
        keyed_host_fingerprint_path=fingerprint_path,
        burnin_artifact_paths=[burnin_path],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["SPY"],
            allowed_actions=["observe", "archive", "recommend"],
            operator_signoff_required=True,
        ),
        now_utc=datetime(2026, 4, 13, 11, 1, tzinfo=timezone.utc),
    )
    (closure_dir / "ROLLOUT_BUNDLE.json").write_text(json.dumps(bundle.model_dump(mode="json"), indent=2), encoding="utf-8")

    checklist = DailyOperationsChecklist(
        generated_at_utc=datetime(2026, 4, 13, 11, 2, tzinfo=timezone.utc),
        startup_check_passed=True,
        readiness_status="READY",
        provider_availability_ok=True,
        freshness_anomaly_count=120,
        fallback_count=0,
        circuit_open_count=0,
        auth_rate_limit_count=0,
        timeout_count=0,
        retry_count=0,
        telemetry_sink_healthy=True,
        policy_change_justified=True,
        policy_change_reasons=["freshness_anomaly_threshold_crossed"],
    )
    (closure_dir / "DAILY_CHECKLIST.json").write_text(json.dumps(checklist.model_dump(mode="json"), indent=2), encoding="utf-8")

    review = review_runtime_evidence(checklist=checklist, now_utc=datetime(2026, 4, 13, 11, 3, tzinfo=timezone.utc))
    (closure_dir / "RUNTIME_REVIEW.json").write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")

    private_key = repo_root / "keys" / "memo_private.pem"
    public_key = repo_root / "keys" / "memo_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_closure_snapshot(
        closure_dir=closure_dir,
        repo_root=repo_root,
        signing_private_key_path=private_key,
    )
    snapshot_path = closure_dir / "CLOSURE_SNAPSHOT.json"
    dsse_path = closure_dir / "CLOSURE_SNAPSHOT.dsse.json"
    snapshot_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    snapshot_verification = verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    verification_path = closure_dir / "CLOSURE_SNAPSHOT.verification.json"
    verification_path.write_text(json.dumps(snapshot_verification.model_dump(mode="json"), indent=2), encoding="utf-8")

    memo, memo_envelope = build_governed_exception_memo(
        snapshot_path=snapshot_path,
        verification_path=verification_path,
        exception_code="freshness_nonconformance_without_runtime_failure",
        requested_by="operator.jpk",
        approved_by="release.authority",
        valid_until_utc=datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc),
        rationale="Temporary environmental allowance.",
        repo_root=repo_root,
        signing_private_key_path=private_key,
        now_utc=datetime(2026, 4, 13, 11, 4, tzinfo=timezone.utc),
    )
    memo_path = closure_dir / "GOVERNED_EXCEPTION_MEMO.json"
    memo_dsse_path = closure_dir / "GOVERNED_EXCEPTION_MEMO.dsse.json"
    memo_path.write_text(json.dumps(memo.model_dump(mode="json"), indent=2), encoding="utf-8")
    memo_dsse_path.write_text(json.dumps(memo_envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    memo_verification = verify_governed_exception_memo(
        memo_path=memo_path,
        repo_root=repo_root,
        dsse_path=memo_dsse_path,
        public_key_path=public_key,
        now_utc=datetime(2026, 4, 13, 12, 1, tzinfo=timezone.utc),
    )
    assert memo_verification.status == "EXPIRED"

    attestation, _ = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        verification=snapshot_verification,
        verification_path=verification_path,
        governed_exception_memo=memo,
        governed_exception_verification=memo_verification,
        now_utc=datetime(2026, 4, 13, 12, 1, tzinfo=timezone.utc),
    )
    assert attestation.signoff_status == "WITHHELD"
    assert attestation.final_release_stance == "SIGNOFF_WITHHELD"
    assert attestation.applied_governed_exception_id is None
    assert any("expired" in reason.lower() for reason in attestation.reasons)
