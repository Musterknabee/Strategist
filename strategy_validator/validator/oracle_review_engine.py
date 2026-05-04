from __future__ import annotations

# Shared contracts, evidence helpers, and low-level oracle transition utilities.
from strategy_validator.validator.oracle_transition_common import *  # noqa: F401,F403
from strategy_validator.validator.oracle_transition_common import (
    _artifact_descriptor,
    _build_regime_transition,
    _build_strategy_transition,
    _epistemic_rank,
    _global_action_rank,
    _json_canonical_bytes,
    _load_attestation,
    _load_manifest,
    _load_transition_report,
    _normalize_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _utc_now,
    _verify_dsse_envelope,
)

from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback

from strategy_validator.validator.oracle_review_rendering import (
    render_oracle_memory_lane_summary_markdown,
    render_oracle_memory_review_markdown,
    render_oracle_state_transition_markdown,
    render_oracle_weekly_digest_markdown,
)


from strategy_validator.validator.oracle_review_evidence import (
    _fallback_weekly_digest_report,
    _load_weekly_digest_report,
    append_oracle_memory_review_to_lane,
    append_oracle_transition_to_lane,
    build_oracle_memory_review_evidence_bundle,
    build_oracle_transition_evidence_bundle,
    build_oracle_weekly_digest_evidence_bundle,
    generate_oracle_weekly_digest,
    review_oracle_memory_lane,
    summarize_oracle_memory_lane,
    verify_oracle_memory_review_evidence_bundle,
    verify_oracle_transition_evidence_bundle,
    verify_oracle_weekly_digest_evidence_bundle,
)

def compare_oracle_evidence(
    *,
    previous_manifest_path: Path,
    current_manifest_path: Path,
    repo_root: Optional[Path] = None,
    previous_dsse_path: Optional[Path] = None,
    current_dsse_path: Optional[Path] = None,
    previous_public_key_path: Optional[Path] = None,
    current_public_key_path: Optional[Path] = None,
    now_utc: Optional[datetime] = None,
) -> OracleStateTransitionReport:
    repo_root = (repo_root or Path.cwd()).resolve()
    previous_manifest_path = previous_manifest_path.resolve()
    current_manifest_path = current_manifest_path.resolve()

    previous_verification = verify_oracle_evidence_bundle(
        manifest_path=previous_manifest_path,
        repo_root=repo_root,
        dsse_path=previous_dsse_path.resolve() if previous_dsse_path else None,
        public_key_path=previous_public_key_path.resolve() if previous_public_key_path else None,
    )
    current_verification = verify_oracle_evidence_bundle(
        manifest_path=current_manifest_path,
        repo_root=repo_root,
        dsse_path=current_dsse_path.resolve() if current_dsse_path else None,
        public_key_path=current_public_key_path.resolve() if current_public_key_path else None,
    )

    previous_manifest = _load_manifest(previous_manifest_path)
    current_manifest = _load_manifest(current_manifest_path)
    previous_attestation = _load_attestation(manifest=previous_manifest, manifest_path=previous_manifest_path, repo_root=repo_root)
    current_attestation = _load_attestation(manifest=current_manifest, manifest_path=current_manifest_path, repo_root=repo_root)

    if previous_attestation.universe_label != current_attestation.universe_label:
        raise ValueError("oracle state transition requires matching universe_label values")
    if previous_attestation.execution_authority != current_attestation.execution_authority:
        raise ValueError("oracle state transition requires matching execution authority")

    comparison_status = "VERIFIED"
    if "INCOMPLETE" in {previous_verification.status, current_verification.status}:
        comparison_status = "INCOMPLETE"
    elif "UNVERIFIED" in {previous_verification.status, current_verification.status}:
        comparison_status = "UNVERIFIED"

    regime_transition = _build_regime_transition(previous_attestation, current_attestation)

    previous_by_id = {item.strategy_id: item for item in previous_attestation.strategy_advisories}
    current_by_id = {item.strategy_id: item for item in current_attestation.strategy_advisories}
    shared_ids = sorted(set(previous_by_id) & set(current_by_id))
    strategy_transitions = [
        _build_strategy_transition(previous_by_id[strategy_id], current_by_id[strategy_id])
        for strategy_id in shared_ids
    ]
    introduced_strategy_ids = sorted(set(current_by_id) - set(previous_by_id))
    removed_strategy_ids = sorted(set(previous_by_id) - set(current_by_id))

    action_escalated = _global_action_rank(current_attestation.recommended_global_action) > _global_action_rank(
        previous_attestation.recommended_global_action
    )
    epistemic_escalated = _epistemic_rank(current_attestation.epistemic_uncertainty.status) > _epistemic_rank(
        previous_attestation.epistemic_uncertainty.status
    )
    severe_strategy_change = any(item.drift_level in {"MATERIAL", "SEVERE"} for item in strategy_transitions)

    drift_score = 0.0
    drift_score += 0.35 if regime_transition.dominant_changed else 0.0
    drift_score += 0.20 if action_escalated else 0.0
    drift_score += 0.20 if epistemic_escalated else 0.0
    drift_score += min(sum(abs(item.posterior_delta) for item in strategy_transitions) * 0.6, 0.20)
    drift_score += min(0.05 * (len(introduced_strategy_ids) + len(removed_strategy_ids)), 0.10)
    drift_score = round(min(drift_score, 1.0), 6)

    transition_classification = "STATE_STABLE"
    if comparison_status != "VERIFIED":
        transition_classification = "EVIDENCE_GAP"
    elif epistemic_escalated and current_attestation.epistemic_uncertainty.status == "UNKNOWN_UNKNOWNS":
        transition_classification = "EPISTEMIC_ESCALATION"
    elif action_escalated:
        transition_classification = "GLOBAL_ACTION_ESCALATION"
    elif regime_transition.dominant_changed:
        transition_classification = "REGIME_DRIFT"
    elif severe_strategy_change or introduced_strategy_ids or removed_strategy_ids:
        transition_classification = "STRATEGY_DRIFT"

    operator_actions = [
        "Treat the transition report as advisory only; it has no execution authority.",
        "Archive the previous and current oracle evidence manifests together with this transition report.",
    ]
    if transition_classification == "EVIDENCE_GAP":
        operator_actions.append("Repair missing or unverified oracle evidence before relying on transition conclusions.")
    elif transition_classification == "EPISTEMIC_ESCALATION":
        operator_actions.append("Escalate to manual review; unknown-unknowns conditions invalidated routine confidence assumptions.")
    elif transition_classification == "GLOBAL_ACTION_ESCALATION":
        operator_actions.append("Review why the advisory global action became more defensive before increasing any risk.")
    elif transition_classification == "REGIME_DRIFT":
        operator_actions.append("Compare the new dominant regime against strategy expected_regimes before changing research priorities.")
    elif transition_classification == "STRATEGY_DRIFT":
        operator_actions.append("Inspect the affected strategies and preserve replay artifacts for posterior-confidence drift review.")

    summary_line = (
        f"Oracle state transition={transition_classification}; previous_action={previous_attestation.recommended_global_action}; "
        f"current_action={current_attestation.recommended_global_action}; previous_epistemic={previous_attestation.epistemic_uncertainty.status}; "
        f"current_epistemic={current_attestation.epistemic_uncertainty.status}; comparison_status={comparison_status}"
    )

    return OracleStateTransitionReport(
        generated_at_utc=now_utc or _utc_now(),
        previous_evidence_id=previous_manifest.evidence_id,
        current_evidence_id=current_manifest.evidence_id,
        universe_label=current_attestation.universe_label,
        execution_authority=current_attestation.execution_authority,
        previous_input_timestamp_utc=previous_attestation.input_timestamp_utc,
        current_input_timestamp_utc=current_attestation.input_timestamp_utc,
        previous_verification_status=previous_verification.status,
        current_verification_status=current_verification.status,
        comparison_status=comparison_status,
        previous_linked_closure_id=previous_manifest.linked_closure_id,
        current_linked_closure_id=current_manifest.linked_closure_id,
        previous_recommended_global_action=previous_attestation.recommended_global_action,
        current_recommended_global_action=current_attestation.recommended_global_action,
        previous_epistemic_status=previous_attestation.epistemic_uncertainty.status,
        current_epistemic_status=current_attestation.epistemic_uncertainty.status,
        regime_transition=regime_transition,
        strategy_transitions=strategy_transitions,
        introduced_strategy_ids=introduced_strategy_ids,
        removed_strategy_ids=removed_strategy_ids,
        transition_classification=transition_classification,
        drift_score=drift_score,
        operator_actions=operator_actions,
        summary_line=summary_line,
    )




