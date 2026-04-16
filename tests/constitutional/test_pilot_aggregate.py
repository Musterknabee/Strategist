from __future__ import annotations

import pytest

from strategy_validator.cli.pilot_aggregate import suggest_env_from_summary, summarize_records


@pytest.mark.constitutional
def test_summarize_empty() -> None:
    assert summarize_records([])["rounds"] == 0


@pytest.mark.constitutional
def test_suggest_env_from_rate_limit_signal() -> None:
    summary = {
        "rounds": 10,
        "rate_limit_proxy_rounds": 5,
        "stale_or_old_snapshot_rounds": 0,
        "auth_domain_rounds": 0,
        "failure_domain_counts": {"RATE_LIMIT": 5},
    }
    lines = suggest_env_from_summary(summary)
    assert any("MAX_RETRIES" in ln for ln in lines)


@pytest.mark.constitutional
def test_suggest_env_empty_pilot_file_message() -> None:
    lines = suggest_env_from_summary({"rounds": 0})
    assert any("pilot probe" in ln.lower() for ln in lines)


@pytest.mark.constitutional
def test_summarize_resolution_schema_latency_and_fallback() -> None:
    rows = [
        {
            "pilot_schema": "2",
            "latency_ms": 10.0,
            "primary_latency_ms": 8.0,
            "fallback_latency_ms": 2.0,
            "provider_status": "STALE",
            "effective_freshness_status": "FRESH",
            "primary_freshness_status": "STALE",
            "failure_domain": "NONE",
            "failure_code": "NONE",
            "fallback_applied": True,
            "vendor_failure_events": [{"domain": "RATE_LIMIT", "code": "HTTP_429"}],
        },
        {
            "pilot_schema": "2",
            "latency_ms": 20.0,
            "primary_latency_ms": 20.0,
            "fallback_latency_ms": 0.0,
            "provider_status": "SUCCESS",
            "effective_freshness_status": "FRESH",
            "primary_freshness_status": "FRESH",
            "failure_domain": None,
            "failure_code": None,
            "fallback_applied": False,
            "vendor_failure_events": [],
        },
    ]
    s = summarize_records(rows)
    assert s["rounds"] == 2
    assert s["fallback_applied_rounds"] == 1
    assert s["effective_freshness_counts"]["FRESH"] == 2
    assert s["primary_freshness_counts"]["STALE"] == 1
    assert s["latency_ms_distribution"]["p50_ms"] is not None
    assert s["vendor_failure_event_domain_counts"].get("RATE_LIMIT") == 1
