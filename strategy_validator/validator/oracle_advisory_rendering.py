from __future__ import annotations

from strategy_validator.contracts.oracle import OracleMorningAttestation


def render_oracle_morning_attestation_markdown(attestation: OracleMorningAttestation) -> str:
    regime_lines = "\n".join(
        f"- {item.regime}: {item.probability:.1%} ({'; '.join(item.drivers)})"
        for item in attestation.regime_probabilities
    )
    strategy_lines = "\n".join(
        f"- {item.strategy_id} [{item.strategy_type}] -> {item.action} (posterior={item.posterior_edge_confidence:.1%}; {'; '.join(item.reasons)})"
        for item in attestation.strategy_advisories
    ) or "- No strategy advisories present."
    action_lines = "\n".join(f"- {item}" for item in attestation.operator_actions) or "- none"
    readiness_lines = "\n".join(f"- {item}" for item in attestation.operator_readiness_reasons) or "- none"
    trust_lines = "\n".join(f"- {item}" for item in attestation.support_chain_trust_reasons) or "- none"
    remediation_lines = "\n".join(f"- {item}" for item in attestation.support_chain_remediation_actions) or "- none"
    governance_action_lines = "\n".join(f"- [{item.dimension}/{item.severity}] {item.action_text}" for item in attestation.governance_plane_action_items) or "- none"
    governance_code_lines = "\n".join(f"- {item}" for item in attestation.governance_plane_codes) or "- none"
    governance_blocker_lines = "\n".join(f"- {item}" for item in attestation.governance_plane_blocking_dimensions) or "- none"
    governance_restriction_lines = "\n".join(f"- {item}" for item in attestation.governance_plane_restricted_dimensions) or "- none"
    reliance_lines = "\n".join(f"- {item}" for item in attestation.operator_reliance_reasons) or "- none"
    escalation_lines = "\n".join(f"- {item}" for item in attestation.operator_escalation_reasons) or "- none"
    lineage_lines = "\n".join(
        f"- [{item.artifact_role}] {item.artifact_label} schema={item.schema_version or 'none'} integrity={item.integrity_status} path={item.source_path or 'none'}"
        for item in attestation.artifact_lineage
    ) or "- none"
    return f"""# ORACLE MORNING ATTESTATION

- Generated at UTC: {attestation.generated_at_utc.isoformat()}
- Input timestamp UTC: {attestation.input_timestamp_utc.isoformat()}
- Universe: {attestation.universe_label}
- Oracle policy version: {attestation.oracle_policy_version}
- Oracle policy sha256: {attestation.oracle_policy_sha256 or 'unknown'}
- Operator readiness: {attestation.operator_readiness}
- Support-chain trust: {attestation.support_chain_trust_status}
- Support-chain remediation: {attestation.support_chain_remediation_status}
- {attestation.trust_plane_summary_line}
- Reliance posture: {attestation.operator_reliance_posture}
- Escalation lane: {attestation.operator_escalation_lane}
- Propagation posture: {attestation.propagation_posture}
- Automation posture: {attestation.automation_posture}
- {attestation.control_plane_summary_line}
- {attestation.governance_plane_summary_line}
- Governance primary dimension: {attestation.governance_plane_primary_dimension or 'none'}
- Governance primary severity: {attestation.governance_plane_primary_severity}
- Governance primary action: {attestation.governance_plane_primary_action_text or 'none'}
- Governance priority: {attestation.governance_plane_priority_band} (score={attestation.governance_plane_priority_score})
- {attestation.governance_plane_priority_summary_line}
{attestation.governance_plane_review_summary_line}
- Governance review due by UTC: {attestation.governance_plane_review_due_by_utc.isoformat() if attestation.governance_plane_review_due_by_utc else 'unknown'}
- {attestation.governance_plane_routing_summary_line}
- Governance routing vector: `{attestation.governance_plane_routing_vector}`
- Governance routing sha256: `{attestation.governance_plane_routing_sha256}`
- Governance dispatch posture: {attestation.governance_plane_dispatch_posture}
- Governance dispatch permitted: {attestation.governance_plane_dispatch_permitted}
- Governance dispatch timeliness: {attestation.governance_plane_dispatch_timeliness}
- Governance dispatch claim permitted now: {attestation.governance_plane_dispatch_claim_permitted_now}
- {attestation.governance_plane_dispatch_timeliness_summary_line}
- Governance dispatch claim urgency: {attestation.governance_plane_dispatch_claim_urgency}
- Governance dispatch claim score: {attestation.governance_plane_dispatch_claim_score}
- {attestation.governance_plane_dispatch_claim_summary_line}
- Governance dispatch claim key: `{attestation.governance_plane_dispatch_claim_key}`
- {attestation.governance_plane_claim_summary_line}
- Governance claim review target: `{attestation.governance_plane_claim_review_target}`
- Governance claim priority band: `{attestation.governance_plane_claim_priority_band}`
- Governance claim route sha256: `{attestation.governance_plane_claim_route_sha256}`
- Governance claim review envelope sha256: `{attestation.governance_plane_claim_review_envelope_sha256}`
- Governance claim routing envelope sha256: `{attestation.governance_plane_claim_routing_envelope_sha256}`
- Governance claim dispatch claim key: `{attestation.governance_plane_claim_dispatch_claim_key}`
- Governance claim dispatch sha256: `{attestation.governance_plane_claim_dispatch_sha256}`
- Governance claim codes: `{", ".join(attestation.governance_plane_claim_codes)}`
- Governance claim primary action: {attestation.governance_plane_claim_primary_action_text}
- Governance claim action items: `{", ".join(f"{item.code}:{item.severity}" for item in attestation.governance_plane_claim_action_items)}`
- Governance claim primary code: `{attestation.governance_plane_claim_primary_code or "none"}`
- Governance claim worker lane: `{attestation.governance_plane_claim_worker_lane}`
- Governance claim worker summary: {attestation.governance_plane_claim_worker_summary_line}
- Governance claim worker sort key: `{attestation.governance_plane_claim_worker_sort_key}`
- Governance claim lease key: `{attestation.governance_plane_claim_lease_key}`
- Governance claim lease mode: {attestation.governance_plane_claim_lease_mode}
- Governance claim lease ttl seconds: {attestation.governance_plane_claim_lease_ttl_seconds}
- Governance claim lease expires at utc: {attestation.governance_plane_claim_lease_expires_at_utc.isoformat() if attestation.governance_plane_claim_lease_expires_at_utc else 'none'}
- Governance claim lease active now: {attestation.governance_plane_claim_lease_active_now}
- Governance claim lease coverage: {attestation.governance_plane_claim_lease_coverage}
- {attestation.governance_plane_claim_lease_coverage_summary_line}
- Governance claim lease health: {attestation.governance_plane_claim_lease_health}
- {attestation.governance_plane_claim_lease_health_summary_line}
- Governance claim lease renewal posture: {attestation.governance_plane_claim_lease_renewal_posture}
- Governance claim lease renewal permitted now: {attestation.governance_plane_claim_lease_renewal_permitted_now}
- {attestation.governance_plane_claim_lease_summary_line}
- {attestation.governance_plane_claim_lease_renewal_summary_line}
- Governance claim disposition: {attestation.governance_plane_claim_disposition}
- {attestation.governance_plane_claim_disposition_summary_line}
- Governance claim process posture: `{attestation.governance_plane_claim_process_posture}`
- Governance claim process permitted now: `{attestation.governance_plane_claim_process_permitted_now}`
- {attestation.governance_plane_claim_process_summary_line}
- Governance claim vector: `{attestation.governance_plane_claim_vector}`
- Governance claim sha256: `{attestation.governance_plane_claim_sha256}`
- Governance vector: `{attestation.governance_plane_vector}`
- Governance sha256: `{attestation.governance_plane_sha256}`
- Evidence freshness status: {attestation.evidence_freshness_status}
- Stale artifact count: {attestation.stale_artifact_count}
- Execution authority: {attestation.execution_authority}
- Dominant regime: {attestation.dominant_regime}
- Recommended global action: {attestation.recommended_global_action}

## Summary

{attestation.summary_line}

## Operator readiness

- {attestation.operator_readiness_summary_line}
{readiness_lines}

## Freshness

- {attestation.freshness_summary_line}

## Support-chain trust

- {attestation.support_chain_trust_summary_line}
{trust_lines}

## Support-chain remediation

- {attestation.support_chain_remediation_summary_line}
{remediation_lines}

## Governance dimensions

Codes:
{governance_code_lines}

Blocking dimensions:
{governance_blocker_lines}

Restricted dimensions:
{governance_restriction_lines}

## Governance actions

{governance_action_lines}

## Governance primary driver

- Dimension: {attestation.governance_plane_primary_dimension or 'none'}
- Severity: {attestation.governance_plane_primary_severity}
- Action: {attestation.governance_plane_primary_action_text or 'none'}

## Governance fingerprint

- Vector: `{attestation.governance_plane_vector}`
- SHA-256: `{attestation.governance_plane_sha256}`

## Escalation lane

- {attestation.operator_escalation_summary_line}
{escalation_lines}

## Artifact lineage

- {attestation.artifact_lineage_summary_line}
- {attestation.support_verification_summary_line}
{lineage_lines}

## Regime probabilities

{regime_lines}

## Semantic state

{attestation.semantic_state_summary}

## Microstructure state

{attestation.microstructure_summary}

## Strategy advisories

{strategy_lines}

## Epistemic uncertainty

- Status: {attestation.epistemic_uncertainty.status}
- Score: {attestation.epistemic_uncertainty.score:.1%}
- Advisory only: {attestation.epistemic_uncertainty.advisory_only}
- Triggers: {', '.join(attestation.epistemic_uncertainty.triggers) if attestation.epistemic_uncertainty.triggers else 'none'}

## Operator actions

{action_lines}
"""

