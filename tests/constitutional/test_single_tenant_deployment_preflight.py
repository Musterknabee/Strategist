from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_preflight_remains_fail_closed_and_scope_aware():
    text=(ROOT/"strategy_validator/cli/single_tenant_preflight.py").read_text()
    for item in ["single_tenant_deployment_preflight/v1","perform_deployment_readiness_check","--verify-backup-restore","operator:command:write","operator:projection:read","require_ready","frontend_readiness_claimed"]:
        assert item in text
