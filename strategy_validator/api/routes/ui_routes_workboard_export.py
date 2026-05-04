from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response
from strategy_validator.api.routes import ui as ui_root

router = APIRouter()


@router.get('/health')
def ui_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'ui',
        'entrypoints': [
            ui_root.build_ui_workboard_payload.__name__,
            ui_root.build_ui_workboard_export_payload.__name__,
            ui_root.build_ui_workboard_export_document.__name__,
            ui_root.build_ui_workboard_export_index.__name__,
            ui_root.build_ui_burnin_payload.__name__,
            ui_root.build_ui_evidence_payload.__name__,
            ui_root.build_ui_pack_detail_payload.__name__,
            ui_root.build_ui_tribunal_payload.__name__,
            ui_root.execute_ui_operator_command.__name__,
            ui_root.build_ui_runtime_status_payload.__name__,
        ],
    }


@router.get('/workboard')
def get_ui_workboard(
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> dict[str, object]:
    return ui_root.build_ui_workboard_payload(**ui_root.build_ui_workboard_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))


@router.get('/workboard/export')
def get_ui_workboard_export(
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> dict[str, object]:
    return ui_root.build_ui_workboard_export_payload(**ui_root.build_ui_workboard_query_kwargs(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    ))


@router.get('/workboard/export/document')
def get_ui_workboard_export_document(
    request: Request,
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_document_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=True,
    )


@router.head('/workboard/export/document')
def head_ui_workboard_export_document(
    request: Request,
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_document_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=False,
    )


@router.get('/workboard/export/index')
def get_ui_workboard_export_index(
    request: Request,
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_index_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=True,
    )


@router.head('/workboard/export/index')
def head_ui_workboard_export_index(
    request: Request,
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_index_response(
        request,
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
        include_body=False,
    )


@router.options('/workboard/export/document')
def options_ui_workboard_export_document(
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_document_options_response(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    )


@router.options('/workboard/export/index')
def options_ui_workboard_export_index(
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> Response:
    return ui_root.build_ui_workboard_export_index_options_response(
        board_label=board_label,
        search_root=search_root,
        pack_kind=pack_kind,
        trust_status=trust_status,
    )
