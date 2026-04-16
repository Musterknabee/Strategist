from __future__ import annotations

from datetime import datetime
from typing import Any

from strategy_validator.control_plane.governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_queue_query import run_operator_queue_query
from strategy_validator.control_plane.operator_queue_service import materialize_governance_work_queue_state


def build_governance_queue(
    *,
    issued_at_utc: datetime,
    surface_label: str,
    evidence_freshness_status: str = 'EVIDENCE_CURRENT',
    evidence_integrity_status: str = 'INTEGRITY_VERIFIED',
    evidence_coverage_status: str = 'COVERAGE_COMPLETE',
    support_verification_status: str = 'SUPPORT_VERIFIED',
    support_chain_trust_status: str = 'TRUSTED',
    support_chain_remediation_status: str = 'REMEDIATION_NONE',
    support_chain_remediation_actions: list[str] | None = None,
    operator_readiness: str = 'READY_FOR_REVIEW',
    **_: Any,
):
    """Materialize the canonical governance work queue state from policy inputs."""
    governance_plane = assess_governance_plane(
        evidence_freshness_status=evidence_freshness_status,
        evidence_integrity_status=evidence_integrity_status,
        evidence_coverage_status=evidence_coverage_status,
        support_verification_status=support_verification_status,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_actions=support_chain_remediation_actions,
        operator_readiness=operator_readiness,
        surface_label=surface_label,
    )
    return materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=issued_at_utc,
    )



def query_operator_queue(*args: Any, **kwargs: Any):
    """Query the operator work queue through the control-plane read surface."""
    return run_operator_queue_query(*args, **kwargs)


__all__ = ['build_governance_queue', 'query_operator_queue']
