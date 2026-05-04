from __future__ import annotations

from typing import Any

from strategy_validator.application.research_evidence_bridge import verify_semantic_materialization_evidence
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.contracts.semantic import (
    SemanticResearchAdjudicationGateSummary,
    SemanticResearchIntegrityIssue,
    SemanticResearchIntegrityReport,
)

_SEMANTIC_EVIDENCE_SCHEMA_VERSION = "semantic_research_materialization_evidence/v1"

def _is_semantic_materialization_evidence(evidence: Evidence) -> bool:
    return evidence.payload.get("schema_version") == _SEMANTIC_EVIDENCE_SCHEMA_VERSION


def _semantic_lane_present(proposal: ExperimentManifest) -> bool:
    return bool(proposal.evidence_bundle.semantic_artifacts) or any(
        _is_semantic_materialization_evidence(item) for item in proposal.evidence_bundle.evidence_items
    )


def _pit_key_from_payload(payload: dict[str, Any]) -> tuple[str, str, str, int] | None:
    pit = payload.get("pit_provenance")
    if not isinstance(pit, dict):
        return None
    dataset_id = pit.get("dataset_id")
    decision_time = pit.get("decision_time_utc")
    cutoff = pit.get("available_at_cutoff_utc")
    row_count_after = pit.get("row_count_after")
    if not isinstance(dataset_id, str) or not dataset_id:
        return None
    if decision_time is None or cutoff is None or row_count_after is None:
        return None
    return (dataset_id, str(decision_time), str(cutoff), int(row_count_after))


def _pit_keys_from_data_spine_seal(proposal: ExperimentManifest) -> set[tuple[str, str, str, int]]:
    seal = proposal.evidence_bundle.data_spine_seal
    if seal is None:
        return set()
    keys: set[tuple[str, str, str, int]] = set()
    for item in seal.as_of_provenance:
        payload = item.model_dump(mode="json")
        keys.add(
            (
                str(payload.get("dataset_id")),
                str(payload.get("decision_time_utc")),
                str(payload.get("available_at_cutoff_utc")),
                int(payload.get("row_count_after") or 0),
            )
        )
    return keys


def verify_proposal_semantic_research_integrity(
    proposal: ExperimentManifest,
    *,
    require_semantic_evidence: bool = True,
    require_data_spine_seal: bool = True,
) -> SemanticResearchIntegrityReport:
    """Verify attached semantic research evidence before adjudication.

    This is intentionally read-only and sits outside the orchestrator authority
    path. It checks that every semantic materialization evidence item on a
    proposal is internally deterministic and that its PIT lineage is represented
    in the bundle-level Data Spine seal.
    """
    issues: list[SemanticResearchIntegrityIssue] = []

    def issue(code: str, message: str, *, evidence_id: str | None = None, severity: str = "BLOCKER") -> None:
        issues.append(
            SemanticResearchIntegrityIssue(
                code=code,
                message=message,
                severity=severity,
                evidence_id=evidence_id,
            )
        )

    semantic_evidence = [item for item in proposal.evidence_bundle.evidence_items if _is_semantic_materialization_evidence(item)]
    if require_semantic_evidence and not semantic_evidence:
        issue("SEMANTIC_RESEARCH_EVIDENCE_MISSING", "proposal has no semantic materialization evidence")

    seal_present = proposal.evidence_bundle.data_spine_seal is not None
    if require_data_spine_seal and semantic_evidence and not seal_present:
        issue("SEMANTIC_RESEARCH_DATA_SPINE_SEAL_MISSING", "semantic evidence is present without bundle Data Spine seal")

    seal_keys = _pit_keys_from_data_spine_seal(proposal)
    seen_evidence_ids: set[str] = set()
    for evidence in semantic_evidence:
        if evidence.evidence_id in seen_evidence_ids:
            issue(
                "SEMANTIC_RESEARCH_DUPLICATE_EVIDENCE_ID",
                "duplicate semantic evidence_id attached to proposal",
                evidence_id=evidence.evidence_id,
            )
        seen_evidence_ids.add(evidence.evidence_id)

        verification = verify_semantic_materialization_evidence(evidence, proposal=proposal)
        for verification_issue in verification.issues:
            issue(
                verification_issue.code,
                verification_issue.message,
                evidence_id=evidence.evidence_id,
                severity=verification_issue.severity,
            )

        pit_key = _pit_key_from_payload(evidence.payload)
        if pit_key is None:
            issue(
                "SEMANTIC_RESEARCH_PIT_PROVENANCE_MISSING",
                "semantic evidence lacks complete PIT provenance payload",
                evidence_id=evidence.evidence_id,
            )
        elif require_data_spine_seal and pit_key not in seal_keys:
            issue(
                "SEMANTIC_RESEARCH_DATA_SPINE_SEAL_MISMATCH",
                "semantic evidence PIT provenance is not represented in proposal Data Spine seal",
                evidence_id=evidence.evidence_id,
            )

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticResearchIntegrityReport(
        experiment_id=proposal.experiment_id,
        verified=verified,
        semantic_evidence_count=len(semantic_evidence),
        data_spine_seal_present=seal_present,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="READY_FOR_ADJUDICATION_PREFLIGHT" if verified else "BLOCK_ADJUDICATION_PREFLIGHT",
    )


def summarize_semantic_research_integrity_report(
    report: SemanticResearchIntegrityReport,
) -> dict[str, object]:
    """Return a compact operator/adjudication summary for semantic research integrity."""
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return {
        "schema_version": "semantic_research_integrity_summary/v1",
        "experiment_id": report.experiment_id,
        "verified": report.verified,
        "recommended_action": report.recommended_action,
        "semantic_evidence_count": report.semantic_evidence_count,
        "data_spine_seal_present": report.data_spine_seal_present,
        "blocker_codes": blocker_codes,
        "warning_codes": warning_codes,
        "issue_count": report.issue_count,
    }


def build_semantic_research_adjudication_gate_summary(
    proposal: ExperimentManifest,
    *,
    require_semantic_evidence: bool | None = None,
    require_data_spine_seal: bool | None = None,
) -> SemanticResearchAdjudicationGateSummary:
    """Build the operator-visible summary for the adjudication semantic gate.

    This mirrors the orchestrator's activation law without importing the
    orchestrator. Non-semantic proposals are reported as pass-through; semantic
    proposals must have verified materialization evidence and, when evidence is
    present, a bundle-level Data Spine seal.
    """
    semantic_artifact_count = len(proposal.evidence_bundle.semantic_artifacts)
    semantic_evidence = [item for item in proposal.evidence_bundle.evidence_items if _is_semantic_materialization_evidence(item)]
    semantic_lane_present = bool(semantic_artifact_count or semantic_evidence)
    if not semantic_lane_present:
        return SemanticResearchAdjudicationGateSummary(
            experiment_id=proposal.experiment_id,
            gate_passed=True,
            gate_reason="NO_SEMANTIC_RESEARCH_LANE",
            recommended_action="ALLOW_NON_SEMANTIC_ADJUDICATION",
            semantic_lane_present=False,
            semantic_artifact_count=0,
            semantic_evidence_count=0,
            data_spine_seal_present=proposal.evidence_bundle.data_spine_seal is not None,
            issue_count=0,
        )

    require_evidence = True if require_semantic_evidence is None else require_semantic_evidence
    require_seal = bool(semantic_evidence) if require_data_spine_seal is None else require_data_spine_seal
    report = verify_proposal_semantic_research_integrity(
        proposal,
        require_semantic_evidence=require_evidence,
        require_data_spine_seal=require_seal,
    )
    summary = summarize_semantic_research_integrity_report(report)
    blocker_codes = list(summary["blocker_codes"])
    warning_codes = list(summary["warning_codes"])
    return SemanticResearchAdjudicationGateSummary(
        experiment_id=proposal.experiment_id,
        gate_passed=report.verified,
        gate_reason=None if report.verified else ",".join(blocker_codes or warning_codes),
        recommended_action="ALLOW_ADJUDICATION" if report.verified else "QUARANTINE_BEFORE_ADJUDICATION",
        semantic_lane_present=True,
        semantic_artifact_count=semantic_artifact_count,
        semantic_evidence_count=report.semantic_evidence_count,
        data_spine_seal_present=report.data_spine_seal_present,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_count=report.issue_count,
    )


def build_semantic_research_adjudication_gate_result(
    proposal: ExperimentManifest,
) -> GateResult:
    """Build the same gate shape the orchestrator records, without mutating state."""
    summary = build_semantic_research_adjudication_gate_summary(proposal)
    return GateResult(
        gate_name=summary.gate_name,
        passed=summary.gate_passed,
        reason=summary.gate_reason,
        note=(
            f"{summary.recommended_action}; "
            f"semantic_lane_present={summary.semantic_lane_present}; "
            f"semantic_artifact_count={summary.semantic_artifact_count}; "
            f"semantic_evidence_count={summary.semantic_evidence_count}; "
            f"data_spine_seal_present={summary.data_spine_seal_present}"
        ),
        metric_value=float(summary.semantic_evidence_count),
    )



__all__ = [
    "_is_semantic_materialization_evidence",
    "_semantic_lane_present",
    "verify_proposal_semantic_research_integrity",
    "summarize_semantic_research_integrity_report",
    "build_semantic_research_adjudication_gate_summary",
    "build_semantic_research_adjudication_gate_result",
]
