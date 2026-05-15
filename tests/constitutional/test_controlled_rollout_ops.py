from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.validator.rollout_ops import (
    build_daily_checklist,
    build_rollout_bundle,
    generate_host_fingerprint,
    review_runtime_evidence,
)
from strategy_validator.contracts.operational import RolloutScope


@pytest.mark.constitutional
def test_keyed_host_fingerprint_secret_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    monkeypatch.setenv("APCA_API_KEY_ID", "abc")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "xyz")

    fp = generate_host_fingerprint(
        host_kind="KEYED_OPERATOR_HOST",
        host_label="ops-host-1",
        policy_path=policy,
        now_utc=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc),
    )

    assert fp.host_kind == "KEYED_OPERATOR_HOST"
    assert fp.env_presence["APCA_API_KEY_ID"] is True
    assert fp.env_presence["APCA_API_SECRET_KEY"] is True
    payload = fp.model_dump(mode="json")
    secret_scan = {key: value for key, value in payload.items() if key not in {"commit", "git_tag"}}
    secret_scan_text = json.dumps(secret_scan)
    assert "abc" not in secret_scan_text
    assert "xyz" not in secret_scan_text
    assert "APCA_API_KEY_ID" in fp.env_value_sha256


@pytest.mark.constitutional
def test_rollout_bundle_captures_frozen_fields(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text("runtime_policy:\n  strict_production_mode: false\n", encoding="utf-8")
    fp_file = tmp_path / "fingerprint.json"
    fp_file.write_text("{}", encoding="utf-8")
    a1 = tmp_path / "a1.jsonl"
    a1.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")

    bundle = build_rollout_bundle(
        policy_path=policy,
        keyed_host_fingerprint_path=fp_file,
        burnin_artifact_paths=[a1],
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["SPY", "QQQ"],
            allowed_actions=["observe", "archive", "recommend"],
            operator_signoff_required=True,
        ),
        now_utc=datetime(2026, 4, 13, 8, 1, tzinfo=timezone.utc),
    )

    assert bundle.interface_freeze_id == "0.1.0rc1"
    assert bundle.keyed_host_fingerprint_path.endswith("fingerprint.json")
    assert bundle.scope.operator_signoff_required is True
    assert len(bundle.policy_sha256) == 64


@pytest.mark.constitutional
def test_daily_checklist_deterministic_and_no_policy_drift() -> None:
    now = datetime(2026, 4, 13, 8, 2, tzinfo=timezone.utc)
    summary = {
        "rounds": 60,
        "provider_status_counts": {"SUCCESS": 58, "STALE": 2},
        "effective_freshness_counts": {"FRESH": 58, "STALE": 2},
        "fallback_applied_rounds": 1,
        "timeout_signal_rounds": 0,
        "failure_domain_counts": {"NONE": 60},
        "rate_limit_proxy_rounds": 0,
    }
    c1 = build_daily_checklist(
        analyze_summaries=[summary],
        startup_json={"readiness": {"status": "READY"}, "http_market_data_connector_issues": [], "alpaca_market_data_connector_issues": []},
        telemetry_sink_healthy=True,
        now_utc=now,
    )
    c2 = build_daily_checklist(
        analyze_summaries=[summary],
        startup_json={"readiness": {"status": "READY"}, "http_market_data_connector_issues": [], "alpaca_market_data_connector_issues": []},
        telemetry_sink_healthy=True,
        now_utc=now,
    )
    assert c1.model_dump(mode="json") == c2.model_dump(mode="json")
    assert c1.policy_change_justified is False
    assert c1.policy_change_reasons == []


@pytest.mark.constitutional
def test_daily_checklist_accepts_heartbeat_startup_bundle_shape() -> None:
    now = datetime(2026, 4, 13, 8, 2, tzinfo=timezone.utc)
    summary = {
        "rounds": 60,
        "provider_status_counts": {"SUCCESS": 60},
        "effective_freshness_counts": {"FRESH": 60},
        "fallback_applied_rounds": 0,
        "timeout_signal_rounds": 0,
        "failure_domain_counts": {"NONE": 60},
        "rate_limit_proxy_rounds": 0,
    }

    checklist = build_daily_checklist(
        analyze_summaries=[summary],
        startup_json={
            "heartbeat": {"readiness_status": "READY"},
            "http_market_data_connector_issues": [],
            "alpaca_market_data_connector_issues": [],
        },
        telemetry_sink_healthy=True,
        now_utc=now,
    )

    assert checklist.startup_check_passed is True


@pytest.mark.constitutional
def test_release_decision_rules_block_and_rollback() -> None:
    now = datetime(2026, 4, 13, 8, 3, tzinfo=timezone.utc)
    checklist_block = build_daily_checklist(
        analyze_summaries=[
            {
                "rounds": 60,
                "provider_status_counts": {"CIRCUIT_OPEN": 58},
                "effective_freshness_counts": {"MISSING": 60},
                "fallback_applied_rounds": 0,
                "timeout_signal_rounds": 0,
                "failure_domain_counts": {"AUTH": 6},
                "rate_limit_proxy_rounds": 0,
            }
        ],
        startup_json={"readiness": {"status": "READY"}, "http_market_data_connector_issues": [], "alpaca_market_data_connector_issues": []},
        telemetry_sink_healthy=True,
        now_utc=now,
    )
    review = review_runtime_evidence(checklist=checklist_block, now_utc=now)
    assert review.decision in {"BLOCK_AND_INVESTIGATE", "ROLLBACK_RECOMMENDED"}
    assert review.must_fix_flags


@pytest.mark.constitutional
def test_release_decision_candidate_rc2_requires_threshold_cross() -> None:
    now = datetime(2026, 4, 13, 8, 4, tzinfo=timezone.utc)
    checklist = build_daily_checklist(
        analyze_summaries=[
            {
                "rounds": 90,
                "provider_status_counts": {"SUCCESS": 60, "STALE": 30},
                "effective_freshness_counts": {"FRESH": 60, "STALE": 30},
                "fallback_applied_rounds": 0,
                "timeout_signal_rounds": 0,
                "failure_domain_counts": {"NONE": 90},
                "rate_limit_proxy_rounds": 0,
            }
        ],
        startup_json={"readiness": {"status": "READY"}, "http_market_data_connector_issues": [], "alpaca_market_data_connector_issues": []},
        telemetry_sink_healthy=True,
        now_utc=now,
    )
    assert checklist.policy_change_justified is True
    review = review_runtime_evidence(checklist=checklist, now_utc=now)
    assert review.decision == "CANDIDATE_RC2"
