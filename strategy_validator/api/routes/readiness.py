from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from strategy_validator.api.auth import require_mutation_auth
from strategy_validator.application.readiness import (
    get_readiness_health_payload,
    publish_release_bundle_from_paths,
)

router = APIRouter(prefix='/readiness', tags=['readiness'])


class PublishReleaseBundleRequest(BaseModel):
    policy_path: str
    keyed_host_fingerprint_path: str
    publication_path: str
    scope: str = 'FULL'
    burnin_artifact_paths: list[str] = Field(default_factory=list)


@router.get('/health')
def readiness_health() -> dict[str, object]:
    return get_readiness_health_payload()


@router.post('/publish-release-bundle', dependencies=[Depends(require_mutation_auth)])
def publish_release_bundle(request: PublishReleaseBundleRequest) -> dict[str, object]:
    return publish_release_bundle_from_paths(
        policy_path=request.policy_path,
        keyed_host_fingerprint_path=request.keyed_host_fingerprint_path,
        burnin_artifact_paths=request.burnin_artifact_paths,
        scope=request.scope,
        publication_path=request.publication_path,
    )
