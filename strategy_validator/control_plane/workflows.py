"""Compatibility shim for governance workflow materialization.

New work should land in the bounded governance modules:
- strategy_validator.control_plane.governance_envelopes
- strategy_validator.control_plane.governance_review_dispatch
- strategy_validator.control_plane.governance_claim_workflows
"""
from strategy_validator.control_plane.governance_envelopes import (
    OracleGovernanceClaimEnvelope,
    OracleGovernanceDispatchEnvelope,
    OracleGovernanceReviewEnvelope,
    OracleGovernanceRoutingEnvelope,
)
from strategy_validator.control_plane.governance_review_dispatch import (
    build_governance_review_sort_key,
    materialize_governance_dispatch_envelope,
    materialize_governance_review_envelope,
    materialize_governance_routing_envelope,
)
from strategy_validator.control_plane.governance_claim_workflows import (
    _governance_claim_worker_sort_key,
    materialize_governance_claim_envelope,
)

__all__ = [
    "OracleGovernanceClaimEnvelope",
    "OracleGovernanceDispatchEnvelope",
    "OracleGovernanceReviewEnvelope",
    "OracleGovernanceRoutingEnvelope",
    "_governance_claim_worker_sort_key",
    "build_governance_review_sort_key",
    "materialize_governance_claim_envelope",
    "materialize_governance_dispatch_envelope",
    "materialize_governance_review_envelope",
    "materialize_governance_routing_envelope",
]
