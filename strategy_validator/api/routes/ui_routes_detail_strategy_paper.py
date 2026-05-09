from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Query

from strategy_validator.api.routes._ui_detail_legacy import legacy_callable
from strategy_validator.api.routes.ui_route_queries import (
    build_ui_burnin_query_kwargs,
    build_ui_evidence_query_kwargs,
    build_ui_pack_detail_query_kwargs,
    build_ui_runtime_query_kwargs,
    build_ui_tribunal_query_kwargs,
)

build_operator_action_event_index_payload = legacy_callable('build_operator_action_event_index_payload')
build_operator_pack_workbench_payload = legacy_callable('build_operator_pack_workbench_payload')
build_ui_evidence_chain_payload = legacy_callable('build_ui_evidence_chain_payload')
build_ui_evidence_bundle_index_payload = legacy_callable('build_ui_evidence_bundle_index_payload')
build_ui_burnin_payload = legacy_callable('build_ui_burnin_payload')
build_ui_evidence_payload = legacy_callable('build_ui_evidence_payload')
build_ui_pack_detail_payload = legacy_callable('build_ui_pack_detail_payload')
build_ui_runtime_status_payload = legacy_callable('build_ui_runtime_status_payload')
build_ui_tribunal_payload = legacy_callable('build_ui_tribunal_payload')
build_ui_paper_tracking_detail_payload = legacy_callable('build_ui_paper_tracking_detail_payload')
build_ui_paper_tracking_latest_payload = legacy_callable('build_ui_paper_tracking_latest_payload')
build_ui_paper_broker_status_payload = legacy_callable('build_ui_paper_broker_status_payload')
build_ui_paper_execution_cockpit_payload = legacy_callable('build_ui_paper_execution_cockpit_payload')
build_ui_provider_setup_payload = legacy_callable('build_ui_provider_setup_payload')
build_ui_operator_command_policy_projection = legacy_callable('build_ui_operator_command_policy_projection')
build_ui_backtest_forensics_detail_payload = legacy_callable('build_ui_backtest_forensics_detail_payload')
build_ui_backtest_forensics_latest_payload = legacy_callable('build_ui_backtest_forensics_latest_payload')
build_ui_strategy_graveyard_latest_payload = legacy_callable('build_ui_strategy_graveyard_latest_payload')
build_ui_daily_operator_run_payload = legacy_callable('build_ui_daily_operator_run_payload')
build_ui_research_os_status_payload = legacy_callable('build_ui_research_os_status_payload')
build_ui_strategy_memory_latest_payload = legacy_callable('build_ui_strategy_memory_latest_payload')
build_ui_strategy_thesis_latest_payload = legacy_callable('build_ui_strategy_thesis_latest_payload')
build_ui_strategy_thesis_generation_latest_payload = legacy_callable('build_ui_strategy_thesis_generation_latest_payload')
build_ui_shadow_book_latest_payload = legacy_callable('build_ui_shadow_book_latest_payload')
build_ui_market_data_integrity_payload = legacy_callable('build_ui_market_data_integrity_payload')
build_ui_strategy_intake_latest_payload = legacy_callable('build_ui_strategy_intake_latest_payload')
build_ui_research_os_closure_latest_payload = legacy_callable('build_ui_research_os_closure_latest_payload')
build_ui_research_os_attestation_latest_payload = legacy_callable('build_ui_research_os_attestation_latest_payload')
build_ui_research_os_briefing_latest_payload = legacy_callable('build_ui_research_os_briefing_latest_payload')
build_ui_research_os_export_latest_payload = legacy_callable('build_ui_research_os_export_latest_payload')
build_ui_research_os_operator_run_latest_payload = legacy_callable('build_ui_research_os_operator_run_latest_payload')
build_ui_research_os_evidence_catalog_latest_payload = legacy_callable('build_ui_research_os_evidence_catalog_latest_payload')
build_ui_research_os_evidence_drift_latest_payload = legacy_callable('build_ui_research_os_evidence_drift_latest_payload')
build_ui_research_os_policy_gate_latest_payload = legacy_callable('build_ui_research_os_policy_gate_latest_payload')
build_ui_research_os_exception_latest_payload = legacy_callable('build_ui_research_os_exception_latest_payload')
build_ui_research_os_remediation_latest_payload = legacy_callable('build_ui_research_os_remediation_latest_payload')
build_ui_research_os_release_readiness_latest_payload = legacy_callable('build_ui_research_os_release_readiness_latest_payload')
build_ui_research_os_handoff_latest_payload = legacy_callable('build_ui_research_os_handoff_latest_payload')
build_ui_research_os_handoff_signoff_latest_payload = legacy_callable('build_ui_research_os_handoff_signoff_latest_payload')
build_ui_research_os_review_journal_latest_payload = legacy_callable('build_ui_research_os_review_journal_latest_payload')
build_ui_strategy_batch_detail_payload = legacy_callable('build_ui_strategy_batch_detail_payload')
build_ui_strategy_batch_latest_payload = legacy_callable('build_ui_strategy_batch_latest_payload')
build_ui_strategy_batch_list_payload = legacy_callable('build_ui_strategy_batch_list_payload')
build_ui_promotion_review_latest_payload = legacy_callable('build_ui_promotion_review_latest_payload')
build_ui_promotion_review_payload = legacy_callable('build_ui_promotion_review_payload')
build_ui_projection_registry_payload = legacy_callable('build_ui_projection_registry_payload')
build_ui_semantic_release_handoff_latest_payload = legacy_callable('build_ui_semantic_release_handoff_latest_payload')
build_ui_semantic_release_handoff_payload = legacy_callable('build_ui_semantic_release_handoff_payload')
build_ui_semantic_validator_handoff_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_latest_payload')
build_ui_semantic_validator_handoff_payload = legacy_callable('build_ui_semantic_validator_handoff_payload')
build_ui_semantic_validator_handoff_lineage_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_lineage_latest_payload')
build_ui_semantic_validator_handoff_lineage_payload = legacy_callable('build_ui_semantic_validator_handoff_lineage_payload')
build_ui_semantic_validator_handoff_remediation_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_remediation_latest_payload')
build_ui_semantic_validator_handoff_remediation_payload = legacy_callable('build_ui_semantic_validator_handoff_remediation_payload')
build_ui_semantic_validator_handoff_review_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_review_latest_payload')
build_ui_semantic_validator_handoff_review_payload = legacy_callable('build_ui_semantic_validator_handoff_review_payload')
build_ui_semantic_validator_handoff_decision_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_decision_latest_payload')
build_ui_semantic_validator_handoff_decision_payload = legacy_callable('build_ui_semantic_validator_handoff_decision_payload')
build_ui_semantic_validator_handoff_signoff_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_signoff_latest_payload')
build_ui_semantic_validator_handoff_signoff_payload = legacy_callable('build_ui_semantic_validator_handoff_signoff_payload')
build_ui_semantic_validator_handoff_custody_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_custody_latest_payload')
build_ui_semantic_validator_handoff_custody_payload = legacy_callable('build_ui_semantic_validator_handoff_custody_payload')
build_ui_semantic_validator_handoff_archive_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_archive_latest_payload')
build_ui_semantic_validator_handoff_archive_payload = legacy_callable('build_ui_semantic_validator_handoff_archive_payload')
build_ui_semantic_validator_handoff_closure_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_closure_latest_payload')
build_ui_semantic_validator_handoff_closure_payload = legacy_callable('build_ui_semantic_validator_handoff_closure_payload')
build_ui_semantic_validator_handoff_continuity_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_continuity_latest_payload')
build_ui_semantic_validator_handoff_continuity_payload = legacy_callable('build_ui_semantic_validator_handoff_continuity_payload')
build_ui_semantic_validator_handoff_runbook_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_runbook_latest_payload')
build_ui_semantic_validator_handoff_runbook_payload = legacy_callable('build_ui_semantic_validator_handoff_runbook_payload')
build_ui_semantic_validator_handoff_exceptions_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_exceptions_latest_payload')
build_ui_semantic_validator_handoff_exceptions_payload = legacy_callable('build_ui_semantic_validator_handoff_exceptions_payload')
build_ui_semantic_validator_handoff_timeline_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_timeline_latest_payload')
build_ui_semantic_validator_handoff_timeline_payload = legacy_callable('build_ui_semantic_validator_handoff_timeline_payload')
build_ui_semantic_validator_handoff_evidence_gaps_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_evidence_gaps_latest_payload')
build_ui_semantic_validator_handoff_evidence_gaps_payload = legacy_callable('build_ui_semantic_validator_handoff_evidence_gaps_payload')
build_ui_semantic_validator_handoff_audit_packet_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_audit_packet_latest_payload')
build_ui_semantic_validator_handoff_audit_packet_payload = legacy_callable('build_ui_semantic_validator_handoff_audit_packet_payload')
build_ui_semantic_validator_handoff_action_queue_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_action_queue_latest_payload')
build_ui_semantic_validator_handoff_action_queue_payload = legacy_callable('build_ui_semantic_validator_handoff_action_queue_payload')
build_ui_semantic_validator_handoff_escalation_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_escalation_board_latest_payload')
build_ui_semantic_validator_handoff_escalation_board_payload = legacy_callable('build_ui_semantic_validator_handoff_escalation_board_payload')
build_ui_semantic_validator_handoff_resolution_plan_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_resolution_plan_latest_payload')
build_ui_semantic_validator_handoff_resolution_plan_payload = legacy_callable('build_ui_semantic_validator_handoff_resolution_plan_payload')
build_ui_semantic_validator_handoff_clearance_gate_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_gate_latest_payload')
build_ui_semantic_validator_handoff_clearance_gate_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_gate_payload')
build_ui_semantic_validator_handoff_clearance_dossier_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_dossier_latest_payload')
build_ui_semantic_validator_handoff_clearance_dossier_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_dossier_payload')
build_ui_semantic_validator_handoff_clearance_checklist_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_checklist_latest_payload')
build_ui_semantic_validator_handoff_clearance_checklist_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_checklist_payload')
build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload')
build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload')
build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_coverage_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_coverage_board_payload')
build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_operations_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_operations_board_payload')
build_ui_semantic_validator_handoff_clearance_action_register_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_action_register_latest_payload')
build_ui_semantic_validator_handoff_clearance_action_register_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_action_register_payload')
build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload')
build_ui_semantic_validator_handoff_clearance_resolution_plan_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_resolution_plan_payload')
build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_verification_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_verification_board_payload')
build_ui_semantic_validator_handoff_clearance_closeout_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_closeout_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_closeout_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_closeout_board_payload')
build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload')
build_ui_semantic_validator_handoff_clearance_review_docket_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_review_docket_payload')
build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload')
build_ui_semantic_validator_handoff_clearance_signoff_packet_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_signoff_packet_payload')
build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_acceptance_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_acceptance_board_payload')
build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload')
build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_packet_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_packet_payload')
build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload')
build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_custody_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_custody_board_payload')
build_ui_semantic_validator_handoff_clearance_release_receipt_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_receipt_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload')
build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload')
build_ui_semantic_validator_handoff_clearance_release_confirmation_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_confirmation_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload')
build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_completion_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_completion_board_payload')
build_ui_semantic_validator_handoff_clearance_release_closure_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_closure_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_closure_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_closure_board_payload')
build_ui_semantic_validator_handoff_clearance_release_archive_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_archive_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_archive_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_archive_board_payload')
build_ui_semantic_validator_handoff_clearance_release_retention_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_retention_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_retention_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_retention_board_payload')
build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload')
build_ui_semantic_validator_handoff_clearance_release_disposal_board_latest_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_disposal_board_latest_payload')
build_ui_semantic_validator_handoff_clearance_release_disposal_board_payload = legacy_callable('build_ui_semantic_validator_handoff_clearance_release_disposal_board_payload')

router = APIRouter()


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


@router.get('/market-data-integrity')
def get_market_data_integrity(
    repo_root: str | None = None,
    scan_root: str | None = None,
    gate_status: list[str] = Query(default=[]),
    provider_id: str | None = None,
    adjusted_status: list[str] = Query(default=[]),
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_raw: bool = False,
) -> dict[str, object]:
    return build_ui_market_data_integrity_payload(
        repo_root=repo_root,
        scan_root=scan_root,
        gate_status=tuple(gate_status or ()),
        provider_id=provider_id,
        adjusted_status=tuple(adjusted_status or ()),
        strategy_id_contains=strategy_id_contains,
        blocker_contains=blocker_contains,
        warning_contains=warning_contains,
        limit=limit,
        include_raw=include_raw,
    )


@router.get('/market-data-integrity/latest')
def get_market_data_integrity_latest(
    repo_root: str | None = None,
    scan_root: str | None = None,
) -> dict[str, object]:
    return build_ui_market_data_integrity_payload(repo_root=repo_root, scan_root=scan_root, limit=1)


@router.get('/promotion-review')
def get_promotion_review(
    repo_root: str | None = None,
    paper_tracking_root: str | None = None,
    recommendation: list[str] = Query(default=[]),
    lifecycle_state: list[str] = Query(default=[]),
    tracking_id: str | None = None,
    strategy_id_contains: str | None = None,
    issue_contains: str | None = None,
    require_blockers: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_raw: bool = False,
) -> dict[str, object]:
    return build_ui_promotion_review_payload(
        repo_root=repo_root,
        paper_tracking_root=paper_tracking_root,
        recommendation=tuple(recommendation or ()),
        lifecycle_state=tuple(lifecycle_state or ()),
        tracking_id=tracking_id,
        strategy_id_contains=strategy_id_contains,
        issue_contains=issue_contains,
        require_blockers=require_blockers,
        limit=limit,
        include_raw=include_raw,
    )


@router.get('/promotion-review/latest')
def get_promotion_review_latest(
    repo_root: str | None = None,
    paper_tracking_root: str | None = None,
) -> dict[str, object]:
    return build_ui_promotion_review_latest_payload(repo_root=repo_root, paper_tracking_root=paper_tracking_root)


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
