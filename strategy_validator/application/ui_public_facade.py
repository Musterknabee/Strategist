from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.ui_public_facade import UiPublicFacadeInventory, UiPublicFacadeRoute

UI_PUBLIC_FACADE_SCHEMA_VERSION = 'ui_public_facade_inventory/v1'
UI_PUBLIC_FACADE_SURFACE = 'ui'
UI_FRONTEND_EXPECTED_PACKAGE = 'ui/strategist-web'
UI_COMMAND_MUTATION_ROUTE = '/ui/commands/{action}'


def _frontend_status(repo_root: Path | None = None) -> tuple[bool, str]:
    root = repo_root or Path.cwd()
    package_json = root / UI_FRONTEND_EXPECTED_PACKAGE / 'package.json'
    package_lock = root / UI_FRONTEND_EXPECTED_PACKAGE / 'package-lock.json'
    package_present = package_json.exists() or package_lock.exists()
    if package_present:
        return True, 'package_present_unverified'
    return False, 'absent'


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
    UiPublicFacadeRoute('POST', UI_COMMAND_MUTATION_ROUTE, 'mutation', True, 'ui_command_mutation/v1'),
)


def build_ui_public_facade_inventory(repo_root: Path | None = None) -> dict[str, object]:
    frontend_present, frontend_status = _frontend_status(repo_root)
    inventory = UiPublicFacadeInventory(
        schema_version=UI_PUBLIC_FACADE_SCHEMA_VERSION,
        surface=UI_PUBLIC_FACADE_SURFACE,
        frontend_expected_package=UI_FRONTEND_EXPECTED_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_status=frontend_status,
        frontend_readiness_claimed=False,
        read_plane_only=True,
        mutation_route=UI_COMMAND_MUTATION_ROUTE,
        routes=_UI_PUBLIC_FACADE_ROUTES,
    )
    return inventory.to_payload()


__all__ = [
    'UI_COMMAND_MUTATION_ROUTE',
    'UI_FRONTEND_EXPECTED_PACKAGE',
    'UI_PUBLIC_FACADE_SCHEMA_VERSION',
    'UI_PUBLIC_FACADE_SURFACE',
    'build_ui_public_facade_inventory',
]
