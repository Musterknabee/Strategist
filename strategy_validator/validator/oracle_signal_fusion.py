from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from strategy_validator.contracts.oracle_core import OracleAdvisoryInput
from strategy_validator.contracts.oracle_strategic_fusion import OracleStrategicFusionReport
from strategy_validator.validator.oracle_advisory import assess_epistemic_uncertainty, infer_regime_probabilities
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_run_identity import strategic_epoch_from_payload
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, strategic_artifact_evidence_support_score
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal
from strategy_validator.validator.oracle_policy import load_oracle_policy, oracle_policy_sha256
from strategy_validator.validator.oracle_artifact_freshness import build_freshness_item, summarize_freshness
from strategy_validator.validator.oracle_artifact_lineage import build_lineage_item, build_lineage_item_from_model, build_lineage_item_from_registered_artifact, summarize_lineage
from strategy_validator.validator.oracle_artifact_integrity import summarize_artifact_integrity
from strategy_validator.validator.oracle_artifact_coverage import summarize_artifact_coverage
from strategy_validator.validator.oracle_operator_readiness import assess_fusion_operator_readiness
from strategy_validator.validator.oracle_support_verification import summarize_support_verification
from strategy_validator.validator.oracle_support_chain_trust import assess_support_chain_trust
from strategy_validator.validator.oracle_support_chain_remediation import assess_support_chain_remediation
from strategy_validator.validator.oracle_governance_plane import assess_governance_plane
from strategy_validator.control_plane.operator_queue_snapshot import materialize_operator_queue_snapshot
from strategy_validator.validator.oracle_schema_registry import load_artifact_payload
from strategy_validator.validator.oracle_signal_fusion_rendering import (
    render_oracle_strategic_fusion_markdown,
)


def _resolve_preferred_artifact_evidence(*artifact_evidences: dict[str, str] | None) -> dict[str, str] | None:
    candidates = [item for item in artifact_evidences if item is not None]
    if not candidates:
        return None
    return max(candidates, key=strategic_artifact_evidence_support_score)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _unique(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in out:
            out.append(value)
    return out


def build_oracle_strategic_fusion_report(
    payload: OracleAdvisoryInput | dict,
    now_utc: datetime | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
) -> OracleStrategicFusionReport:
    payload = OracleAdvisoryInput.model_validate(payload)
    issued_at = now_utc or payload.generated_for_utc or _utc_now()
    oracle_run_id, input_timestamp_utc = strategic_epoch_from_payload(payload)
    regime_probabilities = infer_regime_probabilities(payload)
    dominant = regime_probabilities[0]
    epistemic = assess_epistemic_uncertainty(payload, regime_probabilities)
    second_probability = regime_probabilities[1].probability if len(regime_probabilities) > 1 else 0.0
    ambiguity = _clamp(1.0 - (dominant.probability - second_probability), 0.0, 1.0)
    regime_mismatch_ratio = _mean([
        1.0 if strategy.expected_regimes and dominant.regime not in strategy.expected_regimes else 0.0
        for strategy in payload.strategies
    ])
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    resolved_search_root = search_root.resolve() if search_root is not None else resolved_repo_root
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() and resolved_repo_root is not None else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() and resolved_repo_root is not None else None
    preferred_artifact_evidence = _resolve_preferred_artifact_evidence(doctrine_artifact_evidence, research_artifact_evidence)
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    policy_version, policy_sha256, policy_path = oracle_policy_sha256(repo_root=resolved_repo_root)
    policy_artifact, _ = load_oracle_policy(repo_root=resolved_repo_root)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    exact_evidence_support_score = round(max(doctrine_exact_support, research_exact_support, cadence.exact_evidence_support_score), 6)

    strategy_pressure = _clamp(_mean([
        _clamp(strategy.drawdown_fraction * 2.4, 0.0, 1.0)
        + 0.35 * (1.0 if strategy.realized_live_sharpe < strategy.cpcv_lower_bound else 0.0)
        + 0.25 * (0.5 - min(strategy.recent_win_rate, 0.5)) * 2.0
        for strategy in payload.strategies
    ]), 0.0, 1.0)

    sensors = payload.sensors
    doctrine_stress = _clamp(
        0.30 * sensors.semantic.tribunal_belief_conflict
        + 0.20 * min(sensors.semantic.narrative_contradiction_count / 4.0, 1.0)
        + 0.20 * ambiguity
        + 0.15 * regime_mismatch_ratio
        + 0.15 * sensors.microstructure.liquidity_thinning_score
        - 0.06 * doctrine_exact_support,
        0.0,
        1.0,
    )
    caution_score = _clamp(
        0.28 * epistemic.score
        + 0.22 * sensors.microstructure.liquidity_thinning_score
        + 0.18 * sensors.macro.cross_asset_correlation_stress
        + 0.12 * max(sensors.macro.realized_volatility_zscore, 0.0)
        + 0.10 * strategy_pressure
        + 0.10 * regime_mismatch_ratio
        - 0.05 * exact_evidence_support_score,
        0.0,
        1.0,
    )
    opportunity_score = _clamp(
        0.42 * dominant.probability * (1.0 if dominant.regime == "RISK_ON_LOW_VOL" else 0.75 if dominant.regime == "TRANSITION" else 0.35)
        + 0.25 * _mean([max(strategy.realized_live_sharpe - strategy.cpcv_lower_bound, 0.0) for strategy in payload.strategies])
        + 0.20 * _mean([strategy.recent_win_rate for strategy in payload.strategies])
        + 0.13 * (1.0 - caution_score)
        + 0.04 * exact_evidence_support_score,
        0.0,
        1.0,
    )

    if epistemic.status == "UNKNOWN_UNKNOWNS" and doctrine_stress >= 0.75:
        posture = "RESEARCH_FREEZE"
    elif caution_score >= 0.70 or doctrine_stress >= 0.72:
        posture = "DEFENSIVE_RESEARCH"
    elif opportunity_score >= 0.65 and caution_score < 0.45 and doctrine_stress < 0.45:
        posture = "OPPORTUNITY_BIASED"
    elif caution_score >= 0.52:
        posture = "CAUTION_BIASED"
    else:
        posture = "BALANCED_OBSERVATION"

    opportunity_factors: list[str] = []
    caution_factors: list[str] = []
    doctrine_pressure_points: list[str] = []
    if dominant.regime == "RISK_ON_LOW_VOL":
        opportunity_factors.append(f"dominant risk-on regime confidence is {dominant.probability:.1%}")
    if _mean([strategy.recent_win_rate for strategy in payload.strategies]) >= 0.55:
        opportunity_factors.append("recent strategy win rates are supportive")
    if exact_evidence_support_score > 0.0:
        opportunity_factors.append(f"exact sealed strategist support is stabilizing posture confidence ({exact_evidence_support_score:.2f})")
    if exact_cadence_signal_classification == "EXACT_CONFIRMED_PRESSURE":
        caution_factors.append(f"repeated exact sealed confirmations are tightening posture cadence ({cadence.exact_feedback_confirmation_count})")
    elif exact_cadence_signal_classification == "EXACT_RELIEF_PRESSURE":
        opportunity_factors.append(f"repeated exact sealed relief is softening posture cadence ({cadence.exact_feedback_relief_count})")
    if _mean([max(strategy.realized_live_sharpe - strategy.cpcv_lower_bound, 0.0) for strategy in payload.strategies]) > 0.15:
        opportunity_factors.append("live sharpe is exceeding the cpcv floor across the strategy set")

    if sensors.microstructure.liquidity_thinning_score >= 0.60:
        caution_factors.append("liquidity is thinning materially")
    if sensors.semantic.narrative_contradiction_count >= 3:
        caution_factors.append("narrative contradiction pressure is elevated")
    if sensors.macro.cross_asset_correlation_stress >= 0.65:
        caution_factors.append("cross-asset stress is elevated")
    if regime_mismatch_ratio >= 0.50:
        caution_factors.append("half or more of tracked strategies are misaligned with the dominant regime")

    if sensors.semantic.tribunal_belief_conflict >= 0.55:
        doctrine_pressure_points.append("tribunal belief conflict is pressing on doctrine confidence")
    if regime_mismatch_ratio >= 0.40:
        doctrine_pressure_points.append("strategy regime mismatch is accumulating")
    if ambiguity >= 0.70:
        doctrine_pressure_points.append("regime ambiguity is high enough to weaken stable doctrine assumptions")
    if doctrine_exact_support > 0.0:
        doctrine_pressure_points.append(f"exact sealed doctrine support offsets part of the current doctrine stress ({doctrine_exact_support:.2f})")

    artifact_freshness = [
        build_freshness_item(
            artifact_label="advisory_input",
            generated_at_utc=input_timestamp_utc,
            as_of_utc=issued_at,
            fresh_hours=6.0,
            aging_hours=24.0,
        )
    ]
    if preferred_artifact_evidence is not None and preferred_artifact_evidence.get("manifest_path"):
        try:
            artifact_payload = load_artifact_payload(Path(preferred_artifact_evidence["manifest_path"]))
            artifact_freshness.append(
                build_freshness_item(
                    artifact_label="preferred_strategic_artifact_evidence",
                    generated_at_utc=artifact_payload.get("generated_at_utc"),
                    as_of_utc=issued_at,
                    source_path=preferred_artifact_evidence["manifest_path"],
                    fresh_hours=72.0,
                    aging_hours=168.0,
                )
            )
        except Exception:
            pass
    evidence_freshness_status, stale_artifact_count, freshness_summary_line = summarize_freshness(artifact_freshness)
    artifact_lineage = [
        build_lineage_item(artifact_label="advisory_input", artifact_role="INPUT", schema_version="oracle_advisory_input"),
        build_lineage_item_from_model(artifact_label="oracle_policy", artifact_role="POLICY", model=policy_artifact, source_path=policy_path, integrity_status="VERIFIED"),
    ]
    if preferred_artifact_evidence is not None and preferred_artifact_evidence.get("manifest_path"):
        try:
            artifact_lineage.append(
                build_lineage_item_from_registered_artifact(
                    artifact_label="preferred_strategic_artifact_evidence",
                    artifact_role="EVIDENCE",
                    path=Path(preferred_artifact_evidence["manifest_path"]),
                    integrity_status=preferred_artifact_evidence.get("evidence_status"),
                )
            )
        except Exception:
            pass
    artifact_lineage_summary_line = summarize_lineage(artifact_lineage)
    evidence_integrity_status, unverified_artifact_count, integrity_summary_line = summarize_artifact_integrity(artifact_lineage)
    expected_labels = ["advisory_input", "oracle_policy"]
    strategic_support_declared = doctrine_adaptation_report_path is not None or research_priority_report_path is not None
    if strategic_support_declared:
        expected_labels.append("preferred_strategic_artifact_evidence")
    evidence_coverage_status, missing_expected_artifact_count, evidence_coverage_summary_line, missing_expected_artifact_labels = summarize_artifact_coverage(expected_labels=expected_labels, items=artifact_lineage)
    support_manifest_paths = []
    if preferred_artifact_evidence is not None and preferred_artifact_evidence.get("manifest_path"):
        support_manifest_paths.append(Path(preferred_artifact_evidence["manifest_path"]))
    support_verification_status, support_verification_paths, support_verification_summary_line = summarize_support_verification(support_manifest_paths)
    support_chain_trust_status, support_chain_trust_summary_line, support_chain_trust_reasons = assess_support_chain_trust(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_count=missing_expected_artifact_count,
        support_verification_status=support_verification_status,
        formal_verification_required=True,
    )
    support_chain_remediation_status, support_chain_remediation_summary_line, support_chain_remediation_actions = assess_support_chain_remediation(
        evidence_freshness_status=evidence_freshness_status,
        stale_artifact_count=stale_artifact_count,
        evidence_integrity_status=evidence_integrity_status,
        unverified_artifact_count=unverified_artifact_count,
        evidence_coverage_status=evidence_coverage_status,
        missing_expected_artifact_labels=missing_expected_artifact_labels,
        support_verification_status=support_verification_status,
        formal_verification_required=True,
    )

    operator_actions = [
        "Treat fused posture as advisory-only research guidance, never as execution authority.",
    ]
    if posture in {"DEFENSIVE_RESEARCH", "RESEARCH_FREEZE"}:
        operator_actions.append("Prioritize doctrine review, risk throttling hypotheses, and evidence preservation before new research expansion.")
    elif posture == "OPPORTUNITY_BIASED":
        operator_actions.append("Queue opportunity validation and canary-sized research expansion while preserving regime and doctrine evidence.")
    else:
        operator_actions.append("Monitor sensor drift and refresh the fused posture before making strategy-selection changes.")
    if exact_evidence_support_score >= 0.99:
        operator_actions.append("Treat exact sealed doctrine or research subjects as a stabilizing authority for posture interpretation, while keeping the stack advisory-only.")
    if stale_artifact_count > 0:
        operator_actions.append("Refresh stale strategist evidence before escalating posture changes from this fused view.")
    if support_verification_status == "UNVERIFIED":
        operator_actions.append("Investigate failed or unverified support verification artifacts before treating the fused view as strongly grounded.")
    elif support_verification_status == "INCOMPLETE":
        operator_actions.append("Complete support verification for the fused strategist evidence chain before increasing reliance on this view.")
    elif support_verification_status == "ABSENT" and evidence_coverage_status == "COMPLETE":
        operator_actions.append("Produce formal support verification artifacts for the fused strategist evidence chain to strengthen operator trust and replayability.")
    operator_readiness, operator_readiness_summary_line, operator_readiness_reasons = assess_fusion_operator_readiness(
        epistemic_status=epistemic.status,
        strategic_posture=posture,
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
        surface_label="this fused strategist view",
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

    operator_queue_snapshot = materialize_operator_queue_snapshot(
        governance_plane=governance_plane,
        issued_at_utc=issued_at,
    )
    governance_work_queue = operator_queue_snapshot.queue_state
    governance_review_envelope = governance_work_queue.governance_review_envelope
    governance_routing_envelope = governance_work_queue.governance_routing_envelope
    governance_dispatch_envelope = governance_work_queue.governance_dispatch_envelope
    governance_claim_envelope = governance_work_queue.governance_claim_envelope
    primary_work_item = operator_queue_snapshot.primary_work_item

    return OracleStrategicFusionReport(
        generated_at_utc=issued_at,
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
        governance_plane_actions=governance_plane.governance_plane_actions,
        governance_plane_action_items=governance_plane.governance_plane_action_items,
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
        governance_plane_dispatch_posture=primary_work_item.dispatch_posture,
        governance_plane_dispatch_permitted=primary_work_item.dispatch_permitted,
        governance_plane_dispatch_summary_line=governance_dispatch_envelope.governance_plane_dispatch_summary_line,
        governance_plane_dispatch_reasons=governance_dispatch_envelope.governance_plane_dispatch_reasons,
        governance_plane_dispatch_timeliness=governance_dispatch_envelope.governance_plane_dispatch_timeliness,
        governance_plane_dispatch_claim_permitted_now=primary_work_item.dispatch_claim_permitted_now,
        governance_plane_dispatch_timeliness_summary_line=governance_dispatch_envelope.governance_plane_dispatch_timeliness_summary_line,
        governance_plane_dispatch_claim_urgency=primary_work_item.dispatch_claim_urgency,
        governance_plane_dispatch_claim_score=primary_work_item.dispatch_claim_score,
        governance_plane_dispatch_claim_summary_line=primary_work_item.dispatch_claim_summary_line,
        governance_plane_dispatch_vector=governance_dispatch_envelope.governance_plane_dispatch_vector,
        governance_plane_dispatch_sha256=governance_dispatch_envelope.governance_plane_dispatch_sha256,
        governance_plane_dispatch_claim_key=primary_work_item.dispatch_claim_key,
        governance_plane_claim_summary_line=primary_work_item.claim_summary_line,
        governance_plane_claim_queue_key=primary_work_item.queue_key,
        governance_plane_claim_review_target=primary_work_item.review_target,
        governance_plane_claim_priority_band=primary_work_item.priority_band,
        governance_plane_claim_review_due_by_utc=primary_work_item.review_due_by_utc,
        governance_plane_claim_review_sort_key=primary_work_item.review_sort_key,
        governance_plane_claim_route_sha256=governance_claim_envelope.governance_plane_claim_route_sha256,
        governance_plane_claim_review_envelope_sha256=governance_claim_envelope.governance_plane_claim_review_envelope_sha256,
        governance_plane_claim_routing_envelope_sha256=governance_claim_envelope.governance_plane_claim_routing_envelope_sha256,
        governance_plane_claim_dispatch_claim_key=governance_claim_envelope.governance_plane_claim_dispatch_claim_key,
        governance_plane_claim_dispatch_sha256=governance_claim_envelope.governance_plane_claim_dispatch_sha256,
        governance_plane_claim_codes=governance_claim_envelope.governance_plane_claim_codes,
        governance_plane_claim_primary_code=governance_claim_envelope.governance_plane_claim_primary_code,
        governance_plane_claim_action_items=governance_claim_envelope.governance_plane_claim_action_items,
        governance_plane_claim_primary_action_text=primary_work_item.claim_primary_action_text,
        governance_plane_claim_worker_lane=primary_work_item.claim_worker_lane,
        governance_plane_claim_worker_summary_line=primary_work_item.claim_worker_summary_line,
        governance_plane_claim_worker_sort_key=primary_work_item.claim_worker_sort_key,
        governance_plane_claim_lease_key=primary_work_item.lease_key,
        governance_plane_claim_lease_mode=governance_claim_envelope.governance_plane_claim_lease_mode,
        governance_plane_claim_lease_ttl_seconds=governance_claim_envelope.governance_plane_claim_lease_ttl_seconds,
        governance_plane_claim_lease_expires_at_utc=governance_claim_envelope.governance_plane_claim_lease_expires_at_utc,
        governance_plane_claim_lease_active_now=primary_work_item.lease_active_now,
        governance_plane_claim_lease_summary_line=primary_work_item.lease_summary_line,
        governance_plane_claim_lease_coverage=governance_claim_envelope.governance_plane_claim_lease_coverage,
        governance_plane_claim_lease_coverage_summary_line=governance_claim_envelope.governance_plane_claim_lease_coverage_summary_line,
        governance_plane_claim_lease_health=governance_claim_envelope.governance_plane_claim_lease_health,
        governance_plane_claim_lease_health_summary_line=governance_claim_envelope.governance_plane_claim_lease_health_summary_line,
        governance_plane_claim_lease_renewal_posture=governance_claim_envelope.governance_plane_claim_lease_renewal_posture,
        governance_plane_claim_lease_renewal_permitted_now=governance_claim_envelope.governance_plane_claim_lease_renewal_permitted_now,
        governance_plane_claim_lease_renewal_summary_line=governance_claim_envelope.governance_plane_claim_lease_renewal_summary_line,
        governance_plane_claim_lease_action=primary_work_item.lease_action,
        governance_plane_claim_lease_action_summary_line=primary_work_item.lease_action_summary_line,
        governance_plane_claim_disposition=governance_claim_envelope.governance_plane_claim_disposition,
        governance_plane_claim_disposition_summary_line=governance_claim_envelope.governance_plane_claim_disposition_summary_line,
        governance_plane_claim_process_posture=governance_claim_envelope.governance_plane_claim_process_posture,
        governance_plane_claim_process_permitted_now=governance_claim_envelope.governance_plane_claim_process_permitted_now,
        governance_plane_claim_process_summary_line=governance_claim_envelope.governance_plane_claim_process_summary_line,
        governance_plane_claim_operability=primary_work_item.claim_operability,
        governance_plane_claim_operability_summary_line=primary_work_item.claim_operability_summary_line,
        governance_plane_claim_vector=governance_claim_envelope.governance_plane_claim_vector,
        governance_plane_claim_sha256=governance_claim_envelope.governance_plane_claim_sha256,
        governance_plane_queue_key=governance_plane.governance_plane_queue_key,
        governance_plane_route_vector=governance_plane.governance_plane_route_vector,
        governance_plane_route_sha256=governance_plane.governance_plane_route_sha256,
        governance_plane_vector=governance_plane.governance_plane_vector,
        governance_plane_sha256=governance_plane.governance_plane_sha256,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=dominant.regime,
        preferred_strategic_backing_source=(preferred_artifact_evidence.get("manifest_path") if preferred_artifact_evidence is not None else None) and "strategic_artifact_evidence_manifest" or None,
        preferred_strategic_backing_classification=(preferred_artifact_evidence.get("preferred_strategic_backing_classification") if preferred_artifact_evidence is not None else None) or None,
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        exact_evidence_support_score=exact_evidence_support_score,
        regime_confidence=round(dominant.probability, 6),
        regime_probabilities=regime_probabilities,
        epistemic_status=epistemic.status,
        epistemic_score=round(epistemic.score, 6),
        strategy_pressure_score=round(strategy_pressure, 6),
        doctrine_stress_score=round(doctrine_stress, 6),
        opportunity_score=round(opportunity_score, 6),
        caution_score=round(caution_score, 6),
        strategic_posture=posture,
        opportunity_factors=opportunity_factors,
        caution_factors=caution_factors,
        doctrine_pressure_points=doctrine_pressure_points,
        operator_actions=operator_actions,
        summary_line=(
            f"Strategic posture is {posture} under dominant regime {dominant.regime} "
            f"(confidence={dominant.probability:.1%}; caution={caution_score:.1%}; opportunity={opportunity_score:.1%}; "
            f"cadence={exact_cadence_signal_classification}; exact_confirm={cadence.exact_feedback_confirmation_count}; exact_relief={cadence.exact_feedback_relief_count})."
        ),
    )
