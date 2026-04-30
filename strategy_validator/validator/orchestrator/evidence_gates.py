"""Evidence gate helpers for the adjudication orchestrator."""

from __future__ import annotations

from typing import Iterable

from strategy_validator.contracts.evidence import Evidence, SemanticArtifact
from strategy_validator.contracts.experiments import ExperimentManifest, GateResult
from strategy_validator.application.research_integrity import (
    build_semantic_research_adjudication_gate_result,
    verify_semantic_release_handoff_certificate_evidence,
    verify_semantic_validator_submission_packet_evidence,
)
from strategy_validator.validator.decoys.battery import evaluate_decoy_survival_hook

def _materialize_decoy_hook(experiment: ExperimentManifest, evidence: Iterable[Evidence]) -> None:
    if experiment.evidence_bundle.decoy_survival_passed is not None: return
    decoy_eval = evaluate_decoy_survival_hook(evidence)
    experiment.evidence_bundle.decoy_survival_passed = decoy_eval.passed
    experiment.evidence_bundle.decoy_suite_version = decoy_eval.suite_version
    experiment.evidence_bundle.decoy_coverage = decoy_eval.coverage


def _semantic_artifacts_missing_spans(semantic_artifacts: Iterable[SemanticArtifact]) -> bool:
    for artifact in semantic_artifacts:
        if not artifact.span_citations: return True
    return False


def _evidence_indicates_future_leakage(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if ev.payload.get("future_leakage_detected") is True or ev.payload.get("pit_violation") is True:
            return True
    return False


def _pit_integrity_ok(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if "pit_integrity_ok" in ev.payload and ev.payload["pit_integrity_ok"] is False: return False
    return True


def _phantom_edge_detected(evidence: Iterable[Evidence]) -> bool:
    for ev in evidence:
        if ev.payload.get("phantom_edge_flag") is True: return True
        raw_edge, cost_edge = ev.payload.get("raw_edge"), ev.payload.get("cost_adjusted_edge")
        if raw_edge is not None and cost_edge is not None:
            if float(raw_edge) > 0.0 and float(cost_edge) <= 0.0: return True
    return False


def _evaluate_semantic_research_integrity(manifest: ExperimentManifest) -> GateResult:
    """Validate attached semantic research materialization evidence, when present."""
    return build_semantic_research_adjudication_gate_result(manifest)


def _evaluate_semantic_release_handoff_certificate_evidence(evidence: Iterable[Evidence]) -> GateResult:
    """Validate optional terminal semantic release handoff certificate evidence.

    This gate is intentionally non-requiring: existing non-semantic and early
    semantic research proposals do not need a release certificate. If a release
    handoff certificate evidence object is present, however, it must verify and
    it must allow validator handoff.
    """
    handoff_evidence = [
        ev for ev in evidence
        if ev.payload.get("schema_version") == "semantic_release_handoff_certificate_evidence/v1"
    ]
    if not handoff_evidence:
        return GateResult(
            gate_name="SemanticReleaseHandoffCertificate",
            passed=True,
            reason="NO_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE",
        )
    issue_codes: list[str] = []
    for ev in handoff_evidence:
        report = verify_semantic_release_handoff_certificate_evidence(ev)
        if not report.verified or not report.handoff_allowed:
            issue_codes.extend(report.issue_codes or ["SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_INVALID"])
    if issue_codes:
        return GateResult(
            gate_name="SemanticReleaseHandoffCertificate",
            passed=False,
            reason=";".join(sorted(set(issue_codes))),
            note=f"{len(handoff_evidence)} semantic release handoff certificate evidence item(s) inspected.",
        )
    return GateResult(
        gate_name="SemanticReleaseHandoffCertificate",
        passed=True,
        note=f"{len(handoff_evidence)} semantic release handoff certificate evidence item(s) verified.",
    )



def _evaluate_semantic_validator_submission_packet_evidence(evidence: Iterable[Evidence]) -> GateResult:
    """Validate optional terminal semantic validator submission-packet Evidence.

    The gate is non-requiring for ordinary proposals. Once submission-packet
    Evidence is supplied, it must verify and it must declare readiness for the
    validator adjudication path. The Evidence remains ordinary Evidence and does
    not bypass any authority boundary.
    """
    submission_evidence = [
        ev for ev in evidence
        if ev.payload.get("schema_version") == "semantic_validator_submission_packet_evidence/v1"
    ]
    if not submission_evidence:
        return GateResult(
            gate_name="SemanticValidatorSubmissionPacketEvidence",
            passed=True,
            reason="NO_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE",
        )
    issue_codes: list[str] = []
    for ev in submission_evidence:
        report = verify_semantic_validator_submission_packet_evidence(ev)
        if not report.verified or not report.ready_for_validator_adjudication:
            issue_codes.extend(report.issue_codes or ["SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_INVALID"])
    if issue_codes:
        return GateResult(
            gate_name="SemanticValidatorSubmissionPacketEvidence",
            passed=False,
            reason=";".join(sorted(set(issue_codes))),
            note=f"{len(submission_evidence)} semantic validator submission-packet Evidence item(s) inspected.",
        )
    return GateResult(
        gate_name="SemanticValidatorSubmissionPacketEvidence",
        passed=True,
        note=f"{len(submission_evidence)} semantic validator submission-packet Evidence item(s) verified.",
    )
