from __future__ import annotations

import base64
import hashlib
import json
import math
import mimetypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from strategy_validator.contracts.operational import ClosureSnapshotManifest, DsseEnvelope, DsseSignature, EvidenceResourceDescriptor
from strategy_validator.contracts.oracle_core import (
    EpistemicUncertaintyAssessment,
    MacroRegimeSensorSnapshot,
    MicrostructureSensorSnapshot,
    OracleAdvisoryInput,
    OracleGovernanceActionItem,
    OracleMorningAttestation,
    RegimeProbability,
    SemanticSensorSnapshot,
    StrategyAdvisory,
    StrategyHealthSnapshot,
)
from strategy_validator.contracts.oracle_evidence_events import (
    OracleEvidenceManifest,
    OracleEvidenceVerification,
)

from strategy_validator.validator.oracle_policy import load_oracle_policy, oracle_policy_sha256
from strategy_validator.validator.oracle_artifact_freshness import build_freshness_item, summarize_freshness
from strategy_validator.validator.oracle_artifact_lineage import build_lineage_item, build_lineage_item_from_model, summarize_lineage
from strategy_validator.validator.oracle_artifact_integrity import summarize_artifact_integrity
from strategy_validator.validator.oracle_artifact_coverage import summarize_artifact_coverage
from strategy_validator.validator.oracle_operator_readiness import assess_attestation_operator_readiness
from strategy_validator.validator.oracle_support_verification import summarize_support_verification
from strategy_validator.validator.oracle_support_chain_trust import assess_support_chain_trust
from strategy_validator.validator.oracle_support_chain_remediation import assess_support_chain_remediation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_queue_service import materialize_governance_work_queue_state


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    max_score = max(scores.values())
    exps = {key: math.exp(val - max_score) for key, val in scores.items()}
    total = sum(exps.values()) or 1.0
    return {key: exps[key] / total for key in scores}


def _risk_on_score(macro: MacroRegimeSensorSnapshot, semantic: SemanticSensorSnapshot, micro: MicrostructureSensorSnapshot) -> float:
    return (
        0.018 * macro.yield_curve_slope_bps
        - 0.006 * macro.high_yield_credit_spread_bps
        - 1.15 * macro.cross_asset_correlation_stress
        - 0.90 * macro.realized_volatility_zscore
        - 1.40 * semantic.geopolitical_risk_index
        - 0.80 * semantic.tribunal_belief_conflict
        - 1.00 * micro.liquidity_thinning_score
        - 0.70 * micro.vpin
    )


def _transition_score(macro: MacroRegimeSensorSnapshot, semantic: SemanticSensorSnapshot, micro: MicrostructureSensorSnapshot) -> float:
    return (
        0.60 * abs(macro.equity_bond_correlation)
        + 0.45 * macro.cross_asset_correlation_stress
        + 0.40 * abs(semantic.inflation_hawkishness_score)
        + 0.35 * min(semantic.narrative_contradiction_count / 4.0, 1.5)
        + 0.40 * abs(micro.order_flow_imbalance)
        + 0.30 * max(macro.realized_volatility_zscore, 0.0)
    )


def _risk_off_score(macro: MacroRegimeSensorSnapshot, semantic: SemanticSensorSnapshot, micro: MicrostructureSensorSnapshot) -> float:
    return (
        0.0075 * macro.high_yield_credit_spread_bps
        + 1.10 * macro.cross_asset_correlation_stress
        + 0.95 * max(macro.realized_volatility_zscore, 0.0)
        + 1.25 * semantic.geopolitical_risk_index
        + 0.55 * max(semantic.inflation_hawkishness_score, 0.0)
        + 0.70 * micro.vpin
        + 0.45 * max(micro.spread_variance_zscore, 0.0)
    )


def _liquidity_stress_score(macro: MacroRegimeSensorSnapshot, semantic: SemanticSensorSnapshot, micro: MicrostructureSensorSnapshot) -> float:
    return (
        1.55 * micro.liquidity_thinning_score
        + 1.20 * micro.vpin
        + 0.60 * max(micro.spread_variance_zscore, 0.0)
        + 0.30 * max(macro.realized_volatility_zscore, 0.0)
        + 0.45 * semantic.tribunal_belief_conflict
    )


def _unique(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in out:
            out.append(value)
    return out


def infer_regime_probabilities(payload: OracleAdvisoryInput) -> list[RegimeProbability]:
    semantic = payload.sensors.semantic
    micro = payload.sensors.microstructure
    macro = payload.sensors.macro
    raw_scores = {
        "RISK_ON_LOW_VOL": _risk_on_score(macro, semantic, micro),
        "TRANSITION": _transition_score(macro, semantic, micro),
        "RISK_OFF_HIGH_VOL": _risk_off_score(macro, semantic, micro),
        "LIQUIDITY_STRESS": _liquidity_stress_score(macro, semantic, micro),
    }
    probabilities = _softmax(raw_scores)
    drivers = {
        "RISK_ON_LOW_VOL": [
            f"yield_curve_slope_bps={macro.yield_curve_slope_bps:.1f}",
            f"credit_spread_bps={macro.high_yield_credit_spread_bps:.1f}",
            f"realized_volatility_zscore={macro.realized_volatility_zscore:.2f}",
        ],
        "TRANSITION": [
            f"narrative_contradiction_count={semantic.narrative_contradiction_count}",
            f"order_flow_imbalance={micro.order_flow_imbalance:.2f}",
            f"cross_asset_correlation_stress={macro.cross_asset_correlation_stress:.2f}",
        ],
        "RISK_OFF_HIGH_VOL": [
            f"geopolitical_risk_index={semantic.geopolitical_risk_index:.2f}",
            f"high_yield_credit_spread_bps={macro.high_yield_credit_spread_bps:.1f}",
            f"vpin={micro.vpin:.2f}",
        ],
        "LIQUIDITY_STRESS": [
            f"liquidity_thinning_score={micro.liquidity_thinning_score:.2f}",
            f"spread_variance_zscore={micro.spread_variance_zscore:.2f}",
            f"tribunal_belief_conflict={semantic.tribunal_belief_conflict:.2f}",
        ],
    }
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    return [
        RegimeProbability(regime=regime, probability=round(prob, 6), drivers=drivers[regime])
        for regime, prob in ranked
    ]


def _posterior_edge_confidence(strategy: StrategyHealthSnapshot, dominant_regime: str) -> float:
    prior_strength = 8.0 + abs(strategy.deflated_sharpe_ratio) * 6.0
    alpha = 1.0 + prior_strength * strategy.prior_edge_confidence
    beta = 1.0 + prior_strength * (1.0 - strategy.prior_edge_confidence)
    sharpe_gap = strategy.realized_live_sharpe - strategy.cpcv_lower_bound
    live_success = 0.50
    live_success += 0.18 * _clamp(sharpe_gap, -2.0, 2.0)
    live_success += 0.20 * (strategy.recent_win_rate - 0.50)
    live_success -= 0.35 * strategy.drawdown_fraction
    if strategy.expected_regimes and dominant_regime not in strategy.expected_regimes:
        live_success -= 0.18
    live_success = _clamp(live_success, 0.01, 0.99)
    alpha += 6.0 * live_success
    beta += 6.0 * (1.0 - live_success)
    return _clamp(alpha / (alpha + beta), 0.0, 1.0)


def build_strategy_advisories(strategies: Sequence[StrategyHealthSnapshot], dominant_regime: str) -> list[StrategyAdvisory]:
    advisories: list[StrategyAdvisory] = []
    for strategy in strategies:
        posterior = _posterior_edge_confidence(strategy=strategy, dominant_regime=dominant_regime)
        reasons: list[str] = []
        sharpe_gap = strategy.realized_live_sharpe - strategy.cpcv_lower_bound
        action = "MAINTAIN"
        if strategy.expected_regimes and dominant_regime not in strategy.expected_regimes:
            reasons.append(f"dominant_regime={dominant_regime} not in expected_regimes={strategy.expected_regimes}")
        if sharpe_gap < 0:
            reasons.append(f"realized_live_sharpe below cpcv_lower_bound by {abs(sharpe_gap):.2f}")
        if strategy.drawdown_fraction >= 0.12:
            reasons.append(f"drawdown_fraction elevated at {strategy.drawdown_fraction:.2%}")
        if posterior < 0.25 or strategy.drawdown_fraction >= 0.20:
            action = "HIBERNATE"
            reasons.append("posterior edge confidence breached hard hibernation floor")
        elif posterior < 0.45 or sharpe_gap < 0:
            action = "CANARY"
            reasons.append("posterior edge confidence or live sharpe suggests canary mode")
        else:
            reasons.append("posterior edge confidence remains within advisory maintenance bounds")
        advisories.append(
            StrategyAdvisory(
                strategy_id=strategy.strategy_id,
                strategy_type=strategy.strategy_type,
                posterior_edge_confidence=round(posterior, 6),
                action=action,
                reasons=reasons,
            )
        )
    return advisories


def assess_epistemic_uncertainty(payload: OracleAdvisoryInput, regime_probabilities: Sequence[RegimeProbability]) -> EpistemicUncertaintyAssessment:
    semantic = payload.sensors.semantic
    micro = payload.sensors.microstructure
    macro = payload.sensors.macro
    top_probability = regime_probabilities[0].probability if regime_probabilities else 0.0
    second_probability = regime_probabilities[1].probability if len(regime_probabilities) > 1 else 0.0
    regime_ambiguity = _clamp(1.0 - (top_probability - second_probability), 0.0, 1.0)
    contradiction_pressure = _clamp(semantic.narrative_contradiction_count / 5.0, 0.0, 1.0)
    score = (
        0.35 * semantic.tribunal_belief_conflict
        + 0.20 * contradiction_pressure
        + 0.20 * regime_ambiguity
        + 0.15 * macro.cross_asset_correlation_stress
        + 0.10 * micro.liquidity_thinning_score
    )
    score = _clamp(score, 0.0, 1.0)
    triggers: list[str] = []
    if semantic.tribunal_belief_conflict >= 0.60:
        triggers.append("tribunal belief conflict elevated")
    if semantic.narrative_contradiction_count >= 3:
        triggers.append("narrative contradiction count elevated")
    if regime_ambiguity >= 0.75:
        triggers.append("regime probabilities are unusually flat")
    if macro.cross_asset_correlation_stress >= 0.70:
        triggers.append("cross-asset correlation stress elevated")
    if micro.liquidity_thinning_score >= 0.70:
        triggers.append("liquidity thinning elevated")
    severe_trigger_count = 0
    if semantic.tribunal_belief_conflict >= 0.85:
        severe_trigger_count += 1
    if semantic.narrative_contradiction_count >= 4:
        severe_trigger_count += 1
    if macro.cross_asset_correlation_stress >= 0.85:
        severe_trigger_count += 1
    if micro.liquidity_thinning_score >= 0.75:
        severe_trigger_count += 1
    status = "NOMINAL"
    if score >= 0.75 or severe_trigger_count >= 3:
        status = "UNKNOWN_UNKNOWNS"
    elif score >= 0.45:
        status = "ELEVATED"
    return EpistemicUncertaintyAssessment(
        status=status,
        score=round(score, 6),
        advisory_only=True,
        triggers=triggers,
    )


def _semantic_summary(semantic: SemanticSensorSnapshot) -> str:
    return (
        f"Hawkishness={semantic.inflation_hawkishness_score:.2f}; geopolitical risk={semantic.geopolitical_risk_index:.2f}; "
        f"belief conflict={semantic.tribunal_belief_conflict:.2f}; contradictions={semantic.narrative_contradiction_count}"
    )


def _microstructure_summary(micro: MicrostructureSensorSnapshot) -> str:
    return (
        f"VPIN={micro.vpin:.2f}; OFI={micro.order_flow_imbalance:.2f}; "
        f"spread variance z-score={micro.spread_variance_zscore:.2f}; liquidity thinning={micro.liquidity_thinning_score:.2f}"
    )


def build_oracle_morning_attestation(
    payload: OracleAdvisoryInput,
    now_utc: datetime | None = None,
    repo_root: Path | None = None,
) -> OracleMorningAttestation:
    issued_at = now_utc or payload.generated_for_utc
    regime_probabilities = infer_regime_probabilities(payload)
    dominant_regime = regime_probabilities[0].regime
    strategy_advisories = build_strategy_advisories(payload.strategies, dominant_regime=dominant_regime)
    epistemic = assess_epistemic_uncertainty(payload, regime_probabilities)

    recommended_global_action = "OBSERVE"
    operator_actions = [
        "Treat this report as advisory only; do not route autonomous capital changes from it.",
        "Archive the input payload and attestation beside the current closure package for replay.",
    ]
    if any(item.action == "HIBERNATE" for item in strategy_advisories) or epistemic.status == "UNKNOWN_UNKNOWNS":
        recommended_global_action = "DEFENSIVE_POSTURE"
        operator_actions.append("Escalate to manual review before increasing risk or allocating new capital.")
    elif any(item.action == "CANARY" for item in strategy_advisories) or epistemic.status == "ELEVATED":
        recommended_global_action = "CANARY_REVIEW"
        operator_actions.append("Prefer reduced-size canary observation for strategies under review.")

    policy_version, policy_sha256, policy_path = oracle_policy_sha256(repo_root=repo_root)
    policy_artifact, _ = load_oracle_policy(repo_root=repo_root)
    artifact_freshness = [
        build_freshness_item(
            artifact_label="advisory_input",
            generated_at_utc=payload.generated_for_utc,
            as_of_utc=issued_at,
            fresh_hours=6.0,
            aging_hours=24.0,
        )
    ]
    evidence_freshness_status, stale_artifact_count, freshness_summary_line = summarize_freshness(artifact_freshness)
    artifact_lineage = [
        build_lineage_item(artifact_label="advisory_input", artifact_role="INPUT", schema_version="oracle_advisory_input"),
        build_lineage_item_from_model(artifact_label="oracle_policy", artifact_role="POLICY", model=policy_artifact, source_path=policy_path, integrity_status="VERIFIED"),
    ]
    artifact_lineage_summary_line = summarize_lineage(artifact_lineage)
    evidence_integrity_status, unverified_artifact_count, integrity_summary_line = summarize_artifact_integrity(artifact_lineage)
    evidence_coverage_status, missing_expected_artifact_count, evidence_coverage_summary_line, missing_expected_artifact_labels = summarize_artifact_coverage(expected_labels=["advisory_input", "oracle_policy"], items=artifact_lineage)
    support_verification_status, support_verification_paths, support_verification_summary_line = summarize_support_verification([])
    support_chain_trust_status, support_chain_trust_summary_line, support_chain_trust_reasons = assess_support_chain_trust(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        support_verification_status=support_verification_status,
        formal_verification_required=False,
    )
    support_chain_remediation_status, support_chain_remediation_summary_line, support_chain_remediation_actions = assess_support_chain_remediation(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_labels=missing_expected_artifact_labels,
        support_verification_status=support_verification_status,
        formal_verification_required=False,
    )
    operator_readiness, operator_readiness_summary_line, operator_readiness_reasons = assess_attestation_operator_readiness(
        epistemic_status=epistemic.status,
        recommended_global_action=recommended_global_action,
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        support_verification_status=support_verification_status,
    )

    governance_plane = assess_governance_plane(
        evidence_freshness_status=evidence_freshness_status,
        evidence_integrity_status=evidence_integrity_status,
        evidence_coverage_status=evidence_coverage_status,
        support_verification_status=support_verification_status,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_actions=support_chain_remediation_actions,
        operator_readiness=operator_readiness,
        surface_label="this strategist surface",
    )
    operator_actions = _unique(operator_actions + governance_plane.governance_plane_actions)

    operator_reliance_posture = governance_plane.operator_reliance_posture
    operator_reliance_summary_line = governance_plane.operator_reliance_summary_line
    operator_reliance_reasons = governance_plane.operator_reliance_reasons
    operator_escalation_lane = governance_plane.operator_escalation_lane
    operator_escalation_summary_line = governance_plane.operator_escalation_summary_line
    operator_escalation_reasons = governance_plane.operator_escalation_reasons
    propagation_posture = governance_plane.propagation_posture
    propagation_summary_line = governance_plane.propagation_summary_line
    propagation_reasons = governance_plane.propagation_reasons
    automation_posture = governance_plane.automation_posture
    automation_summary_line = governance_plane.automation_summary_line
    automation_reasons = governance_plane.automation_reasons

    governance_work_queue = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=issued_at,
    )
    governance_review_envelope = governance_work_queue.governance_review_envelope
    governance_routing_envelope = governance_work_queue.governance_routing_envelope
    governance_dispatch_envelope = governance_work_queue.governance_dispatch_envelope
    governance_claim_envelope = governance_work_queue.governance_claim_envelope

    governance_plane_action_items = list(governance_plane.governance_plane_action_items)
    governance_plane_actions = list(governance_plane.governance_plane_actions)
    if not governance_plane_action_items:
        routine_action = OracleGovernanceActionItem(
            dimension="PROPAGATION",
            severity="RESTRICTING",
            action_text="Retain normal provenance discipline when circulating this strategist surface downstream.",
        )
        governance_plane_action_items.append(routine_action)
        governance_plane_actions.append(routine_action.action_text)

    summary_line = (
        f"Dominant regime={dominant_regime}; epistemic status={epistemic.status}; "
        f"global action={recommended_global_action}; execution_authority=ADVISORY_ONLY"
    )
    return OracleMorningAttestation(
        generated_at_utc=issued_at,
        input_timestamp_utc=payload.generated_for_utc,
        universe_label=payload.universe_label,
        oracle_policy_version=policy_version,
        oracle_policy_sha256=policy_sha256,
        oracle_policy_path=policy_path,
        operator_readiness=operator_readiness,
        operator_readiness_summary_line=operator_readiness_summary_line,
        operator_readiness_reasons=operator_readiness_reasons,
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        freshness_summary_line=freshness_summary_line,
        artifact_freshness=artifact_freshness,
        artifact_lineage_summary_line=artifact_lineage_summary_line,
        artifact_lineage=artifact_lineage,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        integrity_summary_line=integrity_summary_line,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        evidence_coverage_summary_line=evidence_coverage_summary_line,
        missing_expected_artifact_labels=missing_expected_artifact_labels,
        support_verification_status=support_verification_status,
        support_verification_summary_line=support_verification_summary_line,
        support_verification_paths=support_verification_paths,
        support_chain_trust_status=support_chain_trust_status,
        support_chain_trust_summary_line=support_chain_trust_summary_line,
        support_chain_trust_reasons=support_chain_trust_reasons,
        support_chain_remediation_status=support_chain_remediation_status,
        support_chain_remediation_summary_line=support_chain_remediation_summary_line,
        support_chain_remediation_actions=support_chain_remediation_actions,
        trust_plane_summary_line=governance_plane.trust_plane_summary_line,
        operator_reliance_posture=operator_reliance_posture,
        operator_reliance_summary_line=operator_reliance_summary_line,
        operator_reliance_reasons=operator_reliance_reasons,
        operator_escalation_lane=operator_escalation_lane,
        operator_escalation_summary_line=operator_escalation_summary_line,
        operator_escalation_reasons=operator_escalation_reasons,
        propagation_posture=propagation_posture,
        propagation_summary_line=propagation_summary_line,
        propagation_reasons=propagation_reasons,
        automation_posture=automation_posture,
        automation_summary_line=automation_summary_line,
        automation_reasons=automation_reasons,
        control_plane_summary_line=governance_plane.control_plane_summary_line,
        governance_plane_status=governance_plane.governance_plane_status,
        governance_plane_summary_line=governance_plane.governance_plane_summary_line,
        governance_plane_reasons=governance_plane.governance_plane_reasons,
        governance_plane_codes=governance_plane.governance_plane_codes,
        governance_plane_blocking_dimensions=governance_plane.governance_plane_blocking_dimensions,
        governance_plane_restricted_dimensions=governance_plane.governance_plane_restricted_dimensions,
        governance_plane_actions=governance_plane_actions,
        governance_plane_action_items=governance_plane_action_items,
        governance_plane_primary_dimension=governance_plane.governance_plane_primary_dimension,
        governance_plane_primary_severity=governance_plane.governance_plane_primary_severity,
        governance_plane_primary_action_text=governance_plane.governance_plane_primary_action_text,
        governance_plane_priority_band=governance_plane.governance_plane_priority_band,
        governance_plane_priority_score=governance_plane.governance_plane_priority_score,
        governance_plane_priority_summary_line=governance_plane.governance_plane_priority_summary_line,
        governance_plane_review_target=governance_plane.governance_plane_review_target,
        governance_plane_review_sla_hours=governance_plane.governance_plane_review_sla_hours,
        governance_plane_review_summary_line=governance_plane.governance_plane_review_summary_line,
        governance_plane_review_due_by_utc=governance_review_envelope.governance_plane_review_due_by_utc,
        governance_plane_review_sort_key=governance_review_envelope.governance_plane_review_sort_key,
        governance_plane_review_envelope_vector=governance_review_envelope.governance_plane_review_envelope_vector,
        governance_plane_review_envelope_sha256=governance_review_envelope.governance_plane_review_envelope_sha256,
        governance_plane_routing_summary_line=governance_routing_envelope.governance_plane_routing_summary_line,
        governance_plane_routing_vector=governance_routing_envelope.governance_plane_routing_vector,
        governance_plane_routing_sha256=governance_routing_envelope.governance_plane_routing_sha256,
        governance_plane_dispatch_posture=governance_dispatch_envelope.governance_plane_dispatch_posture,
        governance_plane_dispatch_permitted=governance_dispatch_envelope.governance_plane_dispatch_permitted,
        governance_plane_dispatch_summary_line=governance_dispatch_envelope.governance_plane_dispatch_summary_line,
        governance_plane_dispatch_reasons=governance_dispatch_envelope.governance_plane_dispatch_reasons,
        governance_plane_dispatch_timeliness=governance_dispatch_envelope.governance_plane_dispatch_timeliness,
        governance_plane_dispatch_claim_permitted_now=governance_dispatch_envelope.governance_plane_dispatch_claim_permitted_now,
        governance_plane_dispatch_timeliness_summary_line=governance_dispatch_envelope.governance_plane_dispatch_timeliness_summary_line,
        governance_plane_dispatch_claim_urgency=governance_dispatch_envelope.governance_plane_dispatch_claim_urgency,
        governance_plane_dispatch_claim_score=governance_dispatch_envelope.governance_plane_dispatch_claim_score,
        governance_plane_dispatch_claim_summary_line=governance_dispatch_envelope.governance_plane_dispatch_claim_summary_line,
        governance_plane_dispatch_vector=governance_dispatch_envelope.governance_plane_dispatch_vector,
        governance_plane_dispatch_sha256=governance_dispatch_envelope.governance_plane_dispatch_sha256,
        governance_plane_dispatch_claim_key=governance_dispatch_envelope.governance_plane_dispatch_claim_key,
        governance_plane_claim_summary_line=governance_claim_envelope.governance_plane_claim_summary_line,
        governance_plane_claim_queue_key=governance_claim_envelope.governance_plane_claim_queue_key,
        governance_plane_claim_review_target=governance_claim_envelope.governance_plane_claim_review_target,
        governance_plane_claim_priority_band=governance_claim_envelope.governance_plane_claim_priority_band,
        governance_plane_claim_review_due_by_utc=governance_claim_envelope.governance_plane_claim_review_due_by_utc,
        governance_plane_claim_review_sort_key=governance_claim_envelope.governance_plane_claim_review_sort_key,
        governance_plane_claim_route_sha256=governance_claim_envelope.governance_plane_claim_route_sha256,
        governance_plane_claim_review_envelope_sha256=governance_claim_envelope.governance_plane_claim_review_envelope_sha256,
        governance_plane_claim_routing_envelope_sha256=governance_claim_envelope.governance_plane_claim_routing_envelope_sha256,
        governance_plane_claim_dispatch_claim_key=governance_claim_envelope.governance_plane_claim_dispatch_claim_key,
        governance_plane_claim_dispatch_sha256=governance_claim_envelope.governance_plane_claim_dispatch_sha256,
        governance_plane_claim_codes=governance_claim_envelope.governance_plane_claim_codes,
        governance_plane_claim_primary_code=governance_claim_envelope.governance_plane_claim_primary_code,
        governance_plane_claim_action_items=governance_claim_envelope.governance_plane_claim_action_items,
        governance_plane_claim_primary_action_text=governance_claim_envelope.governance_plane_claim_primary_action_text,
        governance_plane_claim_worker_lane=governance_claim_envelope.governance_plane_claim_worker_lane,
        governance_plane_claim_worker_summary_line=governance_claim_envelope.governance_plane_claim_worker_summary_line,
        governance_plane_claim_worker_sort_key=governance_claim_envelope.governance_plane_claim_worker_sort_key,
        governance_plane_claim_lease_key=governance_claim_envelope.governance_plane_claim_lease_key,
        governance_plane_claim_lease_mode=governance_claim_envelope.governance_plane_claim_lease_mode,
        governance_plane_claim_lease_ttl_seconds=governance_claim_envelope.governance_plane_claim_lease_ttl_seconds,
        governance_plane_claim_lease_expires_at_utc=governance_claim_envelope.governance_plane_claim_lease_expires_at_utc,
        governance_plane_claim_lease_active_now=governance_claim_envelope.governance_plane_claim_lease_active_now,
        governance_plane_claim_lease_summary_line=governance_claim_envelope.governance_plane_claim_lease_summary_line,
        governance_plane_claim_lease_coverage=governance_claim_envelope.governance_plane_claim_lease_coverage,
        governance_plane_claim_lease_coverage_summary_line=governance_claim_envelope.governance_plane_claim_lease_coverage_summary_line,
        governance_plane_claim_lease_health=governance_claim_envelope.governance_plane_claim_lease_health,
        governance_plane_claim_lease_health_summary_line=governance_claim_envelope.governance_plane_claim_lease_health_summary_line,
        governance_plane_claim_lease_renewal_posture=governance_claim_envelope.governance_plane_claim_lease_renewal_posture,
        governance_plane_claim_lease_renewal_permitted_now=governance_claim_envelope.governance_plane_claim_lease_renewal_permitted_now,
        governance_plane_claim_lease_renewal_summary_line=governance_claim_envelope.governance_plane_claim_lease_renewal_summary_line,
        governance_plane_claim_lease_action=governance_claim_envelope.governance_plane_claim_lease_action,
        governance_plane_claim_lease_action_summary_line=governance_claim_envelope.governance_plane_claim_lease_action_summary_line,
        governance_plane_claim_disposition=governance_claim_envelope.governance_plane_claim_disposition,
        governance_plane_claim_disposition_summary_line=governance_claim_envelope.governance_plane_claim_disposition_summary_line,
        governance_plane_claim_process_posture=governance_claim_envelope.governance_plane_claim_process_posture,
        governance_plane_claim_process_permitted_now=governance_claim_envelope.governance_plane_claim_process_permitted_now,
        governance_plane_claim_process_summary_line=governance_claim_envelope.governance_plane_claim_process_summary_line,
        governance_plane_claim_operability=governance_claim_envelope.governance_plane_claim_operability,
        governance_plane_claim_operability_summary_line=governance_claim_envelope.governance_plane_claim_operability_summary_line,
        governance_plane_claim_vector=governance_claim_envelope.governance_plane_claim_vector,
        governance_plane_claim_sha256=governance_claim_envelope.governance_plane_claim_sha256,
        governance_plane_queue_key=governance_plane.governance_plane_queue_key,
        governance_plane_route_vector=governance_plane.governance_plane_route_vector,
        governance_plane_route_sha256=governance_plane.governance_plane_route_sha256,
        governance_plane_vector=governance_plane.governance_plane_vector,
        governance_plane_sha256=governance_plane.governance_plane_sha256,
        dominant_regime=dominant_regime,
        regime_probabilities=regime_probabilities,
        semantic_state_summary=_semantic_summary(payload.sensors.semantic),
        microstructure_summary=_microstructure_summary(payload.sensors.microstructure),
        strategy_advisories=strategy_advisories,
        epistemic_uncertainty=epistemic,
        recommended_global_action=recommended_global_action,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )


from strategy_validator.validator.oracle_advisory_rendering import render_oracle_morning_attestation_markdown

from strategy_validator.validator.oracle_advisory_evidence import (
    _ORACLE_EVIDENCE_PAYLOAD_TYPE,
    _artifact_descriptor,
    _dsse_pae,
    _json_canonical_bytes,
    _load_private_key,
    _load_public_key,
    _normalize_path,
    _public_key_id,
    _resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _utc_now,
    _verify_dsse_envelope,
    build_oracle_evidence_bundle,
    load_oracle_input,
    verify_oracle_evidence_bundle,
)
