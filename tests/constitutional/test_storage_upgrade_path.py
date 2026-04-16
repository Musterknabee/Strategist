from __future__ import annotations

from pathlib import Path

from strategy_validator.validator.observability import compute_heartbeat
from strategy_validator.validator.readiness import generate_operational_diagnostics, perform_readiness_check


def test_readiness_and_observability_expose_truthful_storage_upgrade_posture() -> None:
    readiness = perform_readiness_check()
    heartbeat = compute_heartbeat()
    diagnostics = generate_operational_diagnostics()

    assert readiness.storage_backend == 'sqlite_single_node'
    assert readiness.storage_upgrade_status == 'PATH_DECLARED_NOT_IMPLEMENTED'
    assert 'SQLite' in readiness.storage_upgrade_summary

    assert heartbeat.storage_backend == readiness.storage_backend
    assert heartbeat.storage_upgrade_status == readiness.storage_upgrade_status
    assert diagnostics.storage_backend == readiness.storage_backend
    assert diagnostics.storage_upgrade_status == readiness.storage_upgrade_status


def test_storage_upgrade_path_runbook_is_checked_in() -> None:
    runbook = Path('docs/STORAGE_UPGRADE_PATH.md').read_text(encoding='utf-8')

    assert 'sqlite_single_node' in runbook
    assert 'PATH_DECLARED_NOT_IMPLEMENTED' in runbook
    assert 'strategy-validator-migrate' in runbook
