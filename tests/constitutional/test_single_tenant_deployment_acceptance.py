from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_acceptance_requires_env_preflight_smoke_and_restore():
    text=(ROOT/"strategy_validator/cli/single_tenant_deployment_acceptance.py").read_text()
    for item in ["single_tenant_deployment_acceptance/v1","env_check","preflight","api_smoke","frontend_readiness_claimed"]:
        assert item in text
    assert "backup_restore" in text or "restore" in text
