from __future__ import annotations

from fastapi import APIRouter, Query
from strategy_validator.api.routes import ui as ui_root
from strategy_validator.application.ui_paper_tracking import (
    build_ui_paper_tracking_detail_payload,
    build_ui_paper_tracking_latest_payload,
)
from strategy_validator.application.ui_paper_broker import build_ui_paper_broker_status_payload
from strategy_validator.application.ui_research_os import build_ui_research_os_status_payload
from strategy_validator.application.ui_strategy_batch import (
    build_ui_strategy_batch_detail_payload,
    build_ui_strategy_batch_latest_payload,
    build_ui_strategy_batch_list_payload,
)

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


@router.get('/strategy-batches/latest')
def get_strategy_batches_latest() -> dict[str, object]:
    return build_ui_strategy_batch_latest_payload()


@router.get('/strategy-batches')
def get_strategy_batches() -> dict[str, object]:
    return build_ui_strategy_batch_list_payload()


@router.get('/strategy-batches/{run_id}')
def get_strategy_batch_by_run(run_id: str) -> dict[str, object]:
    return build_ui_strategy_batch_detail_payload(run_id)


@router.get('/paper-tracking/latest')
def get_paper_tracking_latest() -> dict[str, object]:
    return build_ui_paper_tracking_latest_payload()


@router.get('/paper-tracking/{tracking_id}')
def get_paper_tracking_detail(tracking_id: str) -> dict[str, object]:
    return build_ui_paper_tracking_detail_payload(tracking_id)


@router.get('/paper-broker/status')
def get_paper_broker_status() -> dict[str, object]:
    return build_ui_paper_broker_status_payload()


@router.get('/research-os/status')
def get_research_os_status() -> dict[str, object]:
    return build_ui_research_os_status_payload()
