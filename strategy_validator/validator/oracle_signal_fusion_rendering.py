from __future__ import annotations

from strategy_validator.contracts.oracle import OracleStrategicFusionReport


def render_oracle_strategic_fusion_markdown(report: OracleStrategicFusionReport) -> str:
    regime_lines = "\n".join(
        f"- {item.regime}: {item.probability:.1%} ({'; '.join(item.drivers)})"
        for item in report.regime_probabilities
    ) or "- none"
    readiness_lines = "\n".join(f"- {item}" for item in report.operator_readiness_reasons) or "- none"
    trust_lines = "\n".join(f"- {item}" for item in report.support_chain_trust_reasons) or "- none"
    remediation_lines = "\n".join(f"- {item}" for item in report.support_chain_remediation_actions) or "- none"
    governance_action_lines = "\n".join(f"- [{item.dimension}/{item.severity}] {item.action_text}" for item in report.governance_plane_action_items) or "- none"
    governance_code_lines = "\n".join(f"- {item}" for item in report.governance_plane_codes) or "- none"
    governance_blocker_lines = "\n".join(f"- {item}" for item in report.governance_plane_blocking_dimensions) or "- none"
    governance_restriction_lines = "\n".join(f"- {item}" for item in report.governance_plane_restricted_dimensions) or "- none"
    reliance_lines = "\n".join(f"- {item}" for item in report.operator_reliance_reasons) or "- none"
    escalation_lines = "\n".join(f"- {item}" for item in report.operator_escalation_reasons) or "- none"
    action_lines = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    lineage_lines = "\n".join(
        f"- [{item.artifact_role}] {item.artifact_label} schema={item.schema_version or 'none'} integrity={item.integrity_status} path={item.source_path or 'none'}"
        for item in report.artifact_lineage
    ) or "- none"
    return f"""# ORACLE STRATEGIC FUSION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Oracle policy version: {report.oracle_policy_version}
- Oracle policy sha256: {report.oracle_policy_sha256 or 'unknown'}
- Operator readiness: {report.operator_readiness}
- Support-chain trust: {report.support_chain_trust_status}
- Support-chain remediation: {report.support_chain_remediation_status}
- {report.trust_plane_summary_line}
- Reliance posture: {report.operator_reliance_posture}
- Escalation lane: {report.operator_escalation_lane}
- Propagation posture: {report.propagation_posture}
- Automation posture: {report.automation_posture}
- {report.control_plane_summary_line}
- {report.governance_plane_summary_line}
- Governance primary dimension: {report.governance_plane_primary_dimension or 'none'}
- Governance primary severity: {report.governance_plane_primary_severity}
- Governance primary action: {report.governance_plane_primary_action_text or 'none'}
- Governance priority: {report.governance_plane_priority_band} (score={report.governance_plane_priority_score})
- {report.governance_plane_priority_summary_line}
{report.governance_plane_review_summary_line}
- Governance review due by UTC: {report.governance_plane_review_due_by_utc.isoformat() if report.governance_plane_review_due_by_utc else 'unknown'}
- {report.governance_plane_routing_summary_line}
- Governance routing vector: `{report.governance_plane_routing_vector}`
- Governance routing sha256: `{report.governance_plane_routing_sha256}`
- {report.governance_plane_dispatch_summary_line}
- Governance dispatch vector: `{report.governance_plane_dispatch_vector}`
- Governance dispatch sha256: `{report.governance_plane_dispatch_sha256}`
- Governance dispatch claim key: `{report.governance_plane_dispatch_claim_key}`
- Governance dispatch posture: {report.governance_plane_dispatch_posture}
- Governance dispatch permitted: {report.governance_plane_dispatch_permitted}
- Governance dispatch timeliness: {report.governance_plane_dispatch_timeliness}
- Governance dispatch claim permitted now: {report.governance_plane_dispatch_claim_permitted_now}
- {report.governance_plane_dispatch_timeliness_summary_line}
- Governance dispatch claim urgency: {report.governance_plane_dispatch_claim_urgency}
- Governance dispatch claim score: {report.governance_plane_dispatch_claim_score}
- {report.governance_plane_dispatch_claim_summary_line}
- {report.governance_plane_claim_summary_line}
- Governance claim queue key: `{report.governance_plane_claim_queue_key}`
- Governance claim review target: `{report.governance_plane_claim_review_target}`
- Governance claim priority band: `{report.governance_plane_claim_priority_band}`
- Governance claim due by UTC: `{report.governance_plane_claim_review_due_by_utc}`
- Governance claim sort key: `{report.governance_plane_claim_review_sort_key}`
- Governance claim route sha256: `{report.governance_plane_claim_route_sha256}`
- Governance claim review envelope sha256: `{report.governance_plane_claim_review_envelope_sha256}`
- Governance claim routing envelope sha256: `{report.governance_plane_claim_routing_envelope_sha256}`
- Governance claim dispatch claim key: `{report.governance_plane_claim_dispatch_claim_key}`
- Governance claim dispatch sha256: `{report.governance_plane_claim_dispatch_sha256}`
- Governance claim codes: `{", ".join(report.governance_plane_claim_codes)}`
- Governance claim primary action: {report.governance_plane_claim_primary_action_text}
- Governance claim action items: `{", ".join(f"{item.code}:{item.severity}" for item in report.governance_plane_claim_action_items)}`
- Governance claim primary code: `{report.governance_plane_claim_primary_code or "none"}`
- Governance claim worker lane: `{report.governance_plane_claim_worker_lane}`
- Governance claim worker summary: {report.governance_plane_claim_worker_summary_line}
- Governance claim worker sort key: `{report.governance_plane_claim_worker_sort_key}`
- Governance claim lease key: `{report.governance_plane_claim_lease_key}`
- Governance claim lease mode: {report.governance_plane_claim_lease_mode}
- Governance claim lease ttl seconds: {report.governance_plane_claim_lease_ttl_seconds}
- Governance claim lease expires at utc: {report.governance_plane_claim_lease_expires_at_utc.isoformat() if report.governance_plane_claim_lease_expires_at_utc else 'none'}
- Governance claim lease active now: {report.governance_plane_claim_lease_active_now}
- Governance claim lease coverage: {report.governance_plane_claim_lease_coverage}
- {report.governance_plane_claim_lease_coverage_summary_line}
- Governance claim lease health: {report.governance_plane_claim_lease_health}
- {report.governance_plane_claim_lease_health_summary_line}
- Governance claim lease renewal posture: {report.governance_plane_claim_lease_renewal_posture}
- Governance claim lease renewal permitted now: {report.governance_plane_claim_lease_renewal_permitted_now}
- {report.governance_plane_claim_lease_summary_line}
- {report.governance_plane_claim_lease_renewal_summary_line}
- Governance claim disposition: {report.governance_plane_claim_disposition}
- {report.governance_plane_claim_disposition_summary_line}
- Governance claim process posture: `{report.governance_plane_claim_process_posture}`
- Governance claim process permitted now: `{report.governance_plane_claim_process_permitted_now}`
- {report.governance_plane_claim_process_summary_line}
- Governance claim vector: `{report.governance_plane_claim_vector}`
- Governance claim sha256: `{report.governance_plane_claim_sha256}`
- Governance review sort key: `{report.governance_plane_review_sort_key}`
- Governance review envelope vector: `{report.governance_plane_review_envelope_vector}`
- Governance review envelope sha256: `{report.governance_plane_review_envelope_sha256}`
- Governance queue key: `{report.governance_plane_queue_key}`
- Governance route vector: `{report.governance_plane_route_vector}`
- Governance route sha256: `{report.governance_plane_route_sha256}`
- Governance vector: `{report.governance_plane_vector}`
- Governance sha256: `{report.governance_plane_sha256}`
- Evidence freshness status: {report.evidence_freshness_status}
- Stale artifact count: {report.stale_artifact_count}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Epistemic status: {report.epistemic_status}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmation count: {report.exact_feedback_confirmation_count}
- Exact feedback relief count: {report.exact_feedback_relief_count}

## Summary

{report.summary_line}

## Operator readiness

- {report.operator_readiness_summary_line}
{readiness_lines}

## Freshness

- {report.freshness_summary_line}

## Support-chain trust

- {report.support_chain_trust_summary_line}
{trust_lines}

## Support-chain remediation

- {report.support_chain_remediation_summary_line}
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

- Dimension: {report.governance_plane_primary_dimension or 'none'}
- Severity: {report.governance_plane_primary_severity}
- Action: {report.governance_plane_primary_action_text or 'none'}

## Governance fingerprint

- Vector: `{report.governance_plane_vector}`
- SHA-256: `{report.governance_plane_sha256}`

## Escalation lane

- {report.operator_escalation_summary_line}
{escalation_lines}

## Artifact lineage

- {report.artifact_lineage_summary_line}
- {report.support_verification_summary_line}
{lineage_lines}

## Artifact integrity

- {report.integrity_summary_line}

## Artifact coverage

- {report.evidence_coverage_summary_line}
- Missing expected artifacts: {', '.join(report.missing_expected_artifact_labels) if report.missing_expected_artifact_labels else 'none'}

## Regime stack

{regime_lines}

## Scores

- regime_confidence={report.regime_confidence:.2f}
- epistemic_score={report.epistemic_score:.2f}
- strategy_pressure_score={report.strategy_pressure_score:.2f}
- doctrine_stress_score={report.doctrine_stress_score:.2f}
- opportunity_score={report.opportunity_score:.2f}
- caution_score={report.caution_score:.2f}
- exact_evidence_support_score={report.exact_evidence_support_score:.2f}

## Opportunity factors

{'\n'.join(f'- {item}' for item in report.opportunity_factors) or '- none'}

## Caution factors

{'\n'.join(f'- {item}' for item in report.caution_factors) or '- none'}

## Doctrine pressure

{'\n'.join(f'- {item}' for item in report.doctrine_pressure_points) or '- none'}

## Operator actions

{action_lines}
"""
