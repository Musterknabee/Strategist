from __future__ import annotations

from pathlib import Path


def test_backend_container_declares_fail_closed_runtime_envelope() -> None:
    dockerfile = Path('Dockerfile')
    assert dockerfile.exists()
    content = dockerfile.read_text(encoding='utf-8')
    assert 'STRATEGY_VALIDATOR_MODE=PRODUCTION' in content
    assert 'STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3' in content
    assert 'STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator' in content
    assert 'STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts' in content
    assert 'STRATEGY_VALIDATOR_API_TOKEN=' not in content
    assert 'USER strategy-validator' in content
    assert 'HEALTHCHECK' in content
    assert 'strategy-validator-api' in content


def test_backend_container_docs_name_required_operator_env() -> None:
    docs = Path('docs/deployment/BACKEND_CONTAINER_V1.md')
    assert docs.exists()
    content = docs.read_text(encoding='utf-8')
    assert 'STRATEGY_VALIDATOR_MODE=PRODUCTION' in content
    assert 'STRATEGY_VALIDATOR_API_TOKEN' in content
    assert 'STRATEGY_VALIDATOR_API_TOKEN_SCOPES' in content
    assert 'replace-me' not in content
    assert '--read-only' in content
    assert '--cap-drop ALL' in content
    assert '--security-opt no-new-privileges:true' in content
    assert 'STRATEGY_VALIDATOR_LEDGER_DB_PATH' in content
    assert 'STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR' in content
    assert 'STRATEGY_VALIDATOR_ARTIFACT_ROOT' in content
    assert 'backend-only' in content.lower()
    assert 'does **not** include a frontend' in content


def test_production_smoke_check_script_uses_readiness_surfaces() -> None:
    script = Path('scripts/production_smoke_check.py')
    assert script.exists()
    content = script.read_text(encoding='utf-8')
    assert 'perform_readiness_check' in content
    assert 'perform_deployment_readiness_check' in content
    assert '--require-ready' in content
