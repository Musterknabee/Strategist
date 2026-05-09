"""Paper execution evidence lifecycle raw payload kwarg synthesis."""
from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle_keys import _VALUE_KEYS, _require_complete_values

def build_evidence_lifecycle_payload_kwargs(values: Mapping[str, Any]) -> dict[str, Any]:
    """Build PaperExecutionCockpitPayload kwargs for evidence lifecycle fields."""
    _require_complete_values(values)
    return {key: values[key] for key in _VALUE_KEYS}

__all__ = ["build_evidence_lifecycle_payload_kwargs"]
