from __future__ import annotations

from strategy_validator.application.ui_operator_command_policy_projection import build_ui_operator_command_policy_projection
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext


def test_command_policy_projection_allows_governed_token_context() -> None:
    payload = build_ui_operator_command_policy_projection(
        actions=("claim-item",),
        operator_id="jp",
        work_item_key="wk-1",
        auth_context=UiMutationAuthContext(
            runtime_mode="PRODUCTION",
            authorization_mode="TOKEN",
            token_configured=True,
            token_source="authorization",
            principal_id="jp",
            principal_source="operator_header",
            role="operator",
            scopes=("operator:command:write", "operator:projection:read"),
        ),
    )

    assert payload["schema_version"] == "ui_operator_command_policy_projection/v1"
    assert payload["read_plane_only"] is True
    assert payload["no_token_value_echoed"] is True
    assert payload["overall_lifecycle_state"] == "ALLOWED"
    assert payload["allowed_count"] == 1
    assert payload["blocked_count"] == 0
    assert payload["target_identity_present"] is True
    assert payload["policies"][0]["is_allowed"] is True


def test_command_policy_projection_blocks_missing_operator_and_target() -> None:
    payload = build_ui_operator_command_policy_projection(
        actions=("claim-item", "unknown-command"),
        operator_id="",
        auth_context=UiMutationAuthContext(
            runtime_mode="TEST",
            authorization_mode="NON_PRODUCTION_BYPASS",
            token_configured=False,
            token_source="none",
            principal_id="local",
            principal_source="local_bypass",
            role="local",
            scopes=("operator:command:write",),
        ),
    )

    assert payload["overall_lifecycle_state"] == "BLOCKED"
    assert payload["blocked_count"] == 2
    assert payload["unsupported_count"] == 1
    assert payload["target_identity_present"] is False
    reasons = payload["policies"][0]["blocking_reasons"]
    assert "operator_id is required" in reasons
    assert any("governed target field" in reason for reason in reasons)
    assert payload["policies"][1]["is_supported_action"] is False


def test_command_policy_projection_defaults_to_production_token_preview_without_echo(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "a" * 40)
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN_SCOPES", "operator:command:write operator:projection:read")

    blocked = build_ui_operator_command_policy_projection(
        actions=("claim-item",),
        operator_id="jp",
        work_item_key="wk-1",
    )
    assert blocked["auth_context"]["token_configured"] is True
    assert blocked["auth_context"]["token_source"] == "none"
    assert blocked["blocked_count"] == 1
    assert any("no token source" in reason for reason in blocked["policies"][0]["blocking_reasons"])

    allowed = build_ui_operator_command_policy_projection(
        actions=("claim-item",),
        operator_id="jp",
        work_item_key="wk-1",
        assume_token_present=True,
    )
    assert allowed["auth_context"]["token_source"] == "authorization"
    assert allowed["allowed_count"] == 1
    assert allowed["no_token_value_echoed"] is True
