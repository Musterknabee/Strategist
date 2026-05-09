"""Evidence lifecycle cockpit summary/action/payload projection facade."""
from __future__ import annotations

from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_action_payloads import (
    build_evidence_lifecycle_action_kwargs,
)
from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_summary_payloads import (
    build_evidence_lifecycle_summary_kwargs,
)
from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_value_payloads import (
    build_evidence_lifecycle_payload_kwargs,
)

__all__ = [
    "build_evidence_lifecycle_action_kwargs",
    "build_evidence_lifecycle_payload_kwargs",
    "build_evidence_lifecycle_summary_kwargs",
]
