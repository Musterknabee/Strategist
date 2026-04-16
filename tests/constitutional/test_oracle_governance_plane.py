from strategy_validator.validator.oracle_governance_plane import assess_governance_plane


def test_governance_plane_is_ready_when_trust_and_control_are_open() -> None:
    result = assess_governance_plane(
        evidence_freshness_status="FRESH",
        evidence_integrity_status="VERIFIED",
        evidence_coverage_status="COMPLETE",
        support_verification_status="VERIFIED",
        support_chain_trust_status="TRUSTED",
        support_chain_remediation_status="NO_REMEDIATION",
        support_chain_remediation_actions=[],
        operator_readiness="READY_FOR_REVIEW",
        surface_label="this strategist surface",
    )
    assert result.governance_plane_status == "GOVERNANCE_READY"
    assert "status=GOVERNANCE_READY" in result.governance_plane_summary_line
    assert not result.governance_plane_actions


def test_governance_plane_blocks_when_surface_requires_repair() -> None:
    result = assess_governance_plane(
        evidence_freshness_status="STALE",
        evidence_integrity_status="UNVERIFIED",
        evidence_coverage_status="MISSING",
        support_verification_status="UNVERIFIED",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        support_chain_remediation_actions=["Repair the missing support chain before broader use."],
        operator_readiness="HOLD_FOR_REFRESH",
        surface_label="this briefing pack",
    )
    assert result.governance_plane_status == "GOVERNANCE_BLOCKED"
    assert any("not yet fit" in reason for reason in result.governance_plane_reasons)
    assert any("constitutional repair" in action.lower() for action in result.governance_plane_actions)
    assert any("repair the missing support chain" in action.lower() for action in result.governance_plane_actions)
