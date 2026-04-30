from __future__ import annotations

from strategy_validator.application.ui_command_actions import execute_ui_operator_command
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest
from strategy_validator.projections.operator_action_event_index import build_operator_action_event_projection_index


def test_ui_operator_command_is_visible_in_operator_projection() -> None:
    request = UiOperatorCommandRequest(operator_id="projection-test", work_item_key="item-1", idempotency_key="projection-test-key")
    auth = UiMutationAuthContext(
        runtime_mode="TEST",
        authorization_mode="NON_PRODUCTION_BYPASS",
        token_configured=False,
        token_source="none",
        principal_id="projection-test-principal",
        principal_source="local_bypass",
    )
    receipt = execute_ui_operator_command(action="claim-item", request=request, auth_context=auth)
    index = build_operator_action_event_projection_index()
    entries = {entry.action_event_id: entry for entry in index.entries}
    assert receipt["command_id"] in entries
    assert receipt["authorization"]["principal_id"] == "projection-test-principal"
    entry = entries[receipt["command_id"]]
    assert entry.authorization_principal_id == "projection-test-principal"
    assert entry.authorization_principal_source == "local_bypass"
    assert entry.authorization_mode == "NON_PRODUCTION_BYPASS"
