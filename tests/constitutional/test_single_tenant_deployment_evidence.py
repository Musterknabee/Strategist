from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_single_tenant_evidence_bundle_links_required_reports():
    text = (ROOT / "strategy_validator/cli/single_tenant_deployment_evidence.py").read_text()
    for item in [
        "single_tenant_deployment_evidence/v1",
        "deployment_env_check",
        "single_tenant_preflight",
        "single_tenant_api_smoke",
        "single_tenant_deployment_acceptance",
        "sha256",
    ]:
        assert item in text


def test_single_tenant_evidence_final_has_paths_for_all_required_reports(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    # final=True iterates every required report name; must not KeyError on empty dir.
    report = build_single_tenant_deployment_evidence(evidence_dir=tmp_path, final=True)
    assert report.final_evidence is True
    names = {f.name for f in report.files}
    for required in (
        "acceptance",
        "single_tenant_preflight",
        "preflight",
        "single_tenant_api_smoke",
        "api_smoke",
        "ledger_verify",
        "ledger_backup",
    ):
        assert required in names
