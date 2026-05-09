from __future__ import annotations

import os
from pathlib import Path

from strategy_validator.contracts.ui_public_facade import UiPublicFacadeInventory, UiPublicFacadeRoute
from strategy_validator.application.frontend_readiness_claim import load_frontend_readiness_claim
from strategy_validator.providers.health import (
    build_provider_health_snapshot,
    provider_health_snapshot_public_payload,
)

UI_PUBLIC_FACADE_SCHEMA_VERSION = 'ui_public_facade_inventory/v1'
UI_PUBLIC_FACADE_SURFACE = 'ui'
UI_FRONTEND_EXPECTED_PACKAGE = 'ui/strategist-web'
UI_COMMAND_MUTATION_ROUTE = '/ui/commands/{action}'


def _frontend_status(repo_root: Path | None = None) -> tuple[bool, str]:
    """Detect ``ui/strategist-web`` relative to *repo_root* (default: process cwd).

    In API-only containers the working directory is typically ``/app`` without the
    monorepo tree, so this returns absent even when a separate Next.js operator
    console is running against the same API.
    """
    root = repo_root or Path.cwd()
    package_json = root / UI_FRONTEND_EXPECTED_PACKAGE / 'package.json'
    package_lock = root / UI_FRONTEND_EXPECTED_PACKAGE / 'package-lock.json'
    package_present = package_json.exists() or package_lock.exists()
    if package_present:
        return True, 'package_present_unverified'
    return False, 'absent'


# Shown on GET /ui/facade; stable operator-facing copy (no readiness claim).
_FRONTEND_OPERATOR_CONSOLE_HINT = (
    'The API only scans its process working directory for ui/strategist-web. '
    'frontend_package_present / frontend_package_detected_by_backend are false in typical API-only containers '
    'even when the Next.js operator console runs separately; that is expected. '
    'frontend_readiness_claimed stays false unless STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_ENABLE is set '
    'and a validated claim artifact is present (opt-in; not automatic production certification).'
)


_UI_PUBLIC_FACADE_ROUTES: tuple[UiPublicFacadeRoute, ...] = (
    UiPublicFacadeRoute('GET', '/ui/facade', 'metadata', False, UI_PUBLIC_FACADE_SCHEMA_VERSION),
    UiPublicFacadeRoute('GET', '/ui/health', 'metadata', False, 'ui_health/v1'),
    UiPublicFacadeRoute('GET', '/ui/workboard', 'read', False, 'ui_workboard_dashboard/v1'),
    UiPublicFacadeRoute('GET', '/ui/workboard/export', 'export', False, 'oracle_operator_board_export_payload/v1'),
    UiPublicFacadeRoute('GET', '/ui/workboard/export/document', 'export', False, 'oracle_operator_board_export_document/v1'),
    UiPublicFacadeRoute('HEAD', '/ui/workboard/export/document', 'export', False, 'oracle_operator_board_export_document/v1'),
    UiPublicFacadeRoute('OPTIONS', '/ui/workboard/export/document', 'metadata', False, 'ui_workboard_export_options/v1'),
    UiPublicFacadeRoute('GET', '/ui/workboard/export/index', 'export', False, 'oracle_operator_board_export_index/v1'),
    UiPublicFacadeRoute('HEAD', '/ui/workboard/export/index', 'export', False, 'oracle_operator_board_export_index/v1'),
    UiPublicFacadeRoute('OPTIONS', '/ui/workboard/export/index', 'metadata', False, 'ui_workboard_export_options/v1'),
    UiPublicFacadeRoute('GET', '/ui/burnin', 'read', False, 'ui_burnin/v1'),
    UiPublicFacadeRoute('GET', '/ui/burnin/forensic', 'read', False, 'ui_burnin/v1'),
    UiPublicFacadeRoute('GET', '/ui/burnin/providers', 'read', False, 'ui_burnin/v1'),
    UiPublicFacadeRoute('GET', '/ui/runtime', 'read', False, 'ui_runtime_status/v1'),
    UiPublicFacadeRoute('GET', '/ui/evidence', 'read', False, 'ui_evidence/v1'),
    UiPublicFacadeRoute('GET', '/ui/tribunal', 'read', False, 'ui_tribunal_workspace/v1'),
    UiPublicFacadeRoute('GET', '/ui/packs/workbench', 'read', False, 'oracle_operator_pack_workbench/v1'),
    UiPublicFacadeRoute('GET', '/ui/packs/detail', 'read', False, 'ui_pack_detail/v1'),
    UiPublicFacadeRoute('GET', '/ui/commands/policy', 'read', False, 'ui_operator_command_policy_projection/v1'),
    UiPublicFacadeRoute('GET', '/ui/operator-actions', 'read', False, 'operator_action_event_projection_index/v1'),
    UiPublicFacadeRoute('GET', '/ui/evidence-chain', 'read', False, 'ui_evidence_chain/v1'),
    UiPublicFacadeRoute('GET', '/ui/evidence-bundles', 'read', False, 'evidence_bundle_index/v1'),
    UiPublicFacadeRoute('GET', '/ui/provider-health', 'read', False, 'provider_health_snapshot/v1'),
    UiPublicFacadeRoute('GET', '/ui/provider-setup', 'read', False, 'ui_provider_setup_console/v1'),
    UiPublicFacadeRoute('GET', '/ui/market-data-integrity', 'read', False, 'ui_market_data_integrity/v1'),
    UiPublicFacadeRoute('GET', '/ui/market-data-integrity/latest', 'read', False, 'ui_market_data_integrity/v1'),
    UiPublicFacadeRoute('GET', '/ui/daily-operator-run', 'read', False, 'ui_daily_operator_run/v1'),
    UiPublicFacadeRoute('GET', '/ui/daily-operator-run/latest', 'read', False, 'ui_daily_operator_run/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-compute', 'read', False, 'ui_research_compute/v1'),
    UiPublicFacadeRoute('GET', '/ui/projection-registry', 'read', False, 'ui_projection_registry/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-release', 'read', False, 'ui_semantic_release_handoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-release/latest', 'read', False, 'ui_semantic_release_handoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff', 'read', False, 'ui_semantic_validator_handoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/latest', 'read', False, 'ui_semantic_validator_handoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/lineage', 'read', False, 'ui_semantic_validator_handoff_lineage/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/lineage/latest', 'read', False, 'ui_semantic_validator_handoff_lineage/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/remediation', 'read', False, 'ui_semantic_validator_handoff_remediation/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/remediation/latest', 'read', False, 'ui_semantic_validator_handoff_remediation/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/review', 'read', False, 'ui_semantic_validator_handoff_review/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/review/latest', 'read', False, 'ui_semantic_validator_handoff_review/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/decision', 'read', False, 'ui_semantic_validator_handoff_decision/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/decision/latest', 'read', False, 'ui_semantic_validator_handoff_decision/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/signoff', 'read', False, 'ui_semantic_validator_handoff_signoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/signoff/latest', 'read', False, 'ui_semantic_validator_handoff_signoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/custody', 'read', False, 'ui_semantic_validator_handoff_custody/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/custody/latest', 'read', False, 'ui_semantic_validator_handoff_custody/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/archive', 'read', False, 'ui_semantic_validator_handoff_archive/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/archive/latest', 'read', False, 'ui_semantic_validator_handoff_archive/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/closure', 'read', False, 'ui_semantic_validator_handoff_closure/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/closure/latest', 'read', False, 'ui_semantic_validator_handoff_closure/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/continuity', 'read', False, 'ui_semantic_validator_handoff_continuity/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/continuity/latest', 'read', False, 'ui_semantic_validator_handoff_continuity/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/runbook', 'read', False, 'ui_semantic_validator_handoff_runbook/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/runbook/latest', 'read', False, 'ui_semantic_validator_handoff_runbook/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/exceptions', 'read', False, 'ui_semantic_validator_handoff_exceptions/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/exceptions/latest', 'read', False, 'ui_semantic_validator_handoff_exceptions/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/timeline', 'read', False, 'ui_semantic_validator_handoff_timeline/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/timeline/latest', 'read', False, 'ui_semantic_validator_handoff_timeline/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/evidence-gaps', 'read', False, 'ui_semantic_validator_handoff_evidence_gaps/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/evidence-gaps/latest', 'read', False, 'ui_semantic_validator_handoff_evidence_gaps/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/audit-packet', 'read', False, 'ui_semantic_validator_handoff_audit_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/audit-packet/latest', 'read', False, 'ui_semantic_validator_handoff_audit_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/action-queue', 'read', False, 'ui_semantic_validator_handoff_action_queue/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/action-queue/latest', 'read', False, 'ui_semantic_validator_handoff_action_queue/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/escalation-board', 'read', False, 'ui_semantic_validator_handoff_escalation_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/escalation-board/latest', 'read', False, 'ui_semantic_validator_handoff_escalation_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/resolution-plan', 'read', False, 'ui_semantic_validator_handoff_resolution_plan/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/resolution-plan/latest', 'read', False, 'ui_semantic_validator_handoff_resolution_plan/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-gate', 'read', False, 'ui_semantic_validator_handoff_clearance_gate/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-gate/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_gate/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-dossier', 'read', False, 'ui_semantic_validator_handoff_clearance_dossier/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-dossier/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_dossier/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-checklist', 'read', False, 'ui_semantic_validator_handoff_clearance_checklist/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-checklist/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_checklist/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-evidence-matrix', 'read', False, 'ui_semantic_validator_handoff_clearance_evidence_matrix/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-evidence-matrix/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_evidence_matrix/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-coverage-board', 'read', False, 'ui_semantic_validator_handoff_clearance_coverage_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-coverage-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_coverage_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-operations-board', 'read', False, 'ui_semantic_validator_handoff_clearance_operations_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-operations-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_operations_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-action-register', 'read', False, 'ui_semantic_validator_handoff_clearance_action_register/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-action-register/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_action_register/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-resolution-plan', 'read', False, 'ui_semantic_validator_handoff_clearance_resolution_plan/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-resolution-plan/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_resolution_plan/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-verification-board', 'read', False, 'ui_semantic_validator_handoff_clearance_verification_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-verification-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_verification_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-closeout-board', 'read', False, 'ui_semantic_validator_handoff_clearance_closeout_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-closeout-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_closeout_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-review-docket', 'read', False, 'ui_semantic_validator_handoff_clearance_review_docket/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-review-docket/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_review_docket/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-signoff-packet', 'read', False, 'ui_semantic_validator_handoff_clearance_signoff_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-signoff-packet/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_signoff_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-acceptance-board', 'read', False, 'ui_semantic_validator_handoff_clearance_acceptance_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-acceptance-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_acceptance_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-readiness-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_readiness_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-readiness-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_readiness_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-packet', 'read', False, 'ui_semantic_validator_handoff_clearance_release_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-packet/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_packet/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-handoff-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_handoff_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-handoff-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_handoff_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-custody-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_custody_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-custody-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_custody_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-receipt-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_receipt_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-receipt-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_receipt_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-acknowledgment-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_acknowledgment_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-acknowledgment-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_acknowledgment_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-confirmation-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_confirmation_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-confirmation-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_confirmation_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-completion-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_completion_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-completion-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_completion_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-closure-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_closure_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-closure-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_closure_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-archive-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_archive_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-archive-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_archive_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-retention-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_retention_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-retention-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_retention_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-disposition-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_disposition_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-disposition-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_disposition_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-disposal-board', 'read', False, 'ui_semantic_validator_handoff_clearance_release_disposal_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/semantic-validator-handoff/clearance-release-disposal-board/latest', 'read', False, 'ui_semantic_validator_handoff_clearance_release_disposal_board/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches/latest', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches/{run_id}', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics', 'read', False, 'ui_backtest_forensics/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics/latest', 'read', False, 'ui_backtest_forensics/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics/{run_id}', 'read', False, 'ui_backtest_forensics/v1'),
    UiPublicFacadeRoute('GET', '/ui/promotion-review', 'read', False, 'ui_promotion_review/v1'),
    UiPublicFacadeRoute('GET', '/ui/promotion-review/latest', 'read', False, 'ui_promotion_review/v1'),
    UiPublicFacadeRoute('GET', '/ui/paper-tracking/latest', 'read', False, 'ui_paper_tracking/v2'),
    UiPublicFacadeRoute('GET', '/ui/paper-tracking/{tracking_id}', 'read', False, 'ui_paper_tracking/v2'),
    UiPublicFacadeRoute('GET', '/ui/paper-broker/status', 'read', False, 'ui_paper_broker/v1'),
    UiPublicFacadeRoute('GET', '/ui/paper-execution', 'read', False, 'ui_paper_execution_cockpit/v1'),
    UiPublicFacadeRoute('GET', '/ui/paper-execution/latest', 'read', False, 'ui_paper_execution_cockpit/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-memory/latest', 'read', False, 'ui_strategy_memory/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-graveyard', 'read', False, 'ui_strategy_graveyard/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-graveyard/latest', 'read', False, 'ui_strategy_graveyard/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-intake/latest', 'read', False, 'ui_strategy_intake/v1'),
    UiPublicFacadeRoute('POST', '/ui/strategy-intake', 'mutation', True, 'strategy_intake_receipt/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-thesis/latest', 'read', False, 'ui_strategy_thesis/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-thesis/generation/latest', 'read', False, 'ui_strategy_thesis_generation/v1'),
    UiPublicFacadeRoute('GET', '/ui/shadow-book/latest', 'read', False, 'ui_shadow_book/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/status', 'read', False, 'ui_research_os_status/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/closure/latest', 'read', False, 'ui_research_os_closure/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/attestation/latest', 'read', False, 'ui_research_os_attestation/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/briefing/latest', 'read', False, 'ui_research_os_briefing/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/export/latest', 'read', False, 'ui_research_os_export/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/run/latest', 'read', False, 'ui_research_os_operator_run/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/catalog/latest', 'read', False, 'ui_research_os_evidence_catalog/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/drift/latest', 'read', False, 'ui_research_os_evidence_drift/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/policy-gate/latest', 'read', False, 'ui_research_os_policy_gate/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/exceptions/latest', 'read', False, 'ui_research_os_exception/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/remediation/latest', 'read', False, 'ui_research_os_remediation/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/release-readiness/latest', 'read', False, 'ui_research_os_release_readiness/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/handoff/latest', 'read', False, 'ui_research_os_handoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/handoff-signoff/latest', 'read', False, 'ui_research_os_handoff_signoff/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-os/review-journal/latest', 'read', False, 'ui_research_os_review_journal/v1'),
    UiPublicFacadeRoute('POST', UI_COMMAND_MUTATION_ROUTE, 'mutation', True, 'ui_command_mutation/v1'),
)


def build_ui_public_facade_inventory(repo_root: Path | None = None) -> dict[str, object]:
    frontend_present, frontend_status = _frontend_status(repo_root)
    readiness_claim = load_frontend_readiness_claim(repo_root)
    readiness_claimed = bool(readiness_claim.get("frontend_readiness_claimed"))
    inventory = UiPublicFacadeInventory(
        schema_version=UI_PUBLIC_FACADE_SCHEMA_VERSION,
        surface=UI_PUBLIC_FACADE_SURFACE,
        frontend_expected_package=UI_FRONTEND_EXPECTED_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_package_detected_by_backend=frontend_present,
        frontend_status=frontend_status,
        frontend_readiness_claimed=readiness_claimed,
        frontend_runtime_reachable=readiness_claim.get("frontend_runtime_reachable") if readiness_claimed else None,
        frontend_operator_console_hint=_FRONTEND_OPERATOR_CONSOLE_HINT,
        read_plane_only=True,
        mutation_route=UI_COMMAND_MUTATION_ROUTE,
        routes=_UI_PUBLIC_FACADE_ROUTES,
    )
    return inventory.to_payload()


def build_ui_provider_health_payload(repo_root: Path | None = None) -> dict[str, object]:
    """Read-plane provider health for operators (no secrets; uses process env + optional manifest env)."""
    root = repo_root or Path.cwd()
    snap = build_provider_health_snapshot(env=os.environ, repo_root=root)
    return provider_health_snapshot_public_payload(snap)


__all__ = [
    'UI_COMMAND_MUTATION_ROUTE',
    'UI_FRONTEND_EXPECTED_PACKAGE',
    'UI_PUBLIC_FACADE_SCHEMA_VERSION',
    'UI_PUBLIC_FACADE_SURFACE',
    'build_ui_public_facade_inventory',
    'build_ui_provider_health_payload',
]
