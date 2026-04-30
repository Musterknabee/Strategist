from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_evidence_bundle_links_required_reports():
    text=(ROOT/"strategy_validator/cli/single_tenant_deployment_evidence.py").read_text()
    for item in ["single_tenant_deployment_evidence/v1","deployment_env_check","single_tenant_preflight","single_tenant_api_smoke","single_tenant_deployment_acceptance","sha256"]:
        assert item in text
