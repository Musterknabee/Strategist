from __future__ import annotations

from pathlib import Path

from strategy_validator.control_plane.operator_pack_assignment import (
    build_operator_pack_assignment_request,
    materialize_operator_pack_assignment,
)
from strategy_validator.control_plane.operator_pack_claim_lease import (
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
)
from strategy_validator.control_plane.operator_pack_claim_lifecycle import (
    build_operator_pack_claim_lifecycle_request,
    materialize_operator_pack_claim_lifecycle,
)
from strategy_validator.control_plane.operator_pack_claim_operability import (
    build_operator_pack_claim_operability_request,
    materialize_operator_pack_claim_operability,
)
from strategy_validator.control_plane.operator_pack_escalation import (
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
)


def build_pack_escalation_payload(**kwargs) -> dict:
    return materialize_operator_pack_escalation(
        build_operator_pack_escalation_request(**kwargs)
    ).to_payload()



def build_pack_assignment_payload(**kwargs) -> dict:
    return materialize_operator_pack_assignment(
        build_operator_pack_assignment_request(**kwargs)
    ).to_payload()



def build_pack_claim_lease_payload(**kwargs) -> dict:
    return materialize_operator_pack_claim_lease(
        build_operator_pack_claim_lease_request(**kwargs)
    ).to_payload()



def build_pack_claim_lifecycle_payload(**kwargs) -> dict:
    return materialize_operator_pack_claim_lifecycle(
        build_operator_pack_claim_lifecycle_request(**kwargs)
    ).to_payload()



def build_pack_claim_operability_payload(**kwargs) -> dict:
    return materialize_operator_pack_claim_operability(
        build_operator_pack_claim_operability_request(**kwargs)
    ).to_payload()
