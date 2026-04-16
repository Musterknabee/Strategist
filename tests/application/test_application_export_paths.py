from __future__ import annotations

import strategy_validator.application as application


def test_application_root_exports_operator_queue_command_payloads() -> None:
    assert application.build_queue_snapshot.__module__ == 'strategy_validator.application.operator_queue_commands'
    assert application.build_queue_query_payload.__module__ == 'strategy_validator.application.operator_queue_commands'
    assert application.build_workboard_payload.__module__ == 'strategy_validator.application.operator_queue_commands'
    assert application.build_transition_policy_payload.__module__ == 'strategy_validator.application.operator_queue_commands'
