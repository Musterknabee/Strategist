from __future__ import annotations
from strategy_validator.api.routes._lazy_imports import lazy_callable

from fastapi import APIRouter, Query, Request, Response

from strategy_validator.api.auth import require_mutation_auth
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest
from strategy_validator.contracts.strategy_intake import StrategyIntakeRequest
from strategy_validator.api.routes.ui_route_queries import (
    build_ui_burnin_query_kwargs,
    build_ui_evidence_query_kwargs,
    build_ui_pack_detail_query_kwargs,
    build_ui_runtime_query_kwargs,
    build_ui_tribunal_query_kwargs,
    build_ui_workboard_query_kwargs,
)
from strategy_validator.api.routes import ui_route_responses as _ui_route_responses




# Heavy application/read-plane builders are intentionally lazy-loaded so
# importing the FastAPI app does not eagerly import the entire UI surface.
build_ui_burnin_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_burnin_payload')
build_ui_evidence_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_evidence_payload')
execute_ui_operator_command = lazy_callable('strategy_validator.application.api_ui_surfaces', 'execute_ui_operator_command')
build_ui_pack_detail_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_pack_detail_payload')
build_ui_tribunal_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_tribunal_payload')
build_ui_workboard_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_payload')
build_ui_workboard_export_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_payload')
build_ui_workboard_export_document = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_document')
build_ui_workboard_export_document_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_document_headers')
build_ui_workboard_export_allow_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_allow_headers')
build_ui_workboard_export_representation_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_representation_headers')
build_ui_workboard_export_profile_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_profile_headers')
build_ui_workboard_export_location_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_location_headers')
build_ui_workboard_export_disposition_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_disposition_headers')
build_ui_workboard_export_response_class_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_response_class_headers')
build_ui_workboard_export_index_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_index_headers')
export_etag_matches = lazy_callable('strategy_validator.application.api_ui_surfaces', 'export_etag_matches')
export_last_modified_matches = lazy_callable('strategy_validator.application.api_ui_surfaces', 'export_last_modified_matches')
build_ui_export_entity_headers = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_export_entity_headers')
build_ui_export_options_response = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_export_options_response')
build_ui_export_response = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_export_response')
build_ui_workboard_export_index = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_workboard_export_index')
build_ui_runtime_status_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_runtime_status_payload')
build_operator_action_event_index_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_operator_action_event_index_payload')
build_ui_public_facade_inventory = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_public_facade_inventory')
build_ui_provider_health_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_provider_health_payload')
build_ui_research_compute_payload = lazy_callable('strategy_validator.application.api_ui_surfaces', 'build_ui_research_compute_payload')
submit_ui_strategy_intake = lazy_callable('strategy_validator.application.strategy_intake', 'submit_ui_strategy_intake')

router = APIRouter(prefix='/ui', tags=['ui'])


def build_ui_workboard_export_document_response(
    request: Request,
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    include_body: bool,
) -> Response:
    return _ui_route_responses.build_ui_workboard_export_document_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=include_body,
        build_query_kwargs=build_ui_workboard_query_kwargs,
        build_document=build_ui_workboard_export_document,
        build_document_headers=build_ui_workboard_export_document_headers,
        build_entity_headers=build_ui_export_entity_headers,
        build_export_response=build_ui_export_response,
        build_representation_headers=build_ui_workboard_export_representation_headers,
        build_profile_headers=build_ui_workboard_export_profile_headers,
        build_location_headers=build_ui_workboard_export_location_headers,
        build_disposition_headers=build_ui_workboard_export_disposition_headers,
        build_response_class_headers=build_ui_workboard_export_response_class_headers,
        build_allow_headers=build_ui_workboard_export_allow_headers,
        etag_matches=export_etag_matches,
        last_modified_matches=export_last_modified_matches,
    )


def build_ui_workboard_export_index_response(
    request: Request,
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    include_body: bool,
) -> Response:
    return _ui_route_responses.build_ui_workboard_export_index_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=include_body,
        build_query_kwargs=build_ui_workboard_query_kwargs,
        build_index=build_ui_workboard_export_index,
        build_index_headers=build_ui_workboard_export_index_headers,
        build_entity_headers=build_ui_export_entity_headers,
        build_export_response=build_ui_export_response,
        build_representation_headers=build_ui_workboard_export_representation_headers,
        build_profile_headers=build_ui_workboard_export_profile_headers,
        build_location_headers=build_ui_workboard_export_location_headers,
        build_disposition_headers=build_ui_workboard_export_disposition_headers,
        build_response_class_headers=build_ui_workboard_export_response_class_headers,
        build_allow_headers=build_ui_workboard_export_allow_headers,
        etag_matches=export_etag_matches,
        last_modified_matches=export_last_modified_matches,
    )


def build_ui_workboard_export_document_options_response(
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
) -> Response:
    return _ui_route_responses.build_ui_workboard_export_document_options_response(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        build_query_kwargs=build_ui_workboard_query_kwargs,
        build_document=build_ui_workboard_export_document,
        build_document_headers=build_ui_workboard_export_document_headers,
        build_response_class_headers=build_ui_workboard_export_response_class_headers,
        build_options_response=build_ui_export_options_response,
        build_allow_headers=build_ui_workboard_export_allow_headers,
    )


def build_ui_workboard_export_index_options_response(
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
) -> Response:
    return _ui_route_responses.build_ui_workboard_export_index_options_response(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        build_query_kwargs=build_ui_workboard_query_kwargs,
        build_index=build_ui_workboard_export_index,
        build_index_headers=build_ui_workboard_export_index_headers,
        build_response_class_headers=build_ui_workboard_export_response_class_headers,
        build_options_response=build_ui_export_options_response,
        build_allow_headers=build_ui_workboard_export_allow_headers,
    )


@router.get('/facade')
def get_ui_public_facade() -> dict[str, object]:
    return build_ui_public_facade_inventory()


@router.get('/provider-health')
def get_ui_provider_health() -> dict[str, object]:
    return build_ui_provider_health_payload()


@router.get('/research-compute')
def get_ui_research_compute(
    artifact_root: str | None = None,
    backend_used: list[str] = Query(default=[]),
    fallback_reason: list[str] = Query(default=[]),
    strategy_id_contains: str | None = None,
    task_contains: str | None = None,
    warning_contains: str | None = None,
    blocker_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_raw: bool = False,
) -> dict[str, object]:
    return build_ui_research_compute_payload(
        artifact_root=artifact_root,
        backend_used=tuple(backend_used or ()),
        fallback_reason=tuple(fallback_reason or ()),
        strategy_id_contains=strategy_id_contains,
        task_contains=task_contains,
        warning_contains=warning_contains,
        blocker_contains=blocker_contains,
        limit=limit,
        include_raw=include_raw,
    )


from strategy_validator.api.routes.ui_routes_workboard_export import router as workboard_export_router
from strategy_validator.api.routes.ui_routes_detail_runtime import router as detail_runtime_router
from strategy_validator.api.routes.ui_routes_mutation import router as mutation_router
router.include_router(workboard_export_router)
router.include_router(detail_runtime_router)
router.include_router(mutation_router)
