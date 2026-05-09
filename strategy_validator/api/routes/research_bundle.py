"""Semantic adjudication bundle/readiness research routes."""

from __future__ import annotations
from strategy_validator.api.routes._lazy_imports import lazy_callable, lazy_model

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel



ExperimentManifest = lazy_model('strategy_validator.contracts.experiments', 'ExperimentManifest')
SemanticAdjudicationBundle = lazy_model('strategy_validator.contracts.semantic', 'SemanticAdjudicationBundle')
SemanticAdjudicationHandoffArtifact = lazy_model('strategy_validator.contracts.semantic', 'SemanticAdjudicationHandoffArtifact')
SemanticResearchGateArtifact = lazy_model('strategy_validator.contracts.semantic', 'SemanticResearchGateArtifact')

# Heavy application/read-plane dependencies are lazy-loaded to keep API import fast.
build_semantic_adjudication_bundle = lazy_callable('strategy_validator.application.research_integrity', 'build_semantic_adjudication_bundle')
build_semantic_adjudication_handoff_artifact = lazy_callable('strategy_validator.application.research_integrity', 'build_semantic_adjudication_handoff_artifact')
build_semantic_adjudication_readiness_report = lazy_callable('strategy_validator.application.research_integrity', 'build_semantic_adjudication_readiness_report')
verify_semantic_adjudication_bundle = lazy_callable('strategy_validator.application.research_integrity', 'verify_semantic_adjudication_bundle')
verify_semantic_adjudication_handoff_artifact = lazy_callable('strategy_validator.application.research_integrity', 'verify_semantic_adjudication_handoff_artifact')

router = APIRouter()


class SemanticAdjudicationReadinessRequest(BaseModel):
    proposal: dict[str, Any]
    gate_artifact: dict[str, Any] | None = None
    require_gate_artifact: bool = False
    require_semantic_evidence: bool | None = None
    require_data_spine_seal: bool | None = None


class SemanticAdjudicationHandoffArtifactVerificationRequest(BaseModel):
    artifact: dict[str, Any]
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleRequest(BaseModel):
    proposal: dict[str, Any]
    gate_artifact: dict[str, Any] | None = None
    handoff_artifact: dict[str, Any] | None = None
    require_gate_artifact: bool = True
    require_semantic_evidence: bool | None = None
    require_data_spine_seal: bool | None = None


class SemanticAdjudicationBundleVerificationRequest(BaseModel):
    bundle: dict[str, Any]
    proposal: dict[str, Any] | None = None


@router.post("/semantic-adjudication-readiness")
def semantic_adjudication_readiness(request: SemanticAdjudicationReadinessRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    gate_artifact = (
        SemanticResearchGateArtifact.model_validate(request.gate_artifact)
        if request.gate_artifact is not None
        else None
    )
    report = build_semantic_adjudication_readiness_report(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=request.require_gate_artifact,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-handoff/artifact")
def semantic_adjudication_handoff_artifact(request: SemanticAdjudicationReadinessRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    gate_artifact = (
        SemanticResearchGateArtifact.model_validate(request.gate_artifact)
        if request.gate_artifact is not None
        else None
    )
    artifact = build_semantic_adjudication_handoff_artifact(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=request.require_gate_artifact,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return artifact.model_dump(mode="json")


@router.post("/semantic-adjudication-handoff/artifact/verify")
def semantic_adjudication_handoff_artifact_verify(
    request: SemanticAdjudicationHandoffArtifactVerificationRequest,
) -> dict[str, object]:
    artifact = SemanticAdjudicationHandoffArtifact.model_validate(request.artifact)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_handoff_artifact(artifact, proposal=proposal)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle")
def semantic_adjudication_bundle(request: SemanticAdjudicationBundleRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    gate_artifact = (
        SemanticResearchGateArtifact.model_validate(request.gate_artifact)
        if request.gate_artifact is not None
        else None
    )
    handoff_artifact = (
        SemanticAdjudicationHandoffArtifact.model_validate(request.handoff_artifact)
        if request.handoff_artifact is not None
        else None
    )
    bundle = build_semantic_adjudication_bundle(
        proposal,
        gate_artifact=gate_artifact,
        handoff_artifact=handoff_artifact,
        require_gate_artifact=request.require_gate_artifact,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return bundle.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/verify")
def semantic_adjudication_bundle_verify(
    request: SemanticAdjudicationBundleVerificationRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_bundle(bundle, proposal=proposal)
    return report.model_dump(mode="json")
