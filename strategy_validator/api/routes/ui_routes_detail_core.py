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


@router.get('/packs/workbench')
def get_ui_pack_workbench(
    search_root: str | None = None,
    pack_kind: list[str] = Query(default=[]),
    trust_status: list[str] = Query(default=[]),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> dict[str, object]:
    return build_operator_pack_workbench_payload(
        search_root=Path(search_root) if search_root else Path.cwd(),
        pack_kinds=tuple(pack_kind),
        trust_statuses=tuple(trust_status),
        summary_line_contains=summary_line_contains,
        output_artifact_label_contains=output_artifact_label_contains,
    )


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


@router.get('/commands/policy')
def get_ui_operator_command_policy(
    action: list[str] = Query(default=[]),
    operator_id: str = 'operator',
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
    idempotency_key: str | None = None,
    assume_token_present: bool = False,
    token_delivery: str = 'authorization',
    principal_id: str | None = None,
    role: str | None = None,
    scope: list[str] = Query(default=[]),
) -> dict[str, object]:
    return build_ui_operator_command_policy_projection(
        actions=tuple(action or ()),
        operator_id=operator_id,
        work_item_key=work_item_key,
        review_target=review_target,
        pack_kind=pack_kind,
        manifest_path=manifest_path,
        idempotency_key=idempotency_key,
        assume_token_present=assume_token_present,
        token_delivery=token_delivery,
        principal_id=principal_id,
        role=role,
        scopes=tuple(scope or ()),
    )


@router.get('/operator-actions')
def get_ui_operator_actions(
    database_path: str | None = None,
    readonly: bool = True,
    operator_id: str | None = None,
    action: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    accepted: bool | None = None,
    control_plane_only: bool = False,
    issue_code: list[str] = Query(default=[]),
    authorization_role: str | None = None,
    review_target: str | None = None,
    work_item_key: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_operator_action_event_index_payload(
        database_path=database_path,
        readonly=readonly,
        operator_id=operator_id,
        action=tuple(action or ()),
        status=tuple(status or ()),
        accepted=accepted,
        control_plane_only=control_plane_only,
        issue_code=tuple(issue_code or ()),
        authorization_role=authorization_role,
        review_target=review_target,
        work_item_key=work_item_key,
        limit=limit,
    )


@router.get('/evidence-chain')
def get_ui_evidence_chain(
    database_path: str | None = None,
    readonly: bool = True,
    stream_family: list[str] = Query(default=[]),
    issue_code: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    actor_contains: str | None = None,
    aggregate_contains: str | None = None,
    event_type_contains: str | None = None,
    chained: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_evidence_chain_payload(
        database_path=database_path,
        readonly=readonly,
        stream_family=tuple(stream_family or ()),
        issue_code=tuple(issue_code or ()),
        status=tuple(status or ()),
        actor_contains=actor_contains,
        aggregate_contains=aggregate_contains,
        event_type_contains=event_type_contains,
        chained=chained,
        limit=limit,
    )


@router.get('/evidence-bundles')
def get_ui_evidence_bundles(
    repo_root: str | None = None,
    artifact_root: str | None = None,
    include_digests: bool = False,
) -> dict[str, object]:
    return build_ui_evidence_bundle_index_payload(
        repo_root=repo_root,
        artifact_root=artifact_root,
        include_digests=include_digests,
    )


@router.get('/backtest-forensics/latest')
def get_backtest_forensics_latest(
    review_posture: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    risk_flag: list[str] = Query(default=[]),
    data_plane: list[str] = Query(default=[]),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_backtest_forensics_latest_payload(
        **_backtest_forensics_query_kwargs(
            review_posture=review_posture,
            status=status,
            risk_flag=risk_flag,
            data_plane=data_plane,
            promotion_eligible=promotion_eligible,
            strategy_id_contains=strategy_id_contains,
            blocker_contains=blocker_contains,
            warning_contains=warning_contains,
            limit=limit,
        )
    )


@router.get('/backtest-forensics')
def get_backtest_forensics(
    review_posture: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    risk_flag: list[str] = Query(default=[]),
    data_plane: list[str] = Query(default=[]),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_backtest_forensics_latest_payload(
        **_backtest_forensics_query_kwargs(
            review_posture=review_posture,
            status=status,
            risk_flag=risk_flag,
            data_plane=data_plane,
            promotion_eligible=promotion_eligible,
            strategy_id_contains=strategy_id_contains,
            blocker_contains=blocker_contains,
            warning_contains=warning_contains,
            limit=limit,
        )
    )


@router.get('/backtest-forensics/{run_id}')
def get_backtest_forensics_by_run(
    run_id: str,
    review_posture: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    risk_flag: list[str] = Query(default=[]),
    data_plane: list[str] = Query(default=[]),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, object]:
    return build_ui_backtest_forensics_detail_payload(
        run_id,
        **_backtest_forensics_query_kwargs(
            review_posture=review_posture,
            status=status,
            risk_flag=risk_flag,
            data_plane=data_plane,
            promotion_eligible=promotion_eligible,
            strategy_id_contains=strategy_id_contains,
            blocker_contains=blocker_contains,
            warning_contains=warning_contains,
            limit=limit,
        )
    )


@router.get('/projection-registry')
def get_projection_registry(
    repo_root: str | None = None,
    search_root: str | None = None,
    projection_family: list[str] = Query(default=[]),
    projection_label: list[str] = Query(default=[]),
    supports_checkpoints: bool | None = None,
    output_label_contains: str | None = None,
    handler_contains: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    include_artifact_entries: bool = False,
) -> dict[str, object]:
    return build_ui_projection_registry_payload(
        repo_root=repo_root,
        search_root=search_root,
        projection_family=tuple(projection_family or ()),
        projection_label=tuple(projection_label or ()),
        supports_checkpoints=supports_checkpoints,
        output_label_contains=output_label_contains,
        handler_contains=handler_contains,
        limit=limit,
        include_artifact_entries=include_artifact_entries,
    )
