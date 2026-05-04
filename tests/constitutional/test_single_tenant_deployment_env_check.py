from pathlib import Path

from strategy_validator.cli.deployment_env_check import build_single_tenant_deployment_env_check

ROOT = Path(__file__).resolve().parents[2]


def test_single_tenant_env_checker_validates_production_token_scopes_and_paths():
    text = (ROOT / "strategy_validator/cli/deployment_env_check.py").read_text()
    for item in [
        "single_tenant_deployment_env_check/v1",
        "STRATEGY_VALIDATOR_MODE",
        "STRATEGY_VALIDATOR_API_TOKEN",
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
        "operator:command:write",
        "operator:projection:read",
        "is_placeholder_token",
    ]:
        assert item in text
    assert "must be absolute" in text or "NOT_ABSOLUTE" in text


def test_container_posix_paths_in_env_file_are_absolute_on_windows_hosts(tmp_path: Path) -> None:
    """Regression: pathlib.Path('/var/...') is not absolute on Windows; checker must use POSIX rules."""

    env = tmp_path / "deployment.env"
    env.write_text(
        "STRATEGY_VALIDATOR_MODE=PRODUCTION\n"
        "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890\n"
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read\n"
        "STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3\n"
        "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator\n"
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts\n",
        encoding="utf-8",
    )
    env.chmod(0o600)
    report = build_single_tenant_deployment_env_check(env)
    assert report.ok is True
    err_codes = {i.code for i in report.issues if i.severity == "ERROR"}
    assert err_codes == set()


def test_single_tenant_env_checker_rejects_symlinked_env_file(tmp_path: Path) -> None:
    real_env = tmp_path / "real.env"
    real_env.write_text(
        "STRATEGY_VALIDATOR_MODE=PRODUCTION\n"
        "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890\n"
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read\n"
        "STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3\n"
        "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator\n"
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts\n",
        encoding="utf-8",
    )
    real_env.chmod(0o600)
    linked_env = tmp_path / "deployment.env"
    try:
        linked_env.symlink_to(real_env)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_env_check(linked_env)
    codes = {issue.code for issue in report.issues}

    assert report.ok is False
    assert "ENV_FILE_IS_SYMLINK" in codes


def test_single_tenant_env_checker_rejects_env_file_under_symlinked_parent(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    env = real_dir / "deployment.env"
    env.write_text(
        "STRATEGY_VALIDATOR_MODE=PRODUCTION\n"
        "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890\n"
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read\n"
        "STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3\n"
        "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator\n"
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts\n",
        encoding="utf-8",
    )
    env.chmod(0o600)
    linked_dir = tmp_path / "linked"
    try:
        linked_dir.symlink_to(real_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_env_check(linked_dir / "deployment.env")
    codes = {issue.code for issue in report.issues}

    assert report.ok is False
    assert "ENV_FILE_PARENT_IS_SYMLINK" in codes
