from __future__ import annotations

from pathlib import Path


def test_docker_compose_manifest_runs_single_api_service_with_mounted_ledger() -> None:
    manifest = Path('docker-compose.yml').read_text(encoding='utf-8')

    assert 'strategy-validator-api' in manifest
    assert '8000:8000' in manifest
    assert '/var/lib/strategy-validator/forensic_ledger.sqlite3' in manifest
    assert './artifacts/runtime:/var/lib/strategy-validator' in manifest


def test_deployment_runbook_documents_migration_backup_and_rollback() -> None:
    runbook = Path('docs/DEPLOYMENT_RUNBOOK.md').read_text(encoding='utf-8')

    assert 'strategy-validator-migrate' in runbook
    assert 'docker compose up -d strategy-validator' in runbook
    assert 'Backup drill' in runbook
    assert 'Rollback drill' in runbook
    assert '/readyz' in runbook
