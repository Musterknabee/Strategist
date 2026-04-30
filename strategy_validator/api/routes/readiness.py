from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from strategy_validator.api.auth import require_mutation_auth
from strategy_validator.application.readiness import (
    get_deployment_readiness_payload,
    get_strategic_horizon_readiness_payload,
    summarize_deployment_readiness_payload,
    get_readiness_health_payload,
    publish_release_bundle_from_paths,
)
from strategy_validator.application.release_publication_paths import resolve_release_publication_paths
from strategy_validator.core.path_guards import PathBoundaryError

router = APIRouter(prefix="/readiness", tags=["readiness"])


class PublishReleaseBundleRequest(BaseModel):
    artifact_root: str = Field(..., description="Explicit trusted root for all release-publication input/output paths")
    policy_path: str
    keyed_host_fingerprint_path: str
    publication_path: str
    scope: str = "FULL"
    burnin_artifact_paths: list[str] = Field(default_factory=list)


@router.get("/health")
def readiness_health() -> dict[str, object]:
    return get_readiness_health_payload()


@router.get("/deployment")
def deployment_readiness() -> dict[str, object]:
    return get_deployment_readiness_payload()


@router.get("/deployment/summary")
def deployment_readiness_summary() -> dict[str, object]:
    return summarize_deployment_readiness_payload()


@router.get("/strategic-horizon")
def strategic_horizon_readiness() -> dict[str, object]:
    return get_strategic_horizon_readiness_payload()


@router.post("/publish-release-bundle", dependencies=[Depends(require_mutation_auth)])
def publish_release_bundle(request: PublishReleaseBundleRequest) -> dict[str, object]:
    try:
        resolved = resolve_release_publication_paths(
            artifact_root=request.artifact_root,
            policy_path=request.policy_path,
            keyed_host_fingerprint_path=request.keyed_host_fingerprint_path,
            publication_path=request.publication_path,
            burnin_artifact_paths=request.burnin_artifact_paths,
        )
    except PathBoundaryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return publish_release_bundle_from_paths(
        policy_path=resolved["policy_path"],
        keyed_host_fingerprint_path=resolved["keyed_host_fingerprint_path"],
        burnin_artifact_paths=list(resolved["burnin_artifact_paths"]),
        scope=request.scope,
        publication_path=resolved["publication_path"],
    )
