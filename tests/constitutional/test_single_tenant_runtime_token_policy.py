from __future__ import annotations

from pathlib import Path

from strategy_validator.core.token_policy import (
    is_placeholder_token,
    missing_required_mutation_scopes,
    split_token_scopes,
)


def test_single_tenant_token_policy_rejects_template_values() -> None:
    assert is_placeholder_token("CHANGEME-minimum-32-random-characters") is True
    assert is_placeholder_token("secret-token") is True
    assert is_placeholder_token("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") is True
    assert is_placeholder_token("abcdefghijklmnopqrstuvwxyz1234567890TOKEN") is False


def test_single_tenant_token_policy_normalizes_required_scopes() -> None:
    scopes = split_token_scopes("operator:projection:read, operator:command:write")

    assert scopes == ("operator:command:write", "operator:projection:read")
    assert missing_required_mutation_scopes(scopes) == ()
    assert missing_required_mutation_scopes(("operator:projection:read",)) == ("operator:command:write",)


def test_production_readiness_fails_closed_on_placeholder_token_and_scope_drift() -> None:
    readiness = Path("strategy_validator/validator/readiness.py").read_text(encoding="utf-8")
    auth = Path("strategy_validator/api/auth.py").read_text(encoding="utf-8")

    assert "MUTATION_AUTH_TOKEN_PLACEHOLDER" in readiness
    assert "MUTATION_AUTH_SCOPES_MISSING" in readiness
    assert "is_placeholder_token(api_token)" in readiness
    assert "missing_required_mutation_scopes(api_token_scopes)" in readiness
    assert "MUTATION_TOKEN_PLACEHOLDER" in auth
    assert "MUTATION_TOKEN_SCOPES_MISSING" in auth


def test_production_scope_policy_does_not_default_missing_scopes_to_authorized() -> None:
    auth = Path("strategy_validator/api/auth.py").read_text(encoding="utf-8")
    readiness = Path("strategy_validator/validator/readiness.py").read_text(encoding="utf-8")
    preflight = Path("strategy_validator/cli/single_tenant_preflight.py").read_text(encoding="utf-8")

    assert "default_when_empty=cfg.mode != RuntimeMode.PRODUCTION" in auth
    assert "detail=\"MUTATION_TOKEN_SCOPES_MISSING\"" in auth
    assert "default_when_empty=policy.mode != RuntimeMode.PRODUCTION" in readiness
    assert "default_when_empty=os.environ.get(_ENV_MODE, \"\").strip().upper() != \"PRODUCTION\"" in preflight


def test_research_auth_rejects_placeholder_tokens_in_production() -> None:
    source = Path('strategy_validator/api/research_auth.py').read_text(encoding='utf-8')

    assert 'is_placeholder_token(expected)' in source
    assert 'RESEARCH_API_TOKEN_PLACEHOLDER' in source
    assert 'MUTATION_TOKEN_PLACEHOLDER' in source
