from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_deployment_bundle_is_secret_safe_and_backend_only():
    text=(ROOT/"strategy_validator/cli/single_tenant_deployment_bundle.py").read_text()
    for item in ["single_tenant_deployment_bundle/v1","deployment.env.redacted.json","docker-compose.single-tenant.yml","systemd/strategy-validator.service","frontend_readiness_claimed","STRATEGY_VALIDATOR_API_TOKEN"]:
        assert item in text


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


def test_single_tenant_bundle_generation_self_checks_generated_contract(monkeypatch, tmp_path):
    """Generation must fail closed if a generated template drifts before manifest creation."""

    from strategy_validator.cli import single_tenant_deployment_bundle as bundle

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)

    original_systemd_template = bundle._systemd_template

    def drifted_systemd_template() -> str:
        return original_systemd_template().replace(
            "127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000",
            "0.0.0.0:8000:8000",
        )

    monkeypatch.setattr(bundle, "_systemd_template", drifted_systemd_template)

    report = bundle.build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=tmp_path / "bundle",
        repo_root=ROOT,
        force=True,
    )

    assert report.ok is False
    assert any("generated systemd runtime contract drift" in error for error in report.errors)

    import json

    manifest = json.loads((tmp_path / "bundle" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["ok"] is False
    assert any("generated systemd runtime contract drift" in error for error in manifest["errors"])


def test_single_tenant_bundle_check_rejects_symlinked_generated_file(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_bundle import (
        build_single_tenant_deployment_bundle,
        check_single_tenant_deployment_bundle,
    )

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)
    bundle_dir = tmp_path / "bundle"
    generated = build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=bundle_dir,
        repo_root=ROOT,
        force=True,
    )
    assert generated.ok is True

    target = bundle_dir / "README.md"
    symlinked = bundle_dir / "commands" / "api-smoke.sh"
    symlinked.unlink()
    try:
        symlinked.symlink_to(target)
    except (OSError, NotImplementedError):
        return

    checked = check_single_tenant_deployment_bundle(bundle_dir)

    assert checked.ok is False
    assert any("generated file is a symlink: commands/api-smoke.sh" in error for error in checked.errors)
    assert any("manifest-listed generated file is a symlink: commands/api-smoke.sh" in error for error in checked.errors)


def test_single_tenant_bundle_repo_asset_manifest_rejects_symlinked_source_assets(tmp_path):
    from strategy_validator.cli import single_tenant_deployment_bundle as bundle

    repo = tmp_path / "repo"
    for relative in bundle._REQUIRED_REPO_ASSETS:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"regular asset for {relative}\n", encoding="utf-8")

    real_dockerfile = tmp_path / "real-Dockerfile"
    real_dockerfile.write_text("FROM python:3.11-slim\n", encoding="utf-8")
    (repo / "Dockerfile").unlink()
    try:
        (repo / "Dockerfile").symlink_to(real_dockerfile)
    except (OSError, NotImplementedError):
        return

    payload = bundle._repo_asset_manifest(repo, generated_at_utc="2026-05-02T00:00:00Z")
    dockerfile_item = next(item for item in payload["assets"] if item["path"] == "Dockerfile")
    errors = bundle._verify_repo_asset_manifest_payload(payload)

    assert dockerfile_item["exists"] is False
    assert dockerfile_item["is_symlink"] is True
    assert any("repo-assets.manifest.json marks required asset as a symlink: Dockerfile" in error for error in errors)


def test_single_tenant_bundle_rejects_symlinked_env_file(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_bundle import build_single_tenant_deployment_bundle

    real_env = tmp_path / "real.env"
    _write_valid_single_tenant_env(real_env)
    linked_env = tmp_path / "deployment.env"
    try:
        linked_env.symlink_to(real_env)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_bundle(
        env_file=linked_env,
        output_dir=tmp_path / "bundle",
        repo_root=ROOT,
        force=True,
    )

    assert report.ok is False
    assert report.env_check_ok is False
    assert any("deployment env check has ERROR issues" in error for error in report.errors)


def test_single_tenant_bundle_rejects_symlinked_output_directory(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_bundle import build_single_tenant_deployment_bundle

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)
    real_output = tmp_path / "real-bundle"
    real_output.mkdir()
    linked_output = tmp_path / "bundle"
    try:
        linked_output.symlink_to(real_output, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=linked_output,
        repo_root=ROOT,
        force=True,
    )

    assert report.ok is False
    assert any("deployment bundle output directory contains symlink component" in error for error in report.errors)
    assert not (real_output / "manifest.json").exists()


def test_single_tenant_bundle_check_rejects_symlinked_bundle_directory(tmp_path):
    from strategy_validator.cli.single_tenant_deployment_bundle import (
        build_single_tenant_deployment_bundle,
        check_single_tenant_deployment_bundle,
    )

    env_file = tmp_path / "deployment.env"
    _write_valid_single_tenant_env(env_file)
    real_output = tmp_path / "real-bundle"
    generated = build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=real_output,
        repo_root=ROOT,
        force=True,
    )
    assert generated.ok is True
    linked_output = tmp_path / "bundle-link"
    try:
        linked_output.symlink_to(real_output, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    checked = check_single_tenant_deployment_bundle(linked_output)

    assert checked.ok is False
    assert any("deployment bundle directory contains symlink component" in error for error in checked.errors)
