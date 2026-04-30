from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from strategy_validator.api.research_auth import require_research_api_access
from strategy_validator.api.routes.research_bundle import router as bundle_router
from strategy_validator.api.routes.research_handoff import router as handoff_router
from strategy_validator.api.routes.research_release import router as release_router
from strategy_validator.api.routes.research_submission import router as validator_submission_router
from strategy_validator.application.research_integrity import (
    build_semantic_research_adjudication_gate_summary,
    build_semantic_research_gate_artifact,
    summarize_semantic_research_integrity_report,
    verify_semantic_research_gate_artifact,
    verify_proposal_semantic_research_integrity,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import FeatureFactoryArtifact, SemanticResearchGateArtifact

router = APIRouter(prefix="/research", tags=["research"], dependencies=[Depends(require_research_api_access)])


class SemanticResearchPreflightRequest(BaseModel):
    proposal: dict[str, Any]
    artifact: dict[str, Any]
    published_at: str
    available_at: str
    asset_id: str | None = None
    dataset_id: str = "semantic_tribunal_features/v1"
    attach_to_proposal: bool = Field(default=True)


class SemanticResearchIntegrityRequest(BaseModel):
    proposal: dict[str, Any]
    require_semantic_evidence: bool = True
    require_data_spine_seal: bool = True


class SemanticResearchGateArtifactVerificationRequest(BaseModel):
    artifact: dict[str, Any]
    proposal: dict[str, Any] | None = None


@router.post("/semantic-preflight")
def semantic_research_preflight(request: SemanticResearchPreflightRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    artifact = FeatureFactoryArtifact.model_validate(request.artifact)
    report = run_semantic_research_preflight(
        proposal,
        artifact,
        published_at=request.published_at,
        available_at=request.available_at,
        asset_id=request.asset_id,
        dataset_id=request.dataset_id,
        attach_to_proposal=request.attach_to_proposal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-integrity")
def semantic_research_integrity(request: SemanticResearchIntegrityRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    report = verify_proposal_semantic_research_integrity(
        proposal,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-integrity/summary")
def semantic_research_integrity_summary(request: SemanticResearchIntegrityRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    report = verify_proposal_semantic_research_integrity(
        proposal,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return summarize_semantic_research_integrity_report(report)


@router.post("/semantic-adjudication-gate/summary")
def semantic_research_adjudication_gate_summary(request: SemanticResearchIntegrityRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    summary = build_semantic_research_adjudication_gate_summary(
        proposal,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return summary.model_dump(mode="json")


@router.post("/semantic-adjudication-gate/artifact")
def semantic_research_adjudication_gate_artifact(request: SemanticResearchIntegrityRequest) -> dict[str, object]:
    proposal = ExperimentManifest.model_validate(request.proposal)
    artifact = build_semantic_research_gate_artifact(
        proposal,
        require_semantic_evidence=request.require_semantic_evidence,
        require_data_spine_seal=request.require_data_spine_seal,
    )
    return artifact.model_dump(mode="json")


@router.post("/semantic-adjudication-gate/artifact/verify")
def semantic_research_adjudication_gate_artifact_verify(
    request: SemanticResearchGateArtifactVerificationRequest,
) -> dict[str, object]:
    artifact = SemanticResearchGateArtifact.model_validate(request.artifact)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_research_gate_artifact(artifact, proposal=proposal)
    return report.model_dump(mode="json")


router.include_router(bundle_router)
router.include_router(release_router)
router.include_router(handoff_router)
router.include_router(validator_submission_router)
