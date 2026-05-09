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


@router.get('/semantic-validator-handoff/clearance-acceptance-board')
def get_semantic_validator_handoff_clearance_acceptance_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    acceptance_status: list[str] = Query(default=[]),
    acceptance_readiness: list[str] = Query(default=[]),
    signoff_status: list[str] = Query(default=[]),
    signoff_readiness: list[str] = Query(default=[]),
    docket_status: list[str] = Query(default=[]),
    closeout_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_acceptance_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_authorized_review: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_acceptance_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), signoff_status=tuple(signoff_status or ()), signoff_readiness=tuple(signoff_readiness or ()), docket_status=tuple(docket_status or ()), closeout_status=tuple(closeout_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_acceptance_observation=ready_for_acceptance_observation, blocked=blocked, waiting=waiting, requires_authorized_review=requires_authorized_review, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-acceptance-board/latest')
def get_semantic_validator_handoff_clearance_acceptance_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-readiness-board')
def get_semantic_validator_handoff_clearance_release_readiness_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    release_status: list[str] = Query(default=[]),
    release_readiness: list[str] = Query(default=[]),
    acceptance_status: list[str] = Query(default=[]),
    acceptance_readiness: list[str] = Query(default=[]),
    signoff_status: list[str] = Query(default=[]),
    signoff_readiness: list[str] = Query(default=[]),
    docket_status: list[str] = Query(default=[]),
    closeout_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_release_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_acceptance_observation: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), signoff_status=tuple(signoff_status or ()), signoff_readiness=tuple(signoff_readiness or ()), docket_status=tuple(docket_status or ()), closeout_status=tuple(closeout_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_release_observation=ready_for_release_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-readiness-board/latest')
def get_semantic_validator_handoff_clearance_release_readiness_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-packet')
def get_semantic_validator_handoff_clearance_release_packet(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    release_packet_status: list[str] = Query(default=[]),
    release_packet_readiness: list[str] = Query(default=[]),
    release_status: list[str] = Query(default=[]),
    release_readiness: list[str] = Query(default=[]),
    acceptance_status: list[str] = Query(default=[]),
    acceptance_readiness: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_human_release_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_acceptance_observation: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_packet_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_release_observation=ready_for_human_release_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-packet/latest')
def get_semantic_validator_handoff_clearance_release_packet_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-handoff-board')
def get_semantic_validator_handoff_clearance_release_handoff_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    release_handoff_status: list[str] = Query(default=[]),
    release_handoff_readiness: list[str] = Query(default=[]),
    release_packet_status: list[str] = Query(default=[]),
    release_packet_readiness: list[str] = Query(default=[]),
    release_status: list[str] = Query(default=[]),
    release_readiness: list[str] = Query(default=[]),
    acceptance_status: list[str] = Query(default=[]),
    acceptance_readiness: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_human_transfer_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_acceptance_observation: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_release_packet_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_transfer_observation=ready_for_human_transfer_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_packet_review=requires_release_packet_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-handoff-board/latest')
def get_semantic_validator_handoff_clearance_release_handoff_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-custody-board')
def get_semantic_validator_handoff_clearance_release_custody_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_custody_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_handoff_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_custody_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_custody_observation=ready_for_human_custody_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_handoff_review=requires_release_handoff_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-custody-board/latest')
def get_semantic_validator_handoff_clearance_release_custody_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-receipt-board')
def get_semantic_validator_handoff_clearance_release_receipt_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_receipt_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_custody_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_receipt_observation=ready_for_human_receipt_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_custody_review=requires_release_custody_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-receipt-board/latest')
def get_semantic_validator_handoff_clearance_release_receipt_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_receipt_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board')
def get_semantic_validator_handoff_clearance_release_acknowledgment_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_acknowledgment_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_receipt_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_acknowledgment_observation=ready_for_human_acknowledgment_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_receipt_review=requires_release_receipt_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board/latest')
def get_semantic_validator_handoff_clearance_release_acknowledgment_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-confirmation-board')
def get_semantic_validator_handoff_clearance_release_confirmation_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_confirmation_status: list[str] = Query(default=[]), release_confirmation_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_confirmation_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_acknowledgment_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_confirmation_status=tuple(release_confirmation_status or ()), release_confirmation_readiness=tuple(release_confirmation_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_confirmation_observation=ready_for_human_confirmation_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_acknowledgment_review=requires_release_acknowledgment_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-confirmation-board/latest')
def get_semantic_validator_handoff_clearance_release_confirmation_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_confirmation_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-completion-board')
def get_semantic_validator_handoff_clearance_release_completion_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_confirmation_status: list[str] = Query(default=[]), release_confirmation_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_completion_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_confirmation_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_completion_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_confirmation_status=tuple(release_confirmation_status or ()), release_confirmation_readiness=tuple(release_confirmation_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_completion_observation=ready_for_human_completion_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_confirmation_review=requires_release_confirmation_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-completion-board/latest')
def get_semantic_validator_handoff_clearance_release_completion_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-closure-board')
def get_semantic_validator_handoff_clearance_release_closure_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_closure_status: list[str] = Query(default=[]), release_closure_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_closure_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_completion_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_closure_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_closure_status=tuple(release_closure_status or ()), release_closure_readiness=tuple(release_closure_readiness or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_closure_observation=ready_for_human_closure_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_completion_review=requires_release_completion_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-closure-board/latest')
def get_semantic_validator_handoff_clearance_release_closure_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_closure_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-archive-board')
def get_semantic_validator_handoff_clearance_release_archive_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_archive_status: list[str] = Query(default=[]), release_archive_readiness: list[str] = Query(default=[]), release_closure_status: list[str] = Query(default=[]), release_closure_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_archive_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_closure_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_archive_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_archive_status=tuple(release_archive_status or ()), release_archive_readiness=tuple(release_archive_readiness or ()), release_closure_status=tuple(release_closure_status or ()), release_closure_readiness=tuple(release_closure_readiness or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_archive_observation=ready_for_human_archive_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_closure_review=requires_release_closure_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-archive-board/latest')
def get_semantic_validator_handoff_clearance_release_archive_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_archive_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-retention-board')
def get_semantic_validator_handoff_clearance_release_retention_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_retention_status: list[str] = Query(default=[]), release_retention_readiness: list[str] = Query(default=[]), release_archive_status: list[str] = Query(default=[]), release_archive_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_retention_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_archive_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_retention_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_retention_status=tuple(release_retention_status or ()), release_retention_readiness=tuple(release_retention_readiness or ()), release_archive_status=tuple(release_archive_status or ()), release_archive_readiness=tuple(release_archive_readiness or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_retention_observation=ready_for_human_retention_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_archive_review=requires_release_archive_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-retention-board/latest')
def get_semantic_validator_handoff_clearance_release_retention_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_retention_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-disposition-board')
def get_semantic_validator_handoff_clearance_release_disposition_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_disposition_status: list[str] = Query(default=[]), release_disposition_readiness: list[str] = Query(default=[]), release_retention_status: list[str] = Query(default=[]), release_retention_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_disposition_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_retention_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_disposition_status=tuple(release_disposition_status or ()), release_disposition_readiness=tuple(release_disposition_readiness or ()), release_retention_status=tuple(release_retention_status or ()), release_retention_readiness=tuple(release_retention_readiness or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_disposition_observation=ready_for_human_disposition_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_retention_review=requires_release_retention_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-disposition-board/latest')
def get_semantic_validator_handoff_clearance_release_disposition_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-release-disposal-board')
def get_semantic_validator_handoff_clearance_release_disposal_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_disposal_status: list[str] = Query(default=[]), release_disposal_readiness: list[str] = Query(default=[]), release_disposition_status: list[str] = Query(default=[]), release_disposition_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_disposal_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_disposition_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_disposal_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), release_disposal_status=tuple(release_disposal_status or ()), release_disposal_readiness=tuple(release_disposal_readiness or ()), release_disposition_status=tuple(release_disposition_status or ()), release_disposition_readiness=tuple(release_disposition_readiness or ()), release_completion_status=tuple(release_completion_status or ()), release_completion_readiness=tuple(release_completion_readiness or ()), release_acknowledgment_status=tuple(release_acknowledgment_status or ()), release_acknowledgment_readiness=tuple(release_acknowledgment_readiness or ()), release_receipt_status=tuple(release_receipt_status or ()), release_receipt_readiness=tuple(release_receipt_readiness or ()), release_custody_status=tuple(release_custody_status or ()), release_custody_readiness=tuple(release_custody_readiness or ()), release_handoff_status=tuple(release_handoff_status or ()), release_handoff_readiness=tuple(release_handoff_readiness or ()), release_packet_status=tuple(release_packet_status or ()), release_packet_readiness=tuple(release_packet_readiness or ()), release_status=tuple(release_status or ()), release_readiness=tuple(release_readiness or ()), acceptance_status=tuple(acceptance_status or ()), acceptance_readiness=tuple(acceptance_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_disposal_observation=ready_for_human_disposal_observation, blocked=blocked, waiting=waiting, requires_acceptance_observation=requires_acceptance_observation, requires_external_artifact=requires_external_artifact, requires_release_disposition_review=requires_release_disposition_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-release-disposal-board/latest')
def get_semantic_validator_handoff_clearance_release_disposal_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_release_disposal_board_latest_payload(repo_root=repo_root, search_root=search_root)
