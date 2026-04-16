from strategy_validator.validator.oracle_control_plane import assess_control_plane


def test_control_plane_is_routine_for_ready_trusted_surfaces() -> None:
    result = assess_control_plane(
        operator_readiness="READY_FOR_REVIEW",
        support_chain_trust_status="TRUSTED",
        support_chain_remediation_status="NO_REMEDIATION",
        surface_label="this strategist surface",
    )
    assert result.operator_reliance_posture == "ROUTINE_ADVISORY"
    assert result.operator_escalation_lane == "STANDARD_OPERATOR_FLOW"
    assert result.propagation_posture == "DOWNSTREAM_PROPAGATION_ALLOWED"
    assert result.automation_posture == "AUTOMATION_ELIGIBLE"
    assert not result.control_plane_actions
    assert "reliance=ROUTINE_ADVISORY" in result.control_plane_summary_line


def test_control_plane_requires_repair_for_untrusted_surfaces() -> None:
    result = assess_control_plane(
        operator_readiness="HOLD_FOR_REFRESH",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        surface_label="this briefing pack",
    )
    assert result.operator_reliance_posture == "REPAIR_FIRST"
    assert result.operator_escalation_lane == "CONSTITUTIONAL_REPAIR_ESCALATION"
    assert result.propagation_posture == "LOCAL_ONLY_DO_NOT_PROPAGATE"
    assert result.automation_posture == "HUMAN_ONLY_NO_AUTOMATION"
    assert any("constitutional repair review" in action.lower() for action in result.control_plane_actions)
    assert any("local-only" in action.lower() for action in result.control_plane_actions)
    assert any("automated advisory workflows" in action.lower() for action in result.control_plane_actions)
