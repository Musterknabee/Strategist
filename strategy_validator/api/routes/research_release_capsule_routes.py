"""Semantic adjudication release capsule routes."""

from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.research_release_common import *  # noqa: F403

router = APIRouter()

class SemanticAdjudicationReleaseCapsuleRequest(BaseModel):
    index: dict[str, Any]
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


class SemanticAdjudicationReleaseCapsuleVerificationRequest(BaseModel):
    capsule: dict[str, Any]
    index: dict[str, Any] | None = None
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/release-capsule")
def semantic_adjudication_release_capsule(
    request: SemanticAdjudicationReleaseCapsuleRequest,
) -> dict[str, object]:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    capsule = build_semantic_adjudication_release_capsule(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return capsule.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-capsule/verify")
def semantic_adjudication_release_capsule_verify(
    request: SemanticAdjudicationReleaseCapsuleVerificationRequest,
) -> dict[str, object]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule)
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-capsule/summary")
def summarize_release_capsule_route(
    request: SemanticAdjudicationReleaseCapsuleVerificationRequest,
) -> dict[str, object]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule)
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return summary.model_dump(mode="json")
