from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_acceptance_requires_env_preflight_smoke_and_restore():
    text=(ROOT/"strategy_validator/cli/single_tenant_deployment_acceptance.py").read_text()
    for item in ["single_tenant_deployment_acceptance/v1","env_check","preflight","api_smoke","frontend_readiness_claimed"]:
        assert item in text
    assert "backup_restore" in text or "restore" in text


def test_single_tenant_acceptance_rejects_symlinked_repo_assets(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_acceptance import _required_repo_asset_checks

    repo = tmp_path / "repo"
    for relative in ("Dockerfile",):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("regular\n", encoding="utf-8")

    real_dockerfile = tmp_path / "real-Dockerfile"
    real_dockerfile.write_text("FROM python:3.11-slim\n", encoding="utf-8")
    (repo / "Dockerfile").unlink()
    try:
        (repo / "Dockerfile").symlink_to(real_dockerfile)
    except (OSError, NotImplementedError):
        return

    checks = _required_repo_asset_checks(repo)
    dockerfile = next(check for check in checks if check.name == "repo_asset:Dockerfile")

    assert dockerfile.status == "FAIL"
    assert "symlink" in dockerfile.detail


def _write_valid_single_tenant_env(path: Path) -> None:
    path.write_text(
        "STRATEGY_VALIDATOR_MODE=PRODUCTION\n"
        "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890TOKEN\n"
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read\n"
        "STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3\n"
        "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator\n"
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def test_single_tenant_acceptance_rejects_symlinked_env_file(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_acceptance import (
        build_single_tenant_deployment_acceptance,
    )

    real_env = tmp_path / "real.env"
    _write_valid_single_tenant_env(real_env)
    linked_env = tmp_path / "deployment.env"
    try:
        linked_env.symlink_to(real_env)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_acceptance(env_file=linked_env, repo_root=ROOT)
    issue_codes = {issue["code"] for issue in report.env_check["issues"]}

    assert report.ok is False
    assert "ENV_FILE_IS_SYMLINK" in issue_codes


def test_single_tenant_acceptance_rejects_symlinked_bundle_directory(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_acceptance import (
        build_single_tenant_deployment_acceptance,
    )
    from strategy_validator.cli.single_tenant_deployment_bundle import build_single_tenant_deployment_bundle

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)
    real_bundle = tmp_path / "real-bundle"
    generated = build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=real_bundle,
        repo_root=ROOT,
        force=True,
    )
    assert generated.ok is True
    linked_bundle = tmp_path / "bundle-link"
    try:
        linked_bundle.symlink_to(real_bundle, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_acceptance(
        env_file=env_file,
        bundle_dir=linked_bundle,
        repo_root=ROOT,
    )

    assert report.ok is False
    check = next(item for item in report.checks if item.name == "deployment_bundle_path_not_symlinked")
    assert check.status == "FAIL"
    assert "symlink" in check.detail


def test_single_tenant_acceptance_rejects_symlinked_markdown_output_path(tmp_path, capsys):
    from strategy_validator.cli.single_tenant_deployment_acceptance import main

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)
    real_report = tmp_path / "real-summary.md"
    linked_report = tmp_path / "summary.md"
    try:
        linked_report.symlink_to(real_report)
    except (OSError, NotImplementedError):
        return

    exit_code = main([
        "--env-file",
        str(env_file),
        "--repo-root",
        str(ROOT),
        "--summary-markdown-output-path",
        str(linked_report),
        "--require-ready",
        "--json",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert any(check["name"] == "summary_markdown_output_path_not_symlinked" for check in payload["checks"])
    assert real_report.exists() is False
