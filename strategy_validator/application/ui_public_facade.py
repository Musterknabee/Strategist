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
    UiPublicFacadeRoute('GET', '/ui/tribunal', 'read', False, 'ui_tribunal/v1'),
    UiPublicFacadeRoute('GET', '/ui/packs/detail', 'read', False, 'ui_pack_detail/v1'),
    UiPublicFacadeRoute('GET', '/ui/operator-actions', 'read', False, 'operator_action_event_projection_index/v1'),
    UiPublicFacadeRoute('GET', '/ui/evidence-chain', 'read', False, 'ui_evidence_chain/v1'),
    UiPublicFacadeRoute('GET', '/ui/provider-health', 'read', False, 'provider_health_snapshot/v1'),
    UiPublicFacadeRoute('GET', '/ui/provider-setup', 'read', False, 'ui_provider_setup_console/v1'),
    UiPublicFacadeRoute('GET', '/ui/daily-operator-run', 'read', False, 'ui_daily_operator_run/v1'),
    UiPublicFacadeRoute('GET', '/ui/daily-operator-run/latest', 'read', False, 'ui_daily_operator_run/v1'),
    UiPublicFacadeRoute('GET', '/ui/research-compute', 'read', False, 'ui_research_compute/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches/latest', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/strategy-batches/{run_id}', 'read', False, 'ui_strategy_batch/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics', 'read', False, 'ui_backtest_forensics/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics/latest', 'read', False, 'ui_backtest_forensics/v1'),
    UiPublicFacadeRoute('GET', '/ui/backtest-forensics/{run_id}', 'read', False, 'ui_backtest_forensics/v1'),
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
