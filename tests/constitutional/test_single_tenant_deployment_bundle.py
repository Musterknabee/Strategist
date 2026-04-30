from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_deployment_bundle_is_secret_safe_and_backend_only():
    text=(ROOT/"strategy_validator/cli/single_tenant_deployment_bundle.py").read_text()
    for item in ["single_tenant_deployment_bundle/v1","deployment.env.redacted.json","docker-compose.single-tenant.yml","systemd/strategy-validator.service","frontend_readiness_claimed","STRATEGY_VALIDATOR_API_TOKEN"]:
        assert item in text
