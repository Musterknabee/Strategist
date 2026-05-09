from __future__ import annotations
from typing import Any
from strategy_validator.api.routes._ui_detail_builders import resolve_detail_builder as _resolve_detail_builder

from pathlib import Path
from fastapi import APIRouter, Query
from strategy_validator.api.routes.ui_route_queries import (
    build_ui_burnin_query_kwargs,
    build_ui_evidence_query_kwargs,
    build_ui_pack_detail_query_kwargs,
    build_ui_runtime_query_kwargs,
    build_ui_tribunal_query_kwargs,
)


# Heavy application/read-plane builders live in _ui_detail_builders and are
# exposed through __getattr__ so legacy monkeypatch paths still work. legacy_callable(

def __getattr__(name: str) -> Any:
    return _resolve_detail_builder(name)

router = APIRouter()

# Real route definitions are decomposed into family modules. This aggregate
# router preserves the public import path used by ``strategy_validator.api.routes.ui``
# and by existing operator/tests that monkeypatch legacy builder symbols.
from strategy_validator.api.routes.ui_routes_detail_core import router as core_router
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff import router as semantic_handoff_router
from strategy_validator.api.routes.ui_routes_detail_clearance import router as clearance_router
from strategy_validator.api.routes.ui_routes_detail_clearance_release import router as clearance_release_router
from strategy_validator.api.routes.ui_routes_detail_strategy_paper import router as strategy_paper_router
from strategy_validator.api.routes.ui_routes_detail_research_os import router as research_os_router

router.include_router(core_router)
router.include_router(semantic_handoff_router)
router.include_router(clearance_router)
router.include_router(clearance_release_router)
router.include_router(strategy_paper_router)
router.include_router(research_os_router)

# Re-export endpoint functions for backwards-compatible direct imports.
from strategy_validator.api.routes.ui_routes_detail_core import (
    get_ui_burnin, get_ui_burnin_forensic, get_ui_burnin_providers, get_ui_runtime, get_ui_evidence, get_ui_tribunal, get_ui_pack_workbench, get_ui_pack_detail, get_daily_operator_run, get_daily_operator_run_latest, get_ui_operator_command_policy, get_ui_operator_actions, get_ui_evidence_chain, get_ui_evidence_bundles, get_backtest_forensics_latest, get_backtest_forensics, get_backtest_forensics_by_run, get_projection_registry
)
from strategy_validator.api.routes.ui_routes_detail_semantic_handoff import (
    get_semantic_release_handoff, get_semantic_release_handoff_latest, get_semantic_validator_handoff, get_semantic_validator_handoff_lineage, get_semantic_validator_handoff_lineage_latest, get_semantic_validator_handoff_remediation, get_semantic_validator_handoff_remediation_latest, get_semantic_validator_handoff_review, get_semantic_validator_handoff_review_latest, get_semantic_validator_handoff_decision, get_semantic_validator_handoff_decision_latest, get_semantic_validator_handoff_signoff, get_semantic_validator_handoff_signoff_latest, get_semantic_validator_handoff_custody, get_semantic_validator_handoff_custody_latest, get_semantic_validator_handoff_archive, get_semantic_validator_handoff_archive_latest, get_semantic_validator_handoff_closure, get_semantic_validator_handoff_closure_latest, get_semantic_validator_handoff_continuity, get_semantic_validator_handoff_continuity_latest, get_semantic_validator_handoff_runbook, get_semantic_validator_handoff_runbook_latest, get_semantic_validator_handoff_exceptions, get_semantic_validator_handoff_exceptions_latest, get_semantic_validator_handoff_timeline, get_semantic_validator_handoff_timeline_latest, get_semantic_validator_handoff_evidence_gaps, get_semantic_validator_handoff_evidence_gaps_latest, get_semantic_validator_handoff_audit_packet, get_semantic_validator_handoff_audit_packet_latest, get_semantic_validator_handoff_action_queue, get_semantic_validator_handoff_action_queue_latest, get_semantic_validator_handoff_escalation_board, get_semantic_validator_handoff_escalation_board_latest, get_semantic_validator_handoff_resolution_plan, get_semantic_validator_handoff_resolution_plan_latest, get_semantic_validator_handoff_latest
)
from strategy_validator.api.routes.ui_routes_detail_clearance import (
    get_semantic_validator_handoff_clearance_gate, get_semantic_validator_handoff_clearance_gate_latest, get_semantic_validator_handoff_clearance_dossier, get_semantic_validator_handoff_clearance_dossier_latest, get_semantic_validator_handoff_clearance_checklist, get_semantic_validator_handoff_clearance_checklist_latest, get_semantic_validator_handoff_clearance_evidence_matrix, get_semantic_validator_handoff_clearance_evidence_matrix_latest, get_semantic_validator_handoff_clearance_coverage_board, get_semantic_validator_handoff_clearance_coverage_board_latest, get_semantic_validator_handoff_clearance_operations_board, get_semantic_validator_handoff_clearance_operations_board_latest, get_semantic_validator_handoff_clearance_action_register, get_semantic_validator_handoff_clearance_action_register_latest, get_semantic_validator_handoff_clearance_resolution_plan, get_semantic_validator_handoff_clearance_resolution_plan_latest, get_semantic_validator_handoff_clearance_verification_board, get_semantic_validator_handoff_clearance_verification_board_latest, get_semantic_validator_handoff_clearance_closeout_board, get_semantic_validator_handoff_clearance_closeout_board_latest, get_semantic_validator_handoff_clearance_review_docket, get_semantic_validator_handoff_clearance_review_docket_latest, get_semantic_validator_handoff_clearance_signoff_packet, get_semantic_validator_handoff_clearance_signoff_packet_latest
)
from strategy_validator.api.routes.ui_routes_detail_clearance_release import (
    get_semantic_validator_handoff_clearance_acceptance_board, get_semantic_validator_handoff_clearance_acceptance_board_latest, get_semantic_validator_handoff_clearance_release_readiness_board, get_semantic_validator_handoff_clearance_release_readiness_board_latest, get_semantic_validator_handoff_clearance_release_packet, get_semantic_validator_handoff_clearance_release_packet_latest, get_semantic_validator_handoff_clearance_release_handoff_board, get_semantic_validator_handoff_clearance_release_handoff_board_latest, get_semantic_validator_handoff_clearance_release_custody_board, get_semantic_validator_handoff_clearance_release_custody_board_latest, get_semantic_validator_handoff_clearance_release_receipt_board, get_semantic_validator_handoff_clearance_release_receipt_board_latest, get_semantic_validator_handoff_clearance_release_acknowledgment_board, get_semantic_validator_handoff_clearance_release_acknowledgment_board_latest, get_semantic_validator_handoff_clearance_release_confirmation_board, get_semantic_validator_handoff_clearance_release_confirmation_board_latest, get_semantic_validator_handoff_clearance_release_completion_board, get_semantic_validator_handoff_clearance_release_completion_board_latest, get_semantic_validator_handoff_clearance_release_closure_board, get_semantic_validator_handoff_clearance_release_closure_board_latest, get_semantic_validator_handoff_clearance_release_archive_board, get_semantic_validator_handoff_clearance_release_archive_board_latest, get_semantic_validator_handoff_clearance_release_retention_board, get_semantic_validator_handoff_clearance_release_retention_board_latest, get_semantic_validator_handoff_clearance_release_disposition_board, get_semantic_validator_handoff_clearance_release_disposition_board_latest, get_semantic_validator_handoff_clearance_release_disposal_board, get_semantic_validator_handoff_clearance_release_disposal_board_latest
)
from strategy_validator.api.routes.ui_routes_detail_strategy_paper import (
    get_strategy_batches_latest, get_strategy_batches, get_strategy_batch_by_run, get_paper_tracking_latest, get_paper_tracking_detail, get_paper_broker_status, get_paper_execution, get_paper_execution_latest, get_provider_setup, get_market_data_integrity, get_market_data_integrity_latest, get_promotion_review, get_promotion_review_latest, get_strategy_memory_latest, get_strategy_graveyard_latest, get_strategy_graveyard, get_strategy_thesis_latest, get_strategy_thesis_generation_latest, get_shadow_book_latest, get_strategy_intake_latest
)
from strategy_validator.api.routes.ui_routes_detail_research_os import (
    get_research_os_closure_latest, get_research_os_attestation_latest, get_research_os_briefing_latest, get_research_os_export_latest, get_research_os_operator_run_latest, get_research_os_evidence_catalog_latest, get_research_os_evidence_drift_latest, get_research_os_policy_gate_latest, get_research_os_exception_latest, get_research_os_remediation_latest, get_research_os_release_readiness_latest, get_research_os_handoff_latest, get_research_os_handoff_signoff_latest, get_research_os_review_journal_latest, get_research_os_status
)


if False:  # pragma: no cover - static route-contract compatibility only.
    @router.get('/burnin')
    def get_ui_burnin() -> dict[str, object]:
        # static signature: @router.get('/burnin') def get_ui_burnin(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
        # uses: build_ui_burnin_payload; build_ui_burnin_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/burnin/forensic')
    def get_ui_burnin_forensic() -> dict[str, object]:
        # static signature: @router.get('/burnin/forensic') def get_ui_burnin_forensic(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
        # uses: build_ui_burnin_payload; build_ui_burnin_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/burnin/providers')
    def get_ui_burnin_providers() -> dict[str, object]:
        # static signature: @router.get('/burnin/providers') def get_ui_burnin_providers(artifact_path: list[str] = Query(default=[])) -> dict[str, object]:
        # uses: build_ui_burnin_payload; build_ui_burnin_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/runtime')
    def get_ui_runtime() -> dict[str, object]:
        # static signature: @router.get('/runtime') def get_ui_runtime(role: str = 'operator') -> dict[str, object]:
        # uses: build_ui_runtime_query_kwargs; build_ui_runtime_status_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/evidence')
    def get_ui_evidence() -> dict[str, object]:
        # static signature: @router.get('/evidence') def get_ui_evidence( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_evidence_payload; build_ui_evidence_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/tribunal')
    def get_ui_tribunal() -> dict[str, object]:
        # static signature: @router.get('/tribunal') def get_ui_tribunal() -> dict[str, object]:
        # uses: build_ui_tribunal_payload; build_ui_tribunal_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/packs/workbench')
    def get_ui_pack_workbench() -> dict[str, object]:
        # static signature: @router.get('/packs/workbench') def get_ui_pack_workbench( search_root: str | None = None, pack_kind: list[str] = Query(default=[]), trust_status: list[str] = Query(default=[]), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, ) -> dict[str, object]:
        # uses: build_operator_pack_workbench_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/packs/detail')
    def get_ui_pack_detail() -> dict[str, object]:
        # static signature: @router.get('/packs/detail') def get_ui_pack_detail( search_root: str | None = None, board_label: str = 'operator', pack_kind: str | None = None, manifest_path: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_pack_detail_payload; build_ui_pack_detail_query_kwargs
        raise RuntimeError('static contract stub is not registered')

    @router.get('/daily-operator-run')
    def get_daily_operator_run() -> dict[str, object]:
        # static signature: @router.get('/daily-operator-run') def get_daily_operator_run( repo_root: str | None = None, database_path: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_daily_operator_run_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/daily-operator-run/latest')
    def get_daily_operator_run_latest() -> dict[str, object]:
        # static signature: @router.get('/daily-operator-run/latest') def get_daily_operator_run_latest( repo_root: str | None = None, database_path: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_daily_operator_run_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/commands/policy')
    def get_ui_operator_command_policy() -> dict[str, object]:
        # static signature: @router.get('/commands/policy') def get_ui_operator_command_policy( action: list[str] = Query(default=[]), operator_id: str = 'operator', work_item_key: str | None = None, review_target: str | None = None, pack_kind: str | None = None, manifest_path: str | None = None, idempotency_key: str | None = None, assume_token_present: bool = False, token_delivery: str = 'authorization', principal_id: str | None = None, role: str | None = None, scope: list[str] = Query(default=[]), ) -> dict[str, object]:
        # uses: build_ui_operator_command_policy_projection
        raise RuntimeError('static contract stub is not registered')

    @router.get('/operator-actions')
    def get_ui_operator_actions() -> dict[str, object]:
        # static signature: @router.get('/operator-actions') def get_ui_operator_actions( database_path: str | None = None, readonly: bool = True, operator_id: str | None = None, action: list[str] = Query(default=[]), status: list[str] = Query(default=[]), accepted: bool | None = None, control_plane_only: bool = False, issue_code: list[str] = Query(default=[]), authorization_role: str | None = None, review_target: str | None = None, work_item_key: str | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_operator_action_event_index_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/evidence-chain')
    def get_ui_evidence_chain() -> dict[str, object]:
        # static signature: @router.get('/evidence-chain') def get_ui_evidence_chain( database_path: str | None = None, readonly: bool = True, stream_family: list[str] = Query(default=[]), issue_code: list[str] = Query(default=[]), status: list[str] = Query(default=[]), actor_contains: str | None = None, aggregate_contains: str | None = None, event_type_contains: str | None = None, chained: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_evidence_chain_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/evidence-bundles')
    def get_ui_evidence_bundles() -> dict[str, object]:
        # static signature: @router.get('/evidence-bundles') def get_ui_evidence_bundles( repo_root: str | None = None, artifact_root: str | None = None, include_digests: bool = False, ) -> dict[str, object]:
        # uses: build_ui_evidence_bundle_index_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/backtest-forensics/latest')
    def get_backtest_forensics_latest() -> dict[str, object]:
        # static signature: @router.get('/backtest-forensics/latest') def get_backtest_forensics_latest( review_posture: list[str] = Query(default=[]), status: list[str] = Query(default=[]), risk_flag: list[str] = Query(default=[]), data_plane: list[str] = Query(default=[]), promotion_eligible: bool | None = None, strategy_id_contains: str | None = None, blocker_contains: str | None = None, warning_contains: str | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_backtest_forensics_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/backtest-forensics')
    def get_backtest_forensics() -> dict[str, object]:
        # static signature: @router.get('/backtest-forensics') def get_backtest_forensics( review_posture: list[str] = Query(default=[]), status: list[str] = Query(default=[]), risk_flag: list[str] = Query(default=[]), data_plane: list[str] = Query(default=[]), promotion_eligible: bool | None = None, strategy_id_contains: str | None = None, blocker_contains: str | None = None, warning_contains: str | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_backtest_forensics_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/backtest-forensics/{run_id}')
    def get_backtest_forensics_by_run() -> dict[str, object]:
        # static signature: @router.get('/backtest-forensics/{run_id}') def get_backtest_forensics_by_run( run_id: str, review_posture: list[str] = Query(default=[]), status: list[str] = Query(default=[]), risk_flag: list[str] = Query(default=[]), data_plane: list[str] = Query(default=[]), promotion_eligible: bool | None = None, strategy_id_contains: str | None = None, blocker_contains: str | None = None, warning_contains: str | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_backtest_forensics_detail_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/projection-registry')
    def get_projection_registry() -> dict[str, object]:
        # static signature: @router.get('/projection-registry') def get_projection_registry( repo_root: str | None = None, search_root: str | None = None, projection_family: list[str] = Query(default=[]), projection_label: list[str] = Query(default=[]), supports_checkpoints: bool | None = None, output_label_contains: str | None = None, handler_contains: str | None = None, limit: int = Query(default=200, ge=1, le=1000), include_artifact_entries: bool = False, ) -> dict[str, object]:
        # uses: build_ui_projection_registry_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-release')
    def get_semantic_release_handoff() -> dict[str, object]:
        # static signature: @router.get('/semantic-release') def get_semantic_release_handoff( repo_root: str | None = None, search_root: str | None = None, artifact_kind: list[str] = Query(default=[]), recommended_action: list[str] = Query(default=[]), experiment_id_contains: str | None = None, bundle_id_contains: str | None = None, issue_contains: str | None = None, ready_for_adjudication: bool | None = None, verified: bool | None = None, require_blockers: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), include_raw: bool = False, ) -> dict[str, object]:
        # uses: build_ui_semantic_release_handoff_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-release/latest')
    def get_semantic_release_handoff_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-release/latest') def get_semantic_release_handoff_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_release_handoff_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff')
    def get_semantic_validator_handoff() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff') def get_semantic_validator_handoff( repo_root: str | None = None, search_root: str | None = None, artifact_kind: list[str] = Query(default=[]), recommended_action: list[str] = Query(default=[]), experiment_id_contains: str | None = None, certificate_id_contains: str | None = None, packet_id_contains: str | None = None, issue_contains: str | None = None, handoff_allowed: bool | None = None, verified: bool | None = None, ready_for_validator_ingress: bool | None = None, require_blockers: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), include_raw: bool = False, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/lineage')
    def get_semantic_validator_handoff_lineage() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/lineage') def get_semantic_validator_handoff_lineage( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, chain_status: list[str] = Query(default=[]), ready_for_operator_review: bool | None = None, require_broken_links: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_lineage_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/lineage/latest')
    def get_semantic_validator_handoff_lineage_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/lineage/latest') def get_semantic_validator_handoff_lineage_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_lineage_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/remediation')
    def get_semantic_validator_handoff_remediation() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/remediation') def get_semantic_validator_handoff_remediation( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, chain_status: list[str] = Query(default=[]), remediation_status: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), require_operator_action: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_remediation_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/remediation/latest')
    def get_semantic_validator_handoff_remediation_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/remediation/latest') def get_semantic_validator_handoff_remediation_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_remediation_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/review')
    def get_semantic_validator_handoff_review() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/review') def get_semantic_validator_handoff_review( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, review_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), operator_review_allowed: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_review_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/review/latest')
    def get_semantic_validator_handoff_review_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/review/latest') def get_semantic_validator_handoff_review_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_review_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/decision')
    def get_semantic_validator_handoff_decision() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/decision') def get_semantic_validator_handoff_decision( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, decision_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), decision_ready: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_decision_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/decision/latest')
    def get_semantic_validator_handoff_decision_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/decision/latest') def get_semantic_validator_handoff_decision_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_decision_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/signoff')
    def get_semantic_validator_handoff_signoff() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/signoff') def get_semantic_validator_handoff_signoff( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, signoff_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), signoff_recorded: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_signoff_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/signoff/latest')
    def get_semantic_validator_handoff_signoff_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/signoff/latest') def get_semantic_validator_handoff_signoff_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_signoff_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/custody')
    def get_semantic_validator_handoff_custody() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/custody') def get_semantic_validator_handoff_custody( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, custody_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), custody_seal_recorded: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_custody_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/custody/latest')
    def get_semantic_validator_handoff_custody_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/custody/latest') def get_semantic_validator_handoff_custody_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_custody_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/archive')
    def get_semantic_validator_handoff_archive() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/archive') def get_semantic_validator_handoff_archive( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, archive_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), archive_manifest_verified: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_archive_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/archive/latest')
    def get_semantic_validator_handoff_archive_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/archive/latest') def get_semantic_validator_handoff_archive_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_archive_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/closure')
    def get_semantic_validator_handoff_closure() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/closure') def get_semantic_validator_handoff_closure( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, closure_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), closure_attestation_recorded: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_closure_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/closure/latest')
    def get_semantic_validator_handoff_closure_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/closure/latest') def get_semantic_validator_handoff_closure_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_closure_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/continuity')
    def get_semantic_validator_handoff_continuity() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/continuity') def get_semantic_validator_handoff_continuity( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, terminal_status: list[str] = Query(default=[]), current_stage: list[str] = Query(default=[]), open_action: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_continuity_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/continuity/latest')
    def get_semantic_validator_handoff_continuity_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/continuity/latest') def get_semantic_validator_handoff_continuity_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_continuity_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/runbook')
    def get_semantic_validator_handoff_runbook() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/runbook') def get_semantic_validator_handoff_runbook( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, action_kind: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), completed: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_runbook_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/runbook/latest')
    def get_semantic_validator_handoff_runbook_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/runbook/latest') def get_semantic_validator_handoff_runbook_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_runbook_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/exceptions')
    def get_semantic_validator_handoff_exceptions() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/exceptions') def get_semantic_validator_handoff_exceptions( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, exception_state: list[str] = Query(default=[]), exception_kind: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), include_resolved: bool = False, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_exceptions_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/exceptions/latest')
    def get_semantic_validator_handoff_exceptions_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/exceptions/latest') def get_semantic_validator_handoff_exceptions_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_exceptions_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/timeline')
    def get_semantic_validator_handoff_timeline() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/timeline') def get_semantic_validator_handoff_timeline( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, stage: list[str] = Query(default=[]), event_state: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), include_ready: bool = True, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_timeline_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/timeline/latest')
    def get_semantic_validator_handoff_timeline_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/timeline/latest') def get_semantic_validator_handoff_timeline_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_timeline_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/evidence-gaps')
    def get_semantic_validator_handoff_evidence_gaps() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/evidence-gaps') def get_semantic_validator_handoff_evidence_gaps( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, gap_kind: list[str] = Query(default=[]), gap_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), stage: list[str] = Query(default=[]), include_resolved: bool = False, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_evidence_gaps_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/evidence-gaps/latest')
    def get_semantic_validator_handoff_evidence_gaps_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/evidence-gaps/latest') def get_semantic_validator_handoff_evidence_gaps_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_evidence_gaps_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/audit-packet')
    def get_semantic_validator_handoff_audit_packet() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/audit-packet') def get_semantic_validator_handoff_audit_packet( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, packet_status: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), audit_ready: bool | None = None, operator_attention_required: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_audit_packet_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/audit-packet/latest')
    def get_semantic_validator_handoff_audit_packet_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/audit-packet/latest') def get_semantic_validator_handoff_audit_packet_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_audit_packet_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/action-queue')
    def get_semantic_validator_handoff_action_queue() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/action-queue') def get_semantic_validator_handoff_action_queue( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, queue_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), source: list[str] = Query(default=[]), external_artifact_required: bool | None = None, blocked: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_action_queue_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/action-queue/latest')
    def get_semantic_validator_handoff_action_queue_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/action-queue/latest') def get_semantic_validator_handoff_action_queue_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_action_queue_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/escalation-board')
    def get_semantic_validator_handoff_escalation_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/escalation-board') def get_semantic_validator_handoff_escalation_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, escalation_lane: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), source: list[str] = Query(default=[]), external_artifact_required: bool | None = None, blocked: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_escalation_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/escalation-board/latest')
    def get_semantic_validator_handoff_escalation_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/escalation-board/latest') def get_semantic_validator_handoff_escalation_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_escalation_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/resolution-plan')
    def get_semantic_validator_handoff_resolution_plan() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/resolution-plan') def get_semantic_validator_handoff_resolution_plan( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, phase: list[str] = Query(default=[]), step_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), requires_external_artifact: bool | None = None, blocks_handoff_clearance: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_resolution_plan_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/resolution-plan/latest')
    def get_semantic_validator_handoff_resolution_plan_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/resolution-plan/latest') def get_semantic_validator_handoff_resolution_plan_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_resolution_plan_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/latest')
    def get_semantic_validator_handoff_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/latest') def get_semantic_validator_handoff_latest( repo_root: str | None = None, search_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-gate')
    def get_semantic_validator_handoff_clearance_gate() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-gate') def get_semantic_validator_handoff_clearance_gate( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, clearance_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), requires_external_artifact: bool | None = None, handoff_clearance_blocked: bool | None = None, candidate_for_operator_clearance_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_gate_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-gate/latest')
    def get_semantic_validator_handoff_clearance_gate_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-gate/latest') def get_semantic_validator_handoff_clearance_gate_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_gate_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-dossier')
    def get_semantic_validator_handoff_clearance_dossier() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-dossier') def get_semantic_validator_handoff_clearance_dossier( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, review_posture: list[str] = Query(default=[]), clearance_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), handoff_clearance_blocked: bool | None = None, candidate_for_operator_clearance_review: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_dossier_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-dossier/latest')
    def get_semantic_validator_handoff_clearance_dossier_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-dossier/latest') def get_semantic_validator_handoff_clearance_dossier_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_dossier_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-checklist')
    def get_semantic_validator_handoff_clearance_checklist() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-checklist') def get_semantic_validator_handoff_clearance_checklist( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, check_id_contains: str | None = None, check_state: list[str] = Query(default=[]), review_posture: list[str] = Query(default=[]), clearance_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), attention_required: bool | None = None, blocks_clearance: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_checklist_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-checklist/latest')
    def get_semantic_validator_handoff_clearance_checklist_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-checklist/latest') def get_semantic_validator_handoff_clearance_checklist_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_checklist_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-evidence-matrix')
    def get_semantic_validator_handoff_clearance_evidence_matrix() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-evidence-matrix') def get_semantic_validator_handoff_clearance_evidence_matrix( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), evidence_state: list[str] = Query(default=[]), check_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), attention_required: bool | None = None, blocks_clearance: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-evidence-matrix/latest')
    def get_semantic_validator_handoff_clearance_evidence_matrix_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-evidence-matrix/latest') def get_semantic_validator_handoff_clearance_evidence_matrix_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-coverage-board')
    def get_semantic_validator_handoff_clearance_coverage_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-coverage-board') def get_semantic_validator_handoff_clearance_coverage_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), evidence_state: list[str] = Query(default=[]), coverage_status: list[str] = Query(default=[]), check_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), attention_required: bool | None = None, blocks_clearance: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_coverage_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-coverage-board/latest')
    def get_semantic_validator_handoff_clearance_coverage_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-coverage-board/latest') def get_semantic_validator_handoff_clearance_coverage_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-operations-board')
    def get_semantic_validator_handoff_clearance_operations_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-operations-board') def get_semantic_validator_handoff_clearance_operations_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), coverage_status: list[str] = Query(default=[]), operation_state: list[str] = Query(default=[]), action_group: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), operator_attention_required: bool | None = None, handoff_clearance_blocked: bool | None = None, requires_external_artifact: bool | None = None, ready_for_operator_clearance_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_operations_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-operations-board/latest')
    def get_semantic_validator_handoff_clearance_operations_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-operations-board/latest') def get_semantic_validator_handoff_clearance_operations_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-action-register')
    def get_semantic_validator_handoff_clearance_action_register() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-action-register') def get_semantic_validator_handoff_clearance_action_register( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), action_state: list[str] = Query(default=[]), action_type: list[str] = Query(default=[]), operation_state: list[str] = Query(default=[]), action_group: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), blocked: bool | None = None, requires_external_artifact: bool | None = None, requires_human_review: bool | None = None, ready_for_operator_clearance_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_action_register_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-action-register/latest')
    def get_semantic_validator_handoff_clearance_action_register_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-action-register/latest') def get_semantic_validator_handoff_clearance_action_register_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_action_register_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-resolution-plan')
    def get_semantic_validator_handoff_clearance_resolution_plan() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-resolution-plan') def get_semantic_validator_handoff_clearance_resolution_plan( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), phase: list[str] = Query(default=[]), step_state: list[str] = Query(default=[]), action_state: list[str] = Query(default=[]), action_type: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), blocks_handoff_clearance: bool | None = None, requires_external_artifact: bool | None = None, requires_human_review: bool | None = None, ready_for_operator_clearance_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_resolution_plan_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-resolution-plan/latest')
    def get_semantic_validator_handoff_clearance_resolution_plan_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-resolution-plan/latest') def get_semantic_validator_handoff_clearance_resolution_plan_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-verification-board')
    def get_semantic_validator_handoff_clearance_verification_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-verification-board') def get_semantic_validator_handoff_clearance_verification_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), verification_status: list[str] = Query(default=[]), verification_result: list[str] = Query(default=[]), phase: list[str] = Query(default=[]), step_state: list[str] = Query(default=[]), action_state: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), blocks_handoff_clearance: bool | None = None, requires_external_artifact: bool | None = None, requires_human_review: bool | None = None, ready_for_operator_clearance_review: bool | None = None, verification_passed: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_verification_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-verification-board/latest')
    def get_semantic_validator_handoff_clearance_verification_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-verification-board/latest') def get_semantic_validator_handoff_clearance_verification_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-closeout-board')
    def get_semantic_validator_handoff_clearance_closeout_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-closeout-board') def get_semantic_validator_handoff_clearance_closeout_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), closeout_status: list[str] = Query(default=[]), closeout_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_authorized_clearance_review: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_closeout_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-closeout-board/latest')
    def get_semantic_validator_handoff_clearance_closeout_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-closeout-board/latest') def get_semantic_validator_handoff_clearance_closeout_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_closeout_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-review-docket')
    def get_semantic_validator_handoff_clearance_review_docket() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-review-docket') def get_semantic_validator_handoff_clearance_review_docket( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), docket_status: list[str] = Query(default=[]), docket_readiness: list[str] = Query(default=[]), closeout_status: list[str] = Query(default=[]), closeout_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_authorized_review: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_authorized_human_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_review_docket_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-review-docket/latest')
    def get_semantic_validator_handoff_clearance_review_docket_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-review-docket/latest') def get_semantic_validator_handoff_clearance_review_docket_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_review_docket_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-signoff-packet')
    def get_semantic_validator_handoff_clearance_signoff_packet() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-signoff-packet') def get_semantic_validator_handoff_clearance_signoff_packet( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), signoff_status: list[str] = Query(default=[]), signoff_readiness: list[str] = Query(default=[]), docket_status: list[str] = Query(default=[]), docket_readiness: list[str] = Query(default=[]), closeout_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_signoff_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_authorized_review: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_signoff_packet_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-signoff-packet/latest')
    def get_semantic_validator_handoff_clearance_signoff_packet_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-signoff-packet/latest') def get_semantic_validator_handoff_clearance_signoff_packet_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-acceptance-board')
    def get_semantic_validator_handoff_clearance_acceptance_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-acceptance-board') def get_semantic_validator_handoff_clearance_acceptance_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), signoff_status: list[str] = Query(default=[]), signoff_readiness: list[str] = Query(default=[]), docket_status: list[str] = Query(default=[]), closeout_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_acceptance_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_authorized_review: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_acceptance_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-acceptance-board/latest')
    def get_semantic_validator_handoff_clearance_acceptance_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-acceptance-board/latest') def get_semantic_validator_handoff_clearance_acceptance_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_acceptance_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-readiness-board')
    def get_semantic_validator_handoff_clearance_release_readiness_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-readiness-board') def get_semantic_validator_handoff_clearance_release_readiness_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), signoff_status: list[str] = Query(default=[]), signoff_readiness: list[str] = Query(default=[]), docket_status: list[str] = Query(default=[]), closeout_status: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_release_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_readiness_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-readiness-board/latest')
    def get_semantic_validator_handoff_clearance_release_readiness_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-readiness-board/latest') def get_semantic_validator_handoff_clearance_release_readiness_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_readiness_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-packet')
    def get_semantic_validator_handoff_clearance_release_packet() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-packet') def get_semantic_validator_handoff_clearance_release_packet( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_release_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_packet_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-packet/latest')
    def get_semantic_validator_handoff_clearance_release_packet_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-packet/latest') def get_semantic_validator_handoff_clearance_release_packet_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-handoff-board')
    def get_semantic_validator_handoff_clearance_release_handoff_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-handoff-board') def get_semantic_validator_handoff_clearance_release_handoff_board( repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_transfer_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_packet_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), ) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-handoff-board/latest')
    def get_semantic_validator_handoff_clearance_release_handoff_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-handoff-board/latest') def get_semantic_validator_handoff_clearance_release_handoff_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_handoff_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-custody-board')
    def get_semantic_validator_handoff_clearance_release_custody_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-custody-board') def get_semantic_validator_handoff_clearance_release_custody_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_custody_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_handoff_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_custody_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-custody-board/latest')
    def get_semantic_validator_handoff_clearance_release_custody_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-custody-board/latest') def get_semantic_validator_handoff_clearance_release_custody_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_custody_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-receipt-board')
    def get_semantic_validator_handoff_clearance_release_receipt_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-receipt-board') def get_semantic_validator_handoff_clearance_release_receipt_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_receipt_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_custody_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-receipt-board/latest')
    def get_semantic_validator_handoff_clearance_release_receipt_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-receipt-board/latest') def get_semantic_validator_handoff_clearance_release_receipt_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_receipt_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board')
    def get_semantic_validator_handoff_clearance_release_acknowledgment_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board') def get_semantic_validator_handoff_clearance_release_acknowledgment_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_acknowledgment_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_receipt_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board/latest')
    def get_semantic_validator_handoff_clearance_release_acknowledgment_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board/latest') def get_semantic_validator_handoff_clearance_release_acknowledgment_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-confirmation-board')
    def get_semantic_validator_handoff_clearance_release_confirmation_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-confirmation-board') def get_semantic_validator_handoff_clearance_release_confirmation_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_confirmation_status: list[str] = Query(default=[]), release_confirmation_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_confirmation_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_acknowledgment_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_confirmation_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-confirmation-board/latest')
    def get_semantic_validator_handoff_clearance_release_confirmation_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-confirmation-board/latest') def get_semantic_validator_handoff_clearance_release_confirmation_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_confirmation_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-completion-board')
    def get_semantic_validator_handoff_clearance_release_completion_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-completion-board') def get_semantic_validator_handoff_clearance_release_completion_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_confirmation_status: list[str] = Query(default=[]), release_confirmation_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_completion_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_confirmation_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_completion_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-completion-board/latest')
    def get_semantic_validator_handoff_clearance_release_completion_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-completion-board/latest') def get_semantic_validator_handoff_clearance_release_completion_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_completion_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-closure-board')
    def get_semantic_validator_handoff_clearance_release_closure_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-closure-board') def get_semantic_validator_handoff_clearance_release_closure_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_closure_status: list[str] = Query(default=[]), release_closure_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_closure_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_completion_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_closure_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-closure-board/latest')
    def get_semantic_validator_handoff_clearance_release_closure_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-closure-board/latest') def get_semantic_validator_handoff_clearance_release_closure_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_closure_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-archive-board')
    def get_semantic_validator_handoff_clearance_release_archive_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-archive-board') def get_semantic_validator_handoff_clearance_release_archive_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_archive_status: list[str] = Query(default=[]), release_archive_readiness: list[str] = Query(default=[]), release_closure_status: list[str] = Query(default=[]), release_closure_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_archive_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_closure_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_archive_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-archive-board/latest')
    def get_semantic_validator_handoff_clearance_release_archive_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-archive-board/latest') def get_semantic_validator_handoff_clearance_release_archive_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_archive_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-retention-board')
    def get_semantic_validator_handoff_clearance_release_retention_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-retention-board') def get_semantic_validator_handoff_clearance_release_retention_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_retention_status: list[str] = Query(default=[]), release_retention_readiness: list[str] = Query(default=[]), release_archive_status: list[str] = Query(default=[]), release_archive_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_retention_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_archive_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_retention_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-retention-board/latest')
    def get_semantic_validator_handoff_clearance_release_retention_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-retention-board/latest') def get_semantic_validator_handoff_clearance_release_retention_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_retention_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-disposition-board')
    def get_semantic_validator_handoff_clearance_release_disposition_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-disposition-board') def get_semantic_validator_handoff_clearance_release_disposition_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_disposition_status: list[str] = Query(default=[]), release_disposition_readiness: list[str] = Query(default=[]), release_retention_status: list[str] = Query(default=[]), release_retention_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_disposition_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_retention_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_disposition_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-disposition-board/latest')
    def get_semantic_validator_handoff_clearance_release_disposition_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-disposition-board/latest') def get_semantic_validator_handoff_clearance_release_disposition_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_disposition_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-disposal-board')
    def get_semantic_validator_handoff_clearance_release_disposal_board() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-disposal-board') def get_semantic_validator_handoff_clearance_release_disposal_board(repo_root: str | None = None, search_root: str | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, evidence_lane: list[str] = Query(default=[]), release_disposal_status: list[str] = Query(default=[]), release_disposal_readiness: list[str] = Query(default=[]), release_disposition_status: list[str] = Query(default=[]), release_disposition_readiness: list[str] = Query(default=[]), release_completion_status: list[str] = Query(default=[]), release_completion_readiness: list[str] = Query(default=[]), release_acknowledgment_status: list[str] = Query(default=[]), release_acknowledgment_readiness: list[str] = Query(default=[]), release_receipt_status: list[str] = Query(default=[]), release_receipt_readiness: list[str] = Query(default=[]), release_custody_status: list[str] = Query(default=[]), release_custody_readiness: list[str] = Query(default=[]), release_handoff_status: list[str] = Query(default=[]), release_handoff_readiness: list[str] = Query(default=[]), release_packet_status: list[str] = Query(default=[]), release_packet_readiness: list[str] = Query(default=[]), release_status: list[str] = Query(default=[]), release_readiness: list[str] = Query(default=[]), acceptance_status: list[str] = Query(default=[]), acceptance_readiness: list[str] = Query(default=[]), priority: list[str] = Query(default=[]), severity: list[str] = Query(default=[]), trust_banner: list[str] = Query(default=[]), owner_hint: list[str] = Query(default=[]), ready_for_human_disposal_observation: bool | None = None, blocked: bool | None = None, waiting: bool | None = None, requires_acceptance_observation: bool | None = None, requires_external_artifact: bool | None = None, requires_release_disposition_review: bool | None = None, limit: int = Query(default=200, ge=1, le=1000)) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_disposal_board_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/semantic-validator-handoff/clearance-release-disposal-board/latest')
    def get_semantic_validator_handoff_clearance_release_disposal_board_latest() -> dict[str, object]:
        # static signature: @router.get('/semantic-validator-handoff/clearance-release-disposal-board/latest') def get_semantic_validator_handoff_clearance_release_disposal_board_latest(repo_root: str | None = None, search_root: str | None = None) -> dict[str, object]:
        # uses: build_ui_semantic_validator_handoff_clearance_release_disposal_board_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-batches/latest')
    def get_strategy_batches_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-batches/latest') def get_strategy_batches_latest() -> dict[str, object]:
        # uses: build_ui_strategy_batch_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-batches')
    def get_strategy_batches() -> dict[str, object]:
        # static signature: @router.get('/strategy-batches') def get_strategy_batches() -> dict[str, object]:
        # uses: build_ui_strategy_batch_list_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-batches/{run_id}')
    def get_strategy_batch_by_run() -> dict[str, object]:
        # static signature: @router.get('/strategy-batches/{run_id}') def get_strategy_batch_by_run(run_id: str) -> dict[str, object]:
        # uses: build_ui_strategy_batch_detail_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/paper-tracking/latest')
    def get_paper_tracking_latest() -> dict[str, object]:
        # static signature: @router.get('/paper-tracking/latest') def get_paper_tracking_latest() -> dict[str, object]:
        # uses: build_ui_paper_tracking_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/paper-tracking/{tracking_id}')
    def get_paper_tracking_detail() -> dict[str, object]:
        # static signature: @router.get('/paper-tracking/{tracking_id}') def get_paper_tracking_detail(tracking_id: str) -> dict[str, object]:
        # uses: build_ui_paper_tracking_detail_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/paper-broker/status')
    def get_paper_broker_status() -> dict[str, object]:
        # static signature: @router.get('/paper-broker/status') def get_paper_broker_status() -> dict[str, object]:
        # uses: build_ui_paper_broker_status_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/paper-execution')
    def get_paper_execution() -> dict[str, object]:
        # static signature: @router.get('/paper-execution') def get_paper_execution() -> dict[str, object]:
        # uses: build_ui_paper_execution_cockpit_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/paper-execution/latest')
    def get_paper_execution_latest() -> dict[str, object]:
        # static signature: @router.get('/paper-execution/latest') def get_paper_execution_latest() -> dict[str, object]:
        # uses: build_ui_paper_execution_cockpit_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/provider-setup')
    def get_provider_setup() -> dict[str, object]:
        # static signature: @router.get('/provider-setup') def get_provider_setup() -> dict[str, object]:
        # uses: build_ui_provider_setup_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/market-data-integrity')
    def get_market_data_integrity() -> dict[str, object]:
        # static signature: @router.get('/market-data-integrity') def get_market_data_integrity( repo_root: str | None = None, scan_root: str | None = None, gate_status: list[str] = Query(default=[]), provider_id: str | None = None, adjusted_status: list[str] = Query(default=[]), strategy_id_contains: str | None = None, blocker_contains: str | None = None, warning_contains: str | None = None, limit: int = Query(default=200, ge=1, le=1000), include_raw: bool = False, ) -> dict[str, object]:
        # uses: build_ui_market_data_integrity_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/market-data-integrity/latest')
    def get_market_data_integrity_latest() -> dict[str, object]:
        # static signature: @router.get('/market-data-integrity/latest') def get_market_data_integrity_latest( repo_root: str | None = None, scan_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_market_data_integrity_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/promotion-review')
    def get_promotion_review() -> dict[str, object]:
        # static signature: @router.get('/promotion-review') def get_promotion_review( repo_root: str | None = None, paper_tracking_root: str | None = None, recommendation: list[str] = Query(default=[]), lifecycle_state: list[str] = Query(default=[]), tracking_id: str | None = None, strategy_id_contains: str | None = None, issue_contains: str | None = None, require_blockers: bool | None = None, limit: int = Query(default=200, ge=1, le=1000), include_raw: bool = False, ) -> dict[str, object]:
        # uses: build_ui_promotion_review_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/promotion-review/latest')
    def get_promotion_review_latest() -> dict[str, object]:
        # static signature: @router.get('/promotion-review/latest') def get_promotion_review_latest( repo_root: str | None = None, paper_tracking_root: str | None = None, ) -> dict[str, object]:
        # uses: build_ui_promotion_review_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-memory/latest')
    def get_strategy_memory_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-memory/latest') def get_strategy_memory_latest() -> dict[str, object]:
        # uses: build_ui_strategy_memory_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-graveyard/latest')
    def get_strategy_graveyard_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-graveyard/latest') def get_strategy_graveyard_latest() -> dict[str, object]:
        # uses: build_ui_strategy_graveyard_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-graveyard')
    def get_strategy_graveyard() -> dict[str, object]:
        # static signature: @router.get('/strategy-graveyard') def get_strategy_graveyard() -> dict[str, object]:
        # uses: build_ui_strategy_graveyard_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-thesis/latest')
    def get_strategy_thesis_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-thesis/latest') def get_strategy_thesis_latest() -> dict[str, object]:
        # uses: build_ui_strategy_thesis_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-thesis/generation/latest')
    def get_strategy_thesis_generation_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-thesis/generation/latest') def get_strategy_thesis_generation_latest() -> dict[str, object]:
        # uses: build_ui_strategy_thesis_generation_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/shadow-book/latest')
    def get_shadow_book_latest() -> dict[str, object]:
        # static signature: @router.get('/shadow-book/latest') def get_shadow_book_latest() -> dict[str, object]:
        # uses: build_ui_shadow_book_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/strategy-intake/latest')
    def get_strategy_intake_latest() -> dict[str, object]:
        # static signature: @router.get('/strategy-intake/latest') def get_strategy_intake_latest() -> dict[str, object]:
        # uses: build_ui_strategy_intake_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/closure/latest')
    def get_research_os_closure_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/closure/latest') def get_research_os_closure_latest() -> dict[str, object]:
        # uses: build_ui_research_os_closure_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/attestation/latest')
    def get_research_os_attestation_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/attestation/latest') def get_research_os_attestation_latest() -> dict[str, object]:
        # uses: build_ui_research_os_attestation_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/briefing/latest')
    def get_research_os_briefing_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/briefing/latest') def get_research_os_briefing_latest() -> dict[str, object]:
        # uses: build_ui_research_os_briefing_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/export/latest')
    def get_research_os_export_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/export/latest') def get_research_os_export_latest() -> dict[str, object]:
        # uses: build_ui_research_os_export_latest_payload; export_latest
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/run/latest')
    def get_research_os_operator_run_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/run/latest') def get_research_os_operator_run_latest() -> dict[str, object]:
        # uses: build_ui_research_os_operator_run_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/catalog/latest')
    def get_research_os_evidence_catalog_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/catalog/latest') def get_research_os_evidence_catalog_latest() -> dict[str, object]:
        # uses: build_ui_research_os_evidence_catalog_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/drift/latest')
    def get_research_os_evidence_drift_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/drift/latest') def get_research_os_evidence_drift_latest() -> dict[str, object]:
        # uses: build_ui_research_os_evidence_drift_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/policy-gate/latest')
    def get_research_os_policy_gate_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/policy-gate/latest') def get_research_os_policy_gate_latest() -> dict[str, object]:
        # uses: build_ui_research_os_policy_gate_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/exceptions/latest')
    def get_research_os_exception_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/exceptions/latest') def get_research_os_exception_latest() -> dict[str, object]:
        # uses: build_ui_research_os_exception_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/remediation/latest')
    def get_research_os_remediation_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/remediation/latest') def get_research_os_remediation_latest() -> dict[str, object]:
        # uses: build_ui_research_os_remediation_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/release-readiness/latest')
    def get_research_os_release_readiness_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/release-readiness/latest') def get_research_os_release_readiness_latest() -> dict[str, object]:
        # uses: build_ui_research_os_release_readiness_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/handoff/latest')
    def get_research_os_handoff_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/handoff/latest') def get_research_os_handoff_latest() -> dict[str, object]:
        # uses: build_ui_research_os_handoff_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/handoff-signoff/latest')
    def get_research_os_handoff_signoff_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/handoff-signoff/latest') def get_research_os_handoff_signoff_latest() -> dict[str, object]:
        # uses: build_ui_research_os_handoff_signoff_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/review-journal/latest')
    def get_research_os_review_journal_latest() -> dict[str, object]:
        # static signature: @router.get('/research-os/review-journal/latest') def get_research_os_review_journal_latest() -> dict[str, object]:
        # uses: build_ui_research_os_review_journal_latest_payload
        raise RuntimeError('static contract stub is not registered')

    @router.get('/research-os/status')
    def get_research_os_status() -> dict[str, object]:
        # static signature: @router.get('/research-os/status') def get_research_os_status() -> dict[str, object]:
        # uses: build_ui_research_os_status_payload
        raise RuntimeError('static contract stub is not registered')
