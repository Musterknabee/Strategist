"""Semantic adjudication bundle release-preflight/index routes."""

from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.research_release_common import *  # noqa: F403

router = APIRouter()

class SemanticAdjudicationBundleVerificationRequest(BaseModel):
    bundle: dict[str, Any]
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleManifestRequest(BaseModel):
    bundle: dict[str, Any]
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleManifestVerificationRequest(BaseModel):
    manifest: dict[str, Any]
    bundle: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleReleasePreflightRequest(BaseModel):
    bundle: dict[str, Any]
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/summary")
def semantic_adjudication_bundle_summary(
    request: SemanticAdjudicationBundleVerificationRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)
    return summary.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/manifest")
def semantic_adjudication_bundle_manifest(request: SemanticAdjudicationBundleManifestRequest) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    return manifest.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/manifest/verify")
def semantic_adjudication_bundle_manifest_verify(
    request: SemanticAdjudicationBundleManifestVerificationRequest,
) -> dict[str, object]:
    manifest = SemanticAdjudicationBundleManifest.model_validate(request.manifest)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_bundle_manifest(manifest, bundle=bundle, proposal=proposal)
    return report.model_dump(mode="json")


class SemanticAdjudicationBundleReleaseIndexRequest(BaseModel):
    bundle: dict[str, Any]
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


class SemanticAdjudicationBundleReleaseIndexVerificationRequest(BaseModel):
    index: dict[str, Any]
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/release-preflight")
def semantic_adjudication_bundle_release_preflight(
    request: SemanticAdjudicationBundleReleasePreflightRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = build_semantic_adjudication_bundle_release_preflight(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-index")
def semantic_adjudication_bundle_release_index(
    request: SemanticAdjudicationBundleReleaseIndexRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    index = build_semantic_adjudication_bundle_release_index(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return index.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-index/verify")
def semantic_adjudication_bundle_release_index_verify(
    request: SemanticAdjudicationBundleReleaseIndexVerificationRequest,
) -> dict[str, object]:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_bundle_release_index(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")
