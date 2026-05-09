from __future__ import annotations

from fastapi import APIRouter, Query

from strategy_validator.api.routes._ui_detail_legacy import legacy_callable


build_ui_semantic_release_handoff_latest_payload = legacy_callable('build_ui_semantic_release_handoff_latest_payload')
build_ui_semantic_release_handoff_payload = legacy_callable('build_ui_semantic_release_handoff_payload')
build_ui_semantic_validator_handoff_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_latest_payload')
build_ui_semantic_validator_handoff_payload = legacy_callable('build_ui_semantic_validator_handoff_payload')

router = APIRouter()

@router.get('/semantic-release')
def get_semantic_release_handoff(
    repo_root: str | None = None,
    search_root: str | None = None,
    artifact_kind: list[str] = Query(default=[]),
    recommended_action: list[str] = Query(default=[]),
    experiment_id_contains: str | None = None,
    bundle_id_contains: str | None = None,
    issue_contains: str | None = None,
    ready_for_adjudication: bool | None = None,
    verified: bool | None = None,
    require_blockers: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_raw: bool = False,
) -> dict[str, object]:
    return build_ui_semantic_release_handoff_payload(
        repo_root=repo_root,
        search_root=search_root,
        artifact_kind=tuple(artifact_kind or ()),
        recommended_action=tuple(recommended_action or ()),
        experiment_id_contains=experiment_id_contains,
        bundle_id_contains=bundle_id_contains,
        issue_contains=issue_contains,
        ready_for_adjudication=ready_for_adjudication,
        verified=verified,
        require_blockers=require_blockers,
        limit=limit,
        include_raw=include_raw,
    )

@router.get('/semantic-release/latest')
def get_semantic_release_handoff_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_release_handoff_latest_payload(repo_root=repo_root, search_root=search_root)

@router.get('/semantic-validator-handoff')
def get_semantic_validator_handoff(
    repo_root: str | None = None,
    search_root: str | None = None,
    artifact_kind: list[str] = Query(default=[]),
    recommended_action: list[str] = Query(default=[]),
    experiment_id_contains: str | None = None,
    certificate_id_contains: str | None = None,
    packet_id_contains: str | None = None,
    issue_contains: str | None = None,
    handoff_allowed: bool | None = None,
    verified: bool | None = None,
    ready_for_validator_ingress: bool | None = None,
    require_blockers: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_raw: bool = False,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_payload(
        repo_root=repo_root,
        search_root=search_root,
        artifact_kind=tuple(artifact_kind or ()),
        recommended_action=tuple(recommended_action or ()),
        experiment_id_contains=experiment_id_contains,
        certificate_id_contains=certificate_id_contains,
        packet_id_contains=packet_id_contains,
        issue_contains=issue_contains,
        handoff_allowed=handoff_allowed,
        verified=verified,
        ready_for_validator_ingress=ready_for_validator_ingress,
        require_blockers=require_blockers,
        limit=limit,
        include_raw=include_raw,
    )

@router.get('/semantic-validator-handoff/latest')
def get_semantic_validator_handoff_latest(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_latest_payload(repo_root=repo_root, search_root=search_root)

__all__ = (
    'router',
    'get_semantic_release_handoff',
    'get_semantic_release_handoff_latest',
    'get_semantic_validator_handoff',
    'get_semantic_validator_handoff_latest',
)
