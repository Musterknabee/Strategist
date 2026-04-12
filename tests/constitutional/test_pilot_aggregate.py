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
