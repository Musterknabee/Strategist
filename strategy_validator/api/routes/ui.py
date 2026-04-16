from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query

from strategy_validator.api.auth import require_mutation_auth

from strategy_validator.application import (
    build_ui_burnin_payload,
    build_ui_evidence_payload,
    build_ui_operator_command_receipt_payload,
    build_ui_pack_detail_payload,
    build_ui_tribunal_payload,
    build_ui_workboard_payload,
    build_ui_runtime_status_payload,
)

router = APIRouter(prefix='/ui', tags=['ui'])


class UiCommandRequest(BaseModel):
    operator_id: str = 'operator'
    work_item_key: str | None = None
    review_target: str | None = None
    pack_kind: str | None = None
    manifest_path: str | None = None


@router.get('/health')
def ui_health() -> dict[str, object]:
    return {
        'ok': True,
        'surface': 'ui',
        'entrypoints': [
            build_ui_workboard_payload.__name__,
            build_ui_burnin_payload.__name__,
            build_ui_evidence_payload.__name__,
            build_ui_pack_detail_payload.__name__,
            build_ui_tribunal_payload.__name__,
            build_ui_operator_command_receipt_payload.__name__,
            build_ui_runtime_status_payload.__name__,
        ],
    }


@router.get('/workboard')
def get_ui_workboard(
    board_label: str = 'operator',
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
) -> dict[str, object]:
    return build_ui_workboard_payload(
        board_label=board_label,
        search_root=search_root,
        pack_kinds=pack_kind,
        trust_statuses=trust_status,
    )


@router.get('/burnin')
def get_ui_burnin(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(artifact_paths=artifact_path)




@router.get('/burnin/forensic')
def get_ui_burnin_forensic(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(artifact_paths=artifact_path)


@router.get('/burnin/providers')
def get_ui_burnin_providers(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(artifact_paths=artifact_path)

@router.get('/runtime')
def get_ui_runtime(role: str = 'operator') -> dict[str, object]:
    return build_ui_runtime_status_payload(role=role)






@router.get('/evidence')
def get_ui_evidence(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_evidence_payload(repo_root=repo_root, search_root=search_root)


@router.get('/tribunal')
def get_ui_tribunal() -> dict[str, object]:
    return build_ui_tribunal_payload()


@router.get('/packs/detail')
def get_ui_pack_detail(
    search_root: str | None = None,
    board_label: str = 'operator',
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, object]:
    return build_ui_pack_detail_payload(
        search_root=search_root,
        board_label=board_label,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    )


@router.post('/commands/{action}', dependencies=[Depends(require_mutation_auth)])
def post_ui_command(action: str, request: UiCommandRequest) -> dict[str, object]:
    try:
        return build_ui_operator_command_receipt_payload(action=action, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
