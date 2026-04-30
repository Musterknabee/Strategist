"""Market-data source policy evaluation for the adjudication orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strategy_validator.core.enums import BANK_STATE_RANKING, PromotionState


@dataclass(frozen=True)
class MarketDataPolicyGateOutcome:
    """State and summary-note output from market-data source policy evaluation."""

    state: PromotionState
    summary_notes: tuple[str, ...]


def evaluate_market_data_source_policy(
    *,
    provenance: Any,
    requires_shorting: bool,
    policy: Any,
    state: PromotionState,
) -> MarketDataPolicyGateOutcome:
    """Evaluate market-data source policy without mutating experiment state.

    The orchestrator owns sequencing and state assignment.  This helper only
    converts execution-realism provenance into the most restrictive lawful
    state plus operator-visible summary notes.
    """
    liquidity_mode = getattr(provenance, "liquidity_source_mode", None)
    borrow_mode = getattr(provenance, "borrow_source_mode", None)
    liquidity_freshness = getattr(provenance, "liquidity_freshness_status", None)
    borrow_freshness = getattr(provenance, "borrow_freshness_status", None)
    provider_errors = tuple(getattr(provenance, "provider_errors", ()) or ())

    summary_notes: list[str] = []
    modes = (liquidity_mode, borrow_mode)

    if getattr(policy, "strict_production_mode", False):
        source_violation = False
        reason = ""

        if any(mode == "PROVISIONAL" for mode in modes):
            source_violation = True
            reason = "provisional data usage"
        elif liquidity_freshness == "STALE" or borrow_freshness == "STALE":
            if not getattr(policy, "allow_market_data_fallback", False):
                source_violation = True
                reason = "stale market data (freshness law violation)"
        elif provider_errors:
            source_violation = True
            reason = "market-data provider failure"
        elif liquidity_mode == "NONE":
            source_violation = True
            reason = "missing liquidity feed"
        elif borrow_mode == "NONE" and requires_shorting:
            source_violation = True
            reason = "missing borrow feed (required for short strategy)"
        elif not getattr(policy, "allow_snapshot_market_data", True):
            used_snapshot = liquidity_mode == "SNAPSHOT" or (borrow_mode == "SNAPSHOT" and requires_shorting)
            if used_snapshot:
                source_violation = True
                reason = "SNAPSHOT-level data (LIVE required by policy)"

        if source_violation:
            state = _reconcile_states(state, PromotionState.REJECTED)
            summary_notes.append(f"STRICT_PRODUCTION_BLOCKER: PROMOTABLE rejected due to {reason}.")

    elif not getattr(policy, "allow_provisional_market_data", True):
        if any(mode in ("PROVISIONAL", "NONE") for mode in modes):
            state = _reconcile_states(state, PromotionState.CONDITIONAL)
            summary_notes.append(
                "PRODUCTION_POLICY_VIOLATION: PROMOTABLE state blocked due to "
                "provisional/unverified market-data usage."
            )
        elif not getattr(policy, "allow_snapshot_market_data", True) and any(mode == "SNAPSHOT" for mode in modes):
            state = _reconcile_states(state, PromotionState.CONDITIONAL)
            summary_notes.append(
                "PRODUCTION_POLICY_VIOLATION: PROMOTABLE state blocked due to "
                "SNAPSHOT data usage (LIVE required)."
            )

    if not getattr(policy, "allow_snapshot_market_data", True):
        non_none_modes = [mode for mode in modes if mode not in ("NONE", None)]
        if non_none_modes and all(mode == "SNAPSHOT" for mode in non_none_modes):
            state = _reconcile_states(state, PromotionState.CONDITIONAL)
            summary_notes.append(
                "SNAPSHOT_ONLY_POLICY: PROMOTABLE requires at least one LIVE "
                f"market-data source; got {non_none_modes}."
            )

    return MarketDataPolicyGateOutcome(state=state, summary_notes=tuple(summary_notes))


def _reconcile_states(current_state: PromotionState, new_restriction: PromotionState) -> PromotionState:
    if BANK_STATE_RANKING[new_restriction] > BANK_STATE_RANKING[current_state]:
        return new_restriction
    return current_state
