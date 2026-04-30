from __future__ import annotations

from collections.abc import Callable
from fastapi import Request, Response


def build_ui_workboard_export_document_response(
    request: Request,
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    include_body: bool,
    build_query_kwargs: Callable[..., dict[str, object]],
    build_document: Callable[..., dict[str, object]],
    build_document_headers: Callable[[dict[str, object]], dict[str, str]],
    build_entity_headers: Callable[..., dict[str, str]],
    build_export_response: Callable[..., Response],
    build_representation_headers: Callable[[dict[str, object]], dict[str, str]],
    build_profile_headers: Callable[[dict[str, object]], dict[str, str]],
    build_location_headers: Callable[[dict[str, object]], dict[str, str]],
    build_disposition_headers: Callable[[dict[str, object]], dict[str, str]],
    build_response_class_headers: Callable[[dict[str, object]], dict[str, str]],
    build_allow_headers: Callable[[], dict[str, str]],
    etag_matches: Callable[[Request, dict[str, str]], bool],
    last_modified_matches: Callable[[Request, dict[str, str]], bool],
) -> Response:
    document = build_document(**build_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))
    headers = build_entity_headers(
        payload=document,
        representation_headers_builder=build_representation_headers,
        profile_headers_builder=build_profile_headers,
        location_headers_builder=build_location_headers,
        disposition_headers_builder=build_disposition_headers,
        response_class_headers_builder=build_response_class_headers,
        allow_headers_builder=build_allow_headers,
        entity_headers=build_document_headers(document),
    )
    return build_export_response(
        request,
        headers=headers,
        include_body=include_body,
        media_type='application/json',
        body=str(document.get('canonical_json') or "{}\n"),
        etag_matches=etag_matches,
        last_modified_matches=last_modified_matches,
    )


def build_ui_workboard_export_index_response(
    request: Request,
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    include_body: bool,
    build_query_kwargs: Callable[..., dict[str, object]],
    build_index: Callable[..., dict[str, object]],
    build_index_headers: Callable[[dict[str, object]], dict[str, str]],
    build_entity_headers: Callable[..., dict[str, str]],
    build_export_response: Callable[..., Response],
    build_representation_headers: Callable[[dict[str, object]], dict[str, str]],
    build_profile_headers: Callable[[dict[str, object]], dict[str, str]],
    build_location_headers: Callable[[dict[str, object]], dict[str, str]],
    build_disposition_headers: Callable[[dict[str, object]], dict[str, str]],
    build_response_class_headers: Callable[[dict[str, object]], dict[str, str]],
    build_allow_headers: Callable[[], dict[str, str]],
    etag_matches: Callable[[Request, dict[str, str]], bool],
    last_modified_matches: Callable[[Request, dict[str, str]], bool],
) -> Response:
    index_payload = build_index(**build_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))
    headers = build_entity_headers(
        payload=index_payload,
        representation_headers_builder=build_representation_headers,
        profile_headers_builder=build_profile_headers,
        location_headers_builder=build_location_headers,
        disposition_headers_builder=build_disposition_headers,
        response_class_headers_builder=build_response_class_headers,
        allow_headers_builder=build_allow_headers,
        entity_headers=build_index_headers(index_payload),
    )
    return build_export_response(
        request,
        headers=headers,
        include_body=include_body,
        media_type='application/json',
        body=index_payload,
        etag_matches=etag_matches,
        last_modified_matches=last_modified_matches,
    )


def build_ui_workboard_export_document_options_response(
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    build_query_kwargs: Callable[..., dict[str, object]],
    build_document: Callable[..., dict[str, object]],
    build_document_headers: Callable[[dict[str, object]], dict[str, str]],
    build_response_class_headers: Callable[[dict[str, object]], dict[str, str]],
    build_options_response: Callable[..., Response],
    build_allow_headers: Callable[[], dict[str, str]],
) -> Response:
    document = build_document(**build_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))
    headers = build_response_class_headers(document)
    headers.update(build_document_headers(document))
    return build_options_response(headers=headers, allow_headers_builder=build_allow_headers)


def build_ui_workboard_export_index_options_response(
    *,
    board_label: str,
    search_root: str | None,
    pack_kind: list[str],
    trust_status: list[str],
    build_query_kwargs: Callable[..., dict[str, object]],
    build_index: Callable[..., dict[str, object]],
    build_index_headers: Callable[[dict[str, object]], dict[str, str]],
    build_response_class_headers: Callable[[dict[str, object]], dict[str, str]],
    build_options_response: Callable[..., Response],
    build_allow_headers: Callable[[], dict[str, str]],
) -> Response:
    index_payload = build_index(**build_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))
    headers = build_response_class_headers(index_payload)
    headers.update(build_index_headers(index_payload))
    return build_options_response(headers=headers, allow_headers_builder=build_allow_headers)
