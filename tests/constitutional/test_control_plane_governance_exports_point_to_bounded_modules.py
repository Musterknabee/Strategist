import strategy_validator.control_plane as control_plane


def test_control_plane_governance_exports_resolve_from_bounded_modules() -> None:
    assert control_plane.OracleGovernanceClaimEnvelope.__module__ == "strategy_validator.control_plane.governance_envelopes"
    assert control_plane.OracleGovernanceReviewEnvelope.__module__ == "strategy_validator.control_plane.governance_envelopes"
    assert control_plane.materialize_governance_review_envelope.__module__ == "strategy_validator.control_plane.governance_review_dispatch"
    assert control_plane.materialize_governance_dispatch_envelope.__module__ == "strategy_validator.control_plane.governance_review_dispatch"
    assert control_plane.materialize_governance_claim_envelope.__module__ == "strategy_validator.control_plane.governance_claim_workflows"
