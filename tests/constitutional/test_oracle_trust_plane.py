from strategy_validator.validator.oracle_trust_plane import assess_trust_plane


def test_trust_plane_is_nominal_for_trusted_surface() -> None:
    result = assess_trust_plane(
        evidence_freshness_status="FRESH",
        evidence_integrity_status="VERIFIED",
        evidence_coverage_status="COMPLETE",
        support_verification_status="VERIFIED",
        support_chain_trust_status="TRUSTED",
        support_chain_remediation_status="NO_REMEDIATION",
        support_chain_remediation_actions=["No support-chain remediation is currently required; preserve normal provenance discipline."],
        surface_label="this strategist surface",
    )
    assert "freshness=FRESH" in result.trust_plane_summary_line
    assert any("preserve normal provenance discipline" in action.lower() for action in result.trust_plane_actions)


def test_trust_plane_demands_repair_for_untrusted_surface() -> None:
    result = assess_trust_plane(
        evidence_freshness_status="STALE",
        evidence_integrity_status="UNVERIFIED",
        evidence_coverage_status="MISSING",
        support_verification_status="UNVERIFIED",
        support_chain_trust_status="UNTRUSTED",
        support_chain_remediation_status="REMEDIATION_REQUIRED",
        support_chain_remediation_actions=["Refresh stale supporting artifacts before relying on this strategist surface."],
        surface_label="this briefing pack",
    )
    assert any("do not materially rely" in action.lower() for action in result.trust_plane_actions)
    assert any("refresh stale supporting artifacts" in action.lower() for action in result.trust_plane_actions)
