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


def test_single_tenant_evidence_rejects_symlinked_reports(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    real_report = tmp_path / "real-acceptance.json"
    real_report.write_text(
        '{"schema_version":"single_tenant_deployment_acceptance/v1","ok":true}\n',
        encoding="utf-8",
    )
    symlinked_report = tmp_path / "deployment-acceptance.json"
    try:
        symlinked_report.symlink_to(real_report)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_evidence(evidence_dir=tmp_path, final=False)
    acceptance = next(item for item in report.files if item.name == "acceptance")

    assert report.ok is False
    assert acceptance.status == "FAIL"
    assert "symlink" in acceptance.detail


def test_single_tenant_evidence_rejects_frontend_readiness_claimed_checkpoint(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    (tmp_path / "frontend-checkpoint.json").write_text(
        "{"
        '"schema_version":"single_tenant_frontend_readiness/v1",'
        '"deployment_model":"single_tenant",'
        '"frontend_readiness_claimed":true,'
        '"claim_status":"CLAIMED",'
        '"ok":true'
        "}\n",
        encoding="utf-8",
    )

    report = build_single_tenant_deployment_evidence(evidence_dir=tmp_path, final=False)
    checkpoint = next(item for item in report.files if item.name == "frontend_checkpoint")

    assert report.ok is False
    assert checkpoint.status == "FAIL"
    assert "frontend checkpoint claims readiness" in checkpoint.detail
    assert report.frontend_readiness_claimed is False


def test_single_tenant_evidence_accepts_non_claiming_frontend_checkpoint(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    (tmp_path / "frontend-checkpoint.json").write_text(
        "{"
        '"schema_version":"single_tenant_frontend_readiness/v1",'
        '"deployment_model":"single_tenant",'
        '"frontend_readiness_claimed":false,'
        '"claim_status":"NOT_CLAIMED",'
        '"ok":false'
        "}\n",
        encoding="utf-8",
    )

    report = build_single_tenant_deployment_evidence(evidence_dir=tmp_path, final=False)
    checkpoint = next(item for item in report.files if item.name == "frontend_checkpoint")

    assert report.ok is True
    assert checkpoint.status == "PASS"
    assert checkpoint.schema_version == "single_tenant_frontend_readiness/v1"
    assert report.frontend_readiness_claimed is False


def test_single_tenant_evidence_rejects_symlinked_override_report(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    real_report = tmp_path / "real-acceptance.json"
    real_report.write_text(
        '{"schema_version":"single_tenant_deployment_acceptance/v1","ok":true}\n',
        encoding="utf-8",
    )
    symlinked_override = tmp_path / "override-acceptance.json"
    try:
        symlinked_override.symlink_to(real_report)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_evidence(
        evidence_dir=tmp_path / "evidence",
        final=False,
        report_overrides={"acceptance": symlinked_override},
    )
    acceptance = next(item for item in report.files if item.name == "acceptance")

    assert report.ok is False
    assert acceptance.status == "FAIL"
    assert "symlink" in acceptance.detail


def test_single_tenant_evidence_rejects_symlinked_evidence_directory(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    real_evidence = tmp_path / "real-evidence"
    real_evidence.mkdir()
    linked_evidence = tmp_path / "evidence"
    try:
        linked_evidence.symlink_to(real_evidence, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_evidence(evidence_dir=linked_evidence, final=True)

    assert report.ok is False
    assert any("evidence directory contains symlink component" in error for error in report.errors)
    assert report.files == ()


def test_single_tenant_evidence_reports_non_regular_report_paths(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_evidence import (
        build_single_tenant_deployment_evidence,
    )

    (tmp_path / "deployment-acceptance.json").mkdir()

    report = build_single_tenant_deployment_evidence(evidence_dir=tmp_path, final=False)
    acceptance = next(item for item in report.files if item.name == "acceptance")

    assert report.ok is False
    assert acceptance.status == "FAIL"
    assert "not a regular file" in acceptance.detail


def test_single_tenant_evidence_rejects_symlinked_output_paths(tmp_path, capsys):
    from strategy_validator.cli.single_tenant_deployment_evidence import main

    real_manifest = tmp_path / "real-manifest.json"
    linked_manifest = tmp_path / "deployment-evidence.json"
    try:
        linked_manifest.symlink_to(real_manifest)
    except (OSError, NotImplementedError):
        return

    exit_code = main([
        "--evidence-dir",
        str(tmp_path / "evidence"),
        "--manifest-output-path",
        str(linked_manifest),
        "--require-pass",
        "--json",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert any("evidence manifest output path contains symlink component" in error for error in payload["errors"])
    assert real_manifest.exists() is False
