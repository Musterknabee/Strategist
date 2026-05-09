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


@router.get('/semantic-validator-handoff/clearance-gate')
def get_semantic_validator_handoff_clearance_gate(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    clearance_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    requires_external_artifact: bool | None = None,
    handoff_clearance_blocked: bool | None = None,
    candidate_for_operator_clearance_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_gate_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, clearance_status=tuple(clearance_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), requires_external_artifact=requires_external_artifact, handoff_clearance_blocked=handoff_clearance_blocked, candidate_for_operator_clearance_review=candidate_for_operator_clearance_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-gate/latest')
def get_semantic_validator_handoff_clearance_gate_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_gate_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-dossier')
def get_semantic_validator_handoff_clearance_dossier(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    review_posture: list[str] = Query(default=[]),
    clearance_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    handoff_clearance_blocked: bool | None = None,
    candidate_for_operator_clearance_review: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_dossier_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, review_posture=tuple(review_posture or ()), clearance_status=tuple(clearance_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), handoff_clearance_blocked=handoff_clearance_blocked, candidate_for_operator_clearance_review=candidate_for_operator_clearance_review, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-dossier/latest')
def get_semantic_validator_handoff_clearance_dossier_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_dossier_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-checklist')
def get_semantic_validator_handoff_clearance_checklist(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    check_id_contains: str | None = None,
    check_state: list[str] = Query(default=[]),
    review_posture: list[str] = Query(default=[]),
    clearance_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    attention_required: bool | None = None,
    blocks_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_checklist_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, check_id_contains=check_id_contains, check_state=tuple(check_state or ()), review_posture=tuple(review_posture or ()), clearance_status=tuple(clearance_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-checklist/latest')
def get_semantic_validator_handoff_clearance_checklist_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_checklist_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-evidence-matrix')
def get_semantic_validator_handoff_clearance_evidence_matrix(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    evidence_state: list[str] = Query(default=[]),
    check_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    attention_required: bool | None = None,
    blocks_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), evidence_state=tuple(evidence_state or ()), check_state=tuple(check_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-evidence-matrix/latest')
def get_semantic_validator_handoff_clearance_evidence_matrix_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-coverage-board')
def get_semantic_validator_handoff_clearance_coverage_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    evidence_state: list[str] = Query(default=[]),
    coverage_status: list[str] = Query(default=[]),
    check_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    attention_required: bool | None = None,
    blocks_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_coverage_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), evidence_state=tuple(evidence_state or ()), coverage_status=tuple(coverage_status or ()), check_state=tuple(check_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), attention_required=attention_required, blocks_clearance=blocks_clearance, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-coverage-board/latest')
def get_semantic_validator_handoff_clearance_coverage_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-operations-board')
def get_semantic_validator_handoff_clearance_operations_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    coverage_status: list[str] = Query(default=[]),
    operation_state: list[str] = Query(default=[]),
    action_group: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    operator_attention_required: bool | None = None,
    handoff_clearance_blocked: bool | None = None,
    requires_external_artifact: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_operations_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), coverage_status=tuple(coverage_status or ()), operation_state=tuple(operation_state or ()), action_group=tuple(action_group or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), operator_attention_required=operator_attention_required, handoff_clearance_blocked=handoff_clearance_blocked, requires_external_artifact=requires_external_artifact, ready_for_operator_clearance_review=ready_for_operator_clearance_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-operations-board/latest')
def get_semantic_validator_handoff_clearance_operations_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-action-register')
def get_semantic_validator_handoff_clearance_action_register(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    action_state: list[str] = Query(default=[]),
    action_type: list[str] = Query(default=[]),
    operation_state: list[str] = Query(default=[]),
    action_group: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    blocked: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_action_register_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), action_state=tuple(action_state or ()), action_type=tuple(action_type or ()), operation_state=tuple(operation_state or ()), action_group=tuple(action_group or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), blocked=blocked, requires_external_artifact=requires_external_artifact, requires_human_review=requires_human_review, ready_for_operator_clearance_review=ready_for_operator_clearance_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-action-register/latest')
def get_semantic_validator_handoff_clearance_action_register_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_action_register_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-resolution-plan')
def get_semantic_validator_handoff_clearance_resolution_plan(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    phase: list[str] = Query(default=[]),
    step_state: list[str] = Query(default=[]),
    action_state: list[str] = Query(default=[]),
    action_type: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    blocks_handoff_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_resolution_plan_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), phase=tuple(phase or ()), step_state=tuple(step_state or ()), action_state=tuple(action_state or ()), action_type=tuple(action_type or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), blocks_handoff_clearance=blocks_handoff_clearance, requires_external_artifact=requires_external_artifact, requires_human_review=requires_human_review, ready_for_operator_clearance_review=ready_for_operator_clearance_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-resolution-plan/latest')
def get_semantic_validator_handoff_clearance_resolution_plan_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-verification-board')
def get_semantic_validator_handoff_clearance_verification_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    verification_status: list[str] = Query(default=[]),
    verification_result: list[str] = Query(default=[]),
    phase: list[str] = Query(default=[]),
    step_state: list[str] = Query(default=[]),
    action_state: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    blocks_handoff_clearance: bool | None = None,
    requires_external_artifact: bool | None = None,
    requires_human_review: bool | None = None,
    ready_for_operator_clearance_review: bool | None = None,
    verification_passed: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_verification_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), verification_status=tuple(verification_status or ()), verification_result=tuple(verification_result or ()), phase=tuple(phase or ()), step_state=tuple(step_state or ()), action_state=tuple(action_state or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), blocks_handoff_clearance=blocks_handoff_clearance, requires_external_artifact=requires_external_artifact, requires_human_review=requires_human_review, ready_for_operator_clearance_review=ready_for_operator_clearance_review, verification_passed=verification_passed, limit=limit)


@router.get('/semantic-validator-handoff/clearance-verification-board/latest')
def get_semantic_validator_handoff_clearance_verification_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-closeout-board')
def get_semantic_validator_handoff_clearance_closeout_board(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    closeout_status: list[str] = Query(default=[]),
    closeout_readiness: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_authorized_clearance_review: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_closeout_board_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), closeout_status=tuple(closeout_status or ()), closeout_readiness=tuple(closeout_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_authorized_clearance_review=ready_for_authorized_clearance_review, blocked=blocked, waiting=waiting, limit=limit)


@router.get('/semantic-validator-handoff/clearance-closeout-board/latest')
def get_semantic_validator_handoff_clearance_closeout_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_closeout_board_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-review-docket')
def get_semantic_validator_handoff_clearance_review_docket(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    docket_status: list[str] = Query(default=[]),
    docket_readiness: list[str] = Query(default=[]),
    closeout_status: list[str] = Query(default=[]),
    closeout_readiness: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_authorized_review: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_authorized_human_review: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_review_docket_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), docket_status=tuple(docket_status or ()), docket_readiness=tuple(docket_readiness or ()), closeout_status=tuple(closeout_status or ()), closeout_readiness=tuple(closeout_readiness or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_authorized_review=ready_for_authorized_review, blocked=blocked, waiting=waiting, requires_authorized_human_review=requires_authorized_human_review, limit=limit)


@router.get('/semantic-validator-handoff/clearance-review-docket/latest')
def get_semantic_validator_handoff_clearance_review_docket_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload(repo_root=repo_root, search_root=search_root)


@router.get('/semantic-validator-handoff/clearance-signoff-packet')
def get_semantic_validator_handoff_clearance_signoff_packet(
    repo_root: str | None = None,
    search_root: str | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    evidence_lane: list[str] = Query(default=[]),
    signoff_status: list[str] = Query(default=[]),
    signoff_readiness: list[str] = Query(default=[]),
    docket_status: list[str] = Query(default=[]),
    docket_readiness: list[str] = Query(default=[]),
    closeout_status: list[str] = Query(default=[]),
    priority: list[str] = Query(default=[]),
    severity: list[str] = Query(default=[]),
    trust_banner: list[str] = Query(default=[]),
    owner_hint: list[str] = Query(default=[]),
    ready_for_human_signoff_observation: bool | None = None,
    blocked: bool | None = None,
    waiting: bool | None = None,
    requires_authorized_review: bool | None = None,
    requires_external_artifact: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_signoff_packet_payload(repo_root=repo_root, search_root=search_root, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, evidence_lane=tuple(evidence_lane or ()), signoff_status=tuple(signoff_status or ()), signoff_readiness=tuple(signoff_readiness or ()), docket_status=tuple(docket_status or ()), docket_readiness=tuple(docket_readiness or ()), closeout_status=tuple(closeout_status or ()), priority=tuple(priority or ()), severity=tuple(severity or ()), trust_banner=tuple(trust_banner or ()), owner_hint=tuple(owner_hint or ()), ready_for_human_signoff_observation=ready_for_human_signoff_observation, blocked=blocked, waiting=waiting, requires_authorized_review=requires_authorized_review, requires_external_artifact=requires_external_artifact, limit=limit)


@router.get('/semantic-validator-handoff/clearance-signoff-packet/latest')
def get_semantic_validator_handoff_clearance_signoff_packet_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
    return build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload(repo_root=repo_root, search_root=search_root)
