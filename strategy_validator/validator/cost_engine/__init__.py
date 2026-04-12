"""Execution-cost and economics realism checks (no I/O, no ledger)."""

from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.evidence import Evidence


def evidence_uses_midpoint_only_economics(evidence: Iterable[Evidence]) -> bool:
    """
    Midpoint-only execution economics are not admissible for promotable strategies.

    Convention: evidence.payload may include economics_model or execution_price_assumption.
    """
    for ev in evidence:
        if ev.payload.get("economics_model") in ("midpoint_only", "MIDPOINT_ONLY"):
            return True
        if ev.payload.get("execution_price_assumption") in ("midpoint_only", "MIDPOINT_ONLY"):
            return True
        if ev.payload.get("midpoint_only") is True:
            return True
    return False
