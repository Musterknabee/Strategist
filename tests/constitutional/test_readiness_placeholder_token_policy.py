from __future__ import annotations

from strategy_validator.validator import readiness


def test_production_readiness_rejects_secret_token_placeholder(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "secret-token")
    monkeypatch.setenv(
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
        "operator:command:write,operator:projection:read",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setattr(readiness, "get_schema_version_info", lambda: (1, 1))

    report = readiness.perform_readiness_check()

    assert report.mutation_safety.token_configured is True
    assert report.mutation_safety.mutation_routes_safe is False
    assert report.mutation_safety.detail_code == "MUTATION_AUTH_TOKEN_PLACEHOLDER"
    assert report.checks["production_token_not_placeholder"] is False
    assert report.checks["mutation_routes_safe"] is False
    assert any(blocker.code == "PLACEHOLDER_PRODUCTION_TOKEN" for blocker in report.blockers)
    assert report.status == "BLOCKED"
