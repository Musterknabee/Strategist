from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Query
from strategy_validator.api.routes.ui_route_queries import (
    build_ui_burnin_query_kwargs,
    build_ui_evidence_query_kwargs,
    build_ui_pack_detail_query_kwargs,
    build_ui_runtime_query_kwargs,
    build_ui_tribunal_query_kwargs,
)
from strategy_validator.application.api_ui_surfaces import (
    build_operator_action_event_index_payload,
    build_ui_evidence_chain_payload,
    build_ui_burnin_payload,
    build_ui_evidence_payload,
    build_ui_pack_detail_payload,
    build_ui_runtime_status_payload,
    build_ui_tribunal_payload,
)
from strategy_validator.application.ui_paper_tracking import (
    build_ui_paper_tracking_detail_payload,
    build_ui_paper_tracking_latest_payload,
)
from strategy_validator.application.ui_paper_broker import build_ui_paper_broker_status_payload
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.application.ui_provider_setup import build_ui_provider_setup_payload
from strategy_validator.application.backtest_forensics_projection import (
    build_ui_backtest_forensics_detail_payload,
    build_ui_backtest_forensics_latest_payload,
)
from strategy_validator.application.strategy_graveyard_projection import build_ui_strategy_graveyard_latest_payload
from strategy_validator.application.daily_operator_run_projection import build_ui_daily_operator_run_payload
from strategy_validator.application.ui_research_os import build_ui_research_os_status_payload
from strategy_validator.application.strategy_memory_ops import build_ui_strategy_memory_latest_payload
from strategy_validator.research.strategy_thesis_eval import build_ui_strategy_thesis_latest_payload
from strategy_validator.research.strategy_thesis_generator import build_ui_strategy_thesis_generation_latest_payload
from strategy_validator.application.shadow_book_ops import build_ui_shadow_book_latest_payload
from strategy_validator.application.strategy_intake import build_ui_strategy_intake_latest_payload
from strategy_validator.application.researcher_cockpit_payload import build_ui_researcher_cockpit_payload
from strategy_validator.application.research_os_closure_ops import build_ui_research_os_closure_latest_payload
from strategy_validator.application.research_os_attestation_ops import build_ui_research_os_attestation_latest_payload
from strategy_validator.application.research_os_briefing_ops import build_ui_research_os_briefing_latest_payload
from strategy_validator.application.research_os_export_ops import build_ui_research_os_export_latest_payload
from strategy_validator.application.research_os_operator_run_ops import build_ui_research_os_operator_run_latest_payload
from strategy_validator.application.research_os_evidence_catalog_ops import build_ui_research_os_evidence_catalog_latest_payload
from strategy_validator.application.research_os_drift_ops import build_ui_research_os_evidence_drift_latest_payload
from strategy_validator.application.research_os_policy_gate_ops import build_ui_research_os_policy_gate_latest_payload
from strategy_validator.application.research_os_exception_ops import build_ui_research_os_exception_latest_payload
from strategy_validator.application.research_os_remediation_ops import build_ui_research_os_remediation_latest_payload
from strategy_validator.application.research_os_release_readiness_ops import build_ui_research_os_release_readiness_latest_payload
from strategy_validator.application.research_os_handoff_ops import build_ui_research_os_handoff_latest_payload
from strategy_validator.application.research_os_handoff_signoff_ops import build_ui_research_os_handoff_signoff_latest_payload
from strategy_validator.application.research_os_review_journal_ops import build_ui_research_os_review_journal_latest_payload
from strategy_validator.application.ui_strategy_batch import (
    build_ui_strategy_batch_detail_payload,
    build_ui_strategy_batch_latest_payload,
    build_ui_strategy_batch_list_payload,
)

router = APIRouter()


@router.get('/burnin')
def get_ui_burnin(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(**build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/burnin/forensic')
def get_ui_burnin_forensic(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(**build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/burnin/providers')
def get_ui_burnin_providers(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
    return build_ui_burnin_payload(**build_ui_burnin_query_kwargs(artifact_path=artifact_path))


@router.get('/runtime')
def get_ui_runtime(role: str = 'operator') -> dict[str, object]:
    return build_ui_runtime_status_payload(**build_ui_runtime_query_kwargs(role=role))


@router.get('/evidence')
def get_ui_evidence(
    repo_root: str | None = None,
    search_root: str | None = None,
) -> dict[str, object]:
    return build_ui_evidence_payload(**build_ui_evidence_query_kwargs(
        repo_root=repo_root,
        search_root=search_root,
    ))


@router.get('/tribunal')
def get_ui_tribunal() -> dict[str, object]:
    return build_ui_tribunal_payload(**build_ui_tribunal_query_kwargs())


@router.get('/packs/detail')
def get_ui_pack_detail(
    search_root: str | None = None,
    board_label: str = 'operator',
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, object]:
    return build_ui_pack_detail_payload(**build_ui_pack_detail_query_kwargs(
        search_root=search_root,
        board_label=board_label,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
    ))


@router.get('/daily-operator-run')
def get_daily_operator_run(
    repo_root: str | None = None,
    database_path: str | None = None,
) -> dict[str, object]:
    return build_ui_daily_operator_run_payload(repo_root=Path(repo_root) if repo_root else None, database_path=database_path)


@router.get('/daily-operator-run/latest')
def get_daily_operator_run_latest(
    repo_root: str | None = None,
    database_path: str | None = None,
) -> dict[str, object]:
    return build_ui_daily_operator_run_payload(repo_root=Path(repo_root) if repo_root else None, database_path=database_path)


@router.get('/operator-actions')
def get_ui_operator_actions(
    database_path: str | None = None,
    readonly: bool = True,
) -> dict[str, object]:
    return build_operator_action_event_index_payload(database_path=database_path, readonly=readonly)


@router.get('/evidence-chain')
def get_ui_evidence_chain(
    database_path: str | None = None,
    readonly: bool = True,
    limit: int = 200,
) -> dict[str, object]:
    return build_ui_evidence_chain_payload(database_path=database_path, readonly=readonly, limit=limit)



@router.get('/backtest-forensics/latest')
def get_backtest_forensics_latest() -> dict[str, object]:
    return build_ui_backtest_forensics_latest_payload()


@router.get('/backtest-forensics')
def get_backtest_forensics() -> dict[str, object]:
    return build_ui_backtest_forensics_latest_payload()


@router.get('/backtest-forensics/{run_id}')
def get_backtest_forensics_by_run(run_id: str) -> dict[str, object]:
    return build_ui_backtest_forensics_detail_payload(run_id)


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


@router.get('/paper-execution')
def get_paper_execution() -> dict[str, object]:
    return build_ui_paper_execution_cockpit_payload()


@router.get('/paper-execution/latest')
def get_paper_execution_latest() -> dict[str, object]:
    return build_ui_paper_execution_cockpit_payload()


@router.get('/provider-setup')
def get_provider_setup() -> dict[str, object]:
    return build_ui_provider_setup_payload()



@router.get('/strategy-memory/latest')
def get_strategy_memory_latest() -> dict[str, object]:
    return build_ui_strategy_memory_latest_payload()


@router.get('/strategy-graveyard/latest')
def get_strategy_graveyard_latest() -> dict[str, object]:
    return build_ui_strategy_graveyard_latest_payload()


@router.get('/strategy-graveyard')
def get_strategy_graveyard() -> dict[str, object]:
    return build_ui_strategy_graveyard_latest_payload()


@router.get('/strategy-thesis/latest')
def get_strategy_thesis_latest() -> dict[str, object]:
    return build_ui_strategy_thesis_latest_payload()


@router.get('/strategy-thesis/generation/latest')
def get_strategy_thesis_generation_latest() -> dict[str, object]:
    return build_ui_strategy_thesis_generation_latest_payload()


@router.get('/shadow-book/latest')
def get_shadow_book_latest() -> dict[str, object]:
    return build_ui_shadow_book_latest_payload()


@router.get('/strategy-intake/latest')
def get_strategy_intake_latest() -> dict[str, object]:
    return build_ui_strategy_intake_latest_payload()


@router.get('/researcher/latest')
def get_researcher_cockpit_latest(artifact_root: str | None = None) -> dict[str, object]:
    return build_ui_researcher_cockpit_payload(artifact_root=artifact_root)


@router.get('/research-os/closure/latest')
def get_research_os_closure_latest() -> dict[str, object]:
    return build_ui_research_os_closure_latest_payload()


@router.get('/research-os/attestation/latest')
def get_research_os_attestation_latest() -> dict[str, object]:
    return build_ui_research_os_attestation_latest_payload()


@router.get('/research-os/briefing/latest')
def get_research_os_briefing_latest() -> dict[str, object]:
    return build_ui_research_os_briefing_latest_payload()


@router.get('/research-os/export/latest')
def get_research_os_export_latest() -> dict[str, object]:
    return build_ui_research_os_export_latest_payload()


@router.get('/research-os/run/latest')
def get_research_os_operator_run_latest() -> dict[str, object]:
    return build_ui_research_os_operator_run_latest_payload()


@router.get('/research-os/catalog/latest')
def get_research_os_evidence_catalog_latest() -> dict[str, object]:
    return build_ui_research_os_evidence_catalog_latest_payload()


@router.get('/research-os/drift/latest')
def get_research_os_evidence_drift_latest() -> dict[str, object]:
    return build_ui_research_os_evidence_drift_latest_payload()


@router.get('/research-os/policy-gate/latest')
def get_research_os_policy_gate_latest() -> dict[str, object]:
    return build_ui_research_os_policy_gate_latest_payload()


@router.get('/research-os/exceptions/latest')
def get_research_os_exception_latest() -> dict[str, object]:
    return build_ui_research_os_exception_latest_payload()


@router.get('/research-os/remediation/latest')
def get_research_os_remediation_latest() -> dict[str, object]:
    return build_ui_research_os_remediation_latest_payload()



@router.get('/research-os/release-readiness/latest')
def get_research_os_release_readiness_latest() -> dict[str, object]:
    return build_ui_research_os_release_readiness_latest_payload()



@router.get('/research-os/handoff/latest')
def get_research_os_handoff_latest() -> dict[str, object]:
    return build_ui_research_os_handoff_latest_payload()

@router.get('/research-os/handoff-signoff/latest')
def get_research_os_handoff_signoff_latest() -> dict[str, object]:
    return build_ui_research_os_handoff_signoff_latest_payload()


@router.get('/research-os/review-journal/latest')
def get_research_os_review_journal_latest() -> dict[str, object]:
    return build_ui_research_os_review_journal_latest_payload()

@router.get('/research-os/status')
def get_research_os_status() -> dict[str, object]:
    return build_ui_research_os_status_payload()
