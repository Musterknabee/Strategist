"""Bounded response builders for UI export routes.

These helpers keep HTTP response/header orchestration out of the transport
module while preserving the existing route-facing service seams.
"""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import Request, Response
from fastapi.responses import JSONResponse


def build_ui_export_options_response(*, headers: Mapping[str, str], allow_headers_builder) -> Response:
    return Response(status_code=204, headers=allow_headers_builder(dict(headers)))


def build_ui_export_entity_headers(
    *,
    payload: Mapping[str, object],
    representation_headers_builder,
    profile_headers_builder,
    location_headers_builder,
    disposition_headers_builder,
    response_class_headers_builder,
    allow_headers_builder,
    entity_headers: Mapping[str, str],
) -> dict[str, str]:
    headers = representation_headers_builder()
    headers.update(profile_headers_builder(payload))
    headers.update(location_headers_builder(payload))
    headers.update(disposition_headers_builder(payload))
    headers.update(response_class_headers_builder(payload))
    headers.update(allow_headers_builder(dict(entity_headers)))
    return _append_export_link_relations(headers)



def build_ui_export_response(
    request: Request,
    *,
    headers: Mapping[str, str],
    include_body: bool,
    media_type: str,
    body: str | Mapping[str, object] | None,
    etag_matches,
    last_modified_matches,
) -> Response:
    not_modified = _build_ui_export_not_modified_response(
        request,
        headers=headers,
        etag_matches=etag_matches,
        last_modified_matches=last_modified_matches,
    )
    if not_modified is not None:
        return not_modified
    if not include_body:
        return Response(media_type=media_type, headers=dict(headers))
    if isinstance(body, Mapping):
        return JSONResponse(content=dict(body), headers=dict(headers))
    return Response(content=body or '', media_type=media_type, headers=dict(headers))



def _build_ui_export_not_modified_response(
    request: Request,
    *,
    headers: Mapping[str, str],
    etag_matches,
    last_modified_matches,
) -> Response | None:
    etag = headers.get('ETag')
    if etag_matches(request.headers.get('if-none-match'), etag):
        return Response(status_code=304, headers=dict(headers))
    last_modified = headers.get('Last-Modified')
    if last_modified_matches(request.headers.get('if-modified-since'), last_modified):
        return Response(status_code=304, headers=dict(headers))
    return None



def _append_export_link_relations(headers: Mapping[str, str]) -> dict[str, str]:
    merged = dict(headers)
    link_value = str(merged.get('Link') or '')
    profile_link = str(merged.get('X-Board-Export-Profile') or '').strip()
    canonical_location = str(merged.get('Content-Location') or '').strip()
    if profile_link and 'rel="profile"' not in link_value:
        link_value = f"{link_value}, <{profile_link}>; rel=\"profile\"" if link_value else f"<{profile_link}>; rel=\"profile\""
    if canonical_location and 'rel="canonical"' not in link_value:
        link_value = f"{link_value}, <{canonical_location}>; rel=\"canonical\"" if link_value else f"<{canonical_location}>; rel=\"canonical\""
    if link_value:
        merged['Link'] = link_value
    return merged
