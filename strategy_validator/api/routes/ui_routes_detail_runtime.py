from __future__ import annotations

from fastapi import APIRouter, Query
from strategy_validator.api.routes import ui as ui_root

router = APIRouter()


@router.get('/burnin')
def get_ui_burnin(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return ui_root.build_ui_burnin_payload(**ui_root.build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/burnin/forensic')
def get_ui_burnin_forensic(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return ui_root.build_ui_burnin_payload(**ui_root.build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/burnin/providers')
def get_ui_burnin_providers(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return ui_root.build_ui_burnin_payload(**ui_root.build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/runtime')
def get_ui_runtime(role: str = 'operator') -> dict[str, object]:
    return ui_root.build_ui_runtime_status_payload(**ui_root.build_ui_runtime_query_kwargs(role=role))


@router.get('/evidence')
def get_ui_evidence(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return ui_root.build_ui_evidence_payload(**ui_root.build_ui_evidence_query_kwargs(
        repo_root=repo_root,
        search_root=search_root,
    ))


@router.get('/tribunal')
def get_ui_tribunal() -> dict[str, object]:
    return ui_root.build_ui_tribunal_payload(**ui_root.build_ui_tribunal_query_kwargs())


@router.get('/packs/detail')
def get_ui_pack_detail(
    search_root: str | None = None,
    board_label: str = 'operator',
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, object]:
    return ui_root.build_ui_pack_detail_payload(**ui_root.build_ui_pack_detail_query_kwargs(
        search_root=search_root,
        board_label=board_label,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    ))

@router.get('/operator-actions')
def get_ui_operator_actions(
    database_path: str | None = None,
    readonly: bool = True,
) -> dict[str, object]:
    return ui_root.build_operator_action_event_index_payload(database_path=database_path, readonly=readonly)

