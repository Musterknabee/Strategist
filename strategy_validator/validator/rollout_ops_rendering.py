from __future__ import annotations

from strategy_validator.contracts import (
    ClosureReleaseAttestation,
    ClosureSnapshotManifest,
    ClosureSnapshotVerification,
    GovernedExceptionMemo,
    GovernedExceptionVerification,
)


def render_governed_exception_markdown(*, memo: GovernedExceptionMemo, verification: GovernedExceptionVerification) -> str:
    lines = [
        f"# Governed Exception Memo: {memo.exception_id}",
        "",
        "## Scope",
        f"- **Closure ID**: `{memo.closure_id}`",
        f"- **Environment**: `{memo.scope.environment}`",
        f"- **Provider**: `{memo.scope.provider}`",
        f"- **Symbols**: `{', '.join(memo.scope.symbols) if memo.scope.symbols else 'None'}`",
        f"- **Exception Code**: `{memo.governed_exception_code}`",
        f"- **Verification Status**: `{verification.status}`",
        "",
        "## Approval",
        f"- **Requested By**: `{memo.requested_by}`",
        f"- **Approved By**: `{memo.approved_by}`",
        f"- **Approved At**: `{memo.approved_at_utc.isoformat()}`",
        f"- **Valid Until**: `{memo.valid_until_utc.isoformat()}`",
        "",
        "## Boundary",
        "- This exception preserves the current baseline only for the scoped environment.",
        "- It does not waive runtime failures, evidence-integrity failures, or production validation.",
        "",
        "## Rationale",
        memo.rationale,
        "",
        "## Constraints",
    ]
    lines.extend([f"- {item}" for item in memo.constraints] or ["- No additional constraints recorded."])
    lines.extend(["", "## Evidence Anchors"])
    lines.extend([f"- `{subject.path}` :: `{subject.digest.get('sha256', '')}`" for subject in memo.subjects])
    if verification.notes:
        lines.extend(["", "## Verification Notes"])
        lines.extend([f"- {note}" for note in verification.notes])
    return "\n".join(lines).strip() + "\n"


def render_final_release_signoff_markdown(*, manifest: ClosureSnapshotManifest, verification: ClosureSnapshotVerification, attestation: ClosureReleaseAttestation) -> str:
    lines = [
        f"# Final Release Signoff: {manifest.invariants.interface_freeze_id}",
        "",
        "## Canonical Evidence",
        f"- **Closure ID**: `{manifest.closure_id}`",
        f"- **Snapshot Integrity**: `{verification.status}`",
        f"- **Machine Decision**: `{attestation.machine_decision}`",
        f"- **Primary Classification**: `{attestation.primary_classification}`",
        f"- **Signoff Status**: `{attestation.signoff_status}`",
        f"- **Release Stance**: `{attestation.final_release_stance}`",
        "",
        "## Operational Summary",
        f"- **Startup Check Passed**: `{manifest.operational_summary.startup_check_passed}`",
        f"- **Readiness Status**: `{manifest.operational_summary.readiness_status}`",
        f"- **Provider Availability OK**: `{manifest.operational_summary.provider_availability_ok}`",
        f"- **Freshness Anomaly Count**: `{manifest.operational_summary.freshness_anomaly_count}`",
        f"- **Circuit Open Count**: `{manifest.operational_summary.circuit_open_count}`",
        f"- **Auth / Rate-Limit Count**: `{manifest.operational_summary.auth_rate_limit_count}`",
        f"- **Timeout Count**: `{manifest.operational_summary.timeout_count}`",
        "",
        "## Summary",
        attestation.summary_line,
        "",
        "## Reasons",
    ]
    lines.extend([f"- {reason}" for reason in attestation.reasons] or ["- No additional reasons recorded."])
    lines.extend(["", "## Required Operator Actions"])
    lines.extend([f"- {action}" for action in attestation.required_operator_actions] or ["- No further action required."])
    if attestation.applied_governed_exception_id:
        lines.extend([
            "",
            "## Approved Governed Exception",
            f"- **Exception ID**: `{attestation.applied_governed_exception_id}`",
            f"- **Exception Code**: `{attestation.applied_governed_exception_code}`",
            f"- **Approved By**: `{attestation.applied_governed_exception_approved_by}`",
            f"- **Valid Until**: `{attestation.applied_governed_exception_valid_until_utc.isoformat() if attestation.applied_governed_exception_valid_until_utc else ''}`",
            "- The current baseline is preserved only for the scoped environment and only until the exception expires.",
        ])
    elif attestation.governed_exception_eligible:
        lines.extend([
            "",
            "## Governed Exception Boundary",
            "- A governed exception may preserve the current release baseline only for the scoped environment.",
            "- This does not convert environmental nonconformance into clean release closure or production validation.",
        ])
    return "\n".join(lines).strip() + "\n"


def render_decision_reconciliation_markdown(*, manifest: ClosureSnapshotManifest, verification: ClosureSnapshotVerification, attestation: ClosureReleaseAttestation) -> str:
    lines = [
        "# Decision Reconciliation",
        "",
        "## Machine Facts",
        f"- **Verification Status**: `{verification.status}`",
        f"- **Machine Decision**: `{attestation.machine_decision}`",
        f"- **Primary Classification**: `{attestation.primary_classification}`",
        f"- **Secondary Classifications**: `{', '.join(attestation.secondary_classifications) if attestation.secondary_classifications else 'None'}`",
        f"- **Governed Exception Eligible**: `{attestation.governed_exception_eligible}`",
        f"- **Applied Governed Exception**: `{attestation.applied_governed_exception_id or 'None'}`",
        "",
        "## Canonical Boundary",
        "- Signoff conclusions must be derived from the verified closure snapshot and its referenced review artifact.",
        "- Non-canonical or stale artifact chains must not be used to reinterpret the current release stance.",
        "",
        "## Why this stance follows",
    ]
    lines.extend([f"- {reason}" for reason in attestation.reasons] or ["- No additional reasoning recorded."])
    lines.extend(["", "## Operator next step"])
    lines.extend([f"- {action}" for action in attestation.required_operator_actions] or ["- No operator action required."])
    if attestation.applied_governed_exception_id:
        lines.extend([
            "",
            "## Exception Enforcement Boundary",
            f"- The approved governed exception `{attestation.applied_governed_exception_id}` preserves the current baseline only until `{attestation.applied_governed_exception_valid_until_utc.isoformat() if attestation.applied_governed_exception_valid_until_utc else ''}`.",
            "- The exception must be re-evaluated against a fresh verified closure snapshot before renewal.",
        ])
    if manifest.missing_artifact_paths:
        lines.extend(["", "## Missing artifacts", *[f"- {path}" for path in manifest.missing_artifact_paths]])
    return "\n".join(lines).strip() + "\n"
