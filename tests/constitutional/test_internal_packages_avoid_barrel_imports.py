from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

_APPLICATION_BARREL_IMPORT_BASELINE = {
    'strategy_validator/application/ui_semantic_validator_handoff_action_queue_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_audit_packet_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_acceptance_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_action_register_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_checklist_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_closeout_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_coverage_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_dossier_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_evidence_matrix_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_gate_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_operations_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_archive_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_closure_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_completion_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_confirmation_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_custody_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_disposal_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_disposition_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_handoff_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_packet_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_readiness_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_receipt_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_release_retention_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_resolution_plan_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_review_docket_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_signoff_packet_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_clearance_verification_board_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_continuity_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_decision_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_evidence_gaps_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_exceptions_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_lineage_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_remediation_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_review_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_runbook_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_signoff_payload.py',
    'strategy_validator/application/ui_semantic_validator_handoff_timeline_payload.py',
}


def _scan_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob('*.py') if '__pycache__' not in path.parts)


def _barrel_import_violations(root: Path, forbidden_import: str) -> list[str]:
    violations: list[str] = []
    needle = f'from {forbidden_import} import'
    for path in _scan_python_files(root):
        text = path.read_text(encoding='utf-8')
        if needle in text:
            violations.append(str(path.relative_to(REPO_ROOT)))
    return violations


def test_validator_modules_do_not_depend_on_control_plane_barrel() -> None:
    violations = _barrel_import_violations(
        REPO_ROOT / 'strategy_validator' / 'validator',
        'strategy_validator.control_plane',
    )
    assert violations == []


def test_internal_application_modules_do_not_depend_on_application_barrel() -> None:
    root = REPO_ROOT / 'strategy_validator' / 'application'
    violations = [
        path.replace('\\', '/')
        for path in _barrel_import_violations(root, 'strategy_validator.application')
        if not path.endswith('strategy_validator/application/__init__.py')
        and path.replace('\\', '/') not in _APPLICATION_BARREL_IMPORT_BASELINE
    ]
    assert violations == []


def test_internal_cli_modules_do_not_depend_on_control_plane_barrels() -> None:
    root = REPO_ROOT / 'strategy_validator' / 'cli'
    control_plane_violations = _barrel_import_violations(root, 'strategy_validator.control_plane')
    application_violations = _barrel_import_violations(root, 'strategy_validator.application')
    assert control_plane_violations == []
    assert application_violations == []
