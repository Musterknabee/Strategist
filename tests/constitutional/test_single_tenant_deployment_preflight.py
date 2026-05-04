from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_preflight_remains_fail_closed_and_scope_aware():
    text=(ROOT/"strategy_validator/cli/single_tenant_preflight.py").read_text()
    for item in ["single_tenant_deployment_preflight/v1","perform_deployment_readiness_check","--verify-backup-restore","operator:command:write","operator:projection:read","require_ready","frontend_readiness_claimed"]:
        assert item in text


def _set_single_tenant_preflight_env(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "abcdefghijklmnopqrstuvwxyz1234567890TOKEN")
    monkeypatch.setenv(
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
        "operator:command:write,operator:projection:read",
    )


def test_single_tenant_preflight_rejects_symlinked_durable_database_path(monkeypatch, tmp_path):
    from strategy_validator.cli.single_tenant_preflight import build_single_tenant_deployment_preflight

    _set_single_tenant_preflight_env(monkeypatch)
    real_db = tmp_path / "outside-ledger.sqlite3"
    linked_db = tmp_path / "ledger.sqlite3"
    try:
        linked_db.symlink_to(real_db)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_preflight(
        repo_root=ROOT,
        database_path=str(linked_db),
        backup_dir=str(tmp_path / "backups"),
        artifact_root=str(tmp_path / "artifacts"),
        prepare=True,
    )

    assert report["ok"] is False
    assert report["checks"]["deployment_paths_not_symlinked"] is False
    assert report["preparation"]["path_integrity"]["ok"] is False
    assert any("SYMLINK_IN_DURABLE_PATH" in error for error in report["errors"])
    assert report["preparation"]["migration"] is None
    assert real_db.exists() is False


def test_single_tenant_preflight_rejects_symlinked_restore_drill_path(monkeypatch, tmp_path):
    from strategy_validator.cli.single_tenant_preflight import build_single_tenant_deployment_preflight

    _set_single_tenant_preflight_env(monkeypatch)
    real_restore = tmp_path / "outside-restore.sqlite3"
    linked_restore = tmp_path / "restore-drill.sqlite3"
    try:
        linked_restore.symlink_to(real_restore)
    except (OSError, NotImplementedError):
        return

    report = build_single_tenant_deployment_preflight(
        repo_root=ROOT,
        database_path=str(tmp_path / "ledger.sqlite3"),
        backup_dir=str(tmp_path / "backups"),
        artifact_root=str(tmp_path / "artifacts"),
        prepare=True,
        verify_backup_restore=True,
        restore_drill_path=str(linked_restore),
    )

    assert report["ok"] is False
    assert report["checks"]["deployment_paths_not_symlinked"] is False
    assert report["backup_restore_drill"]["ok"] is False
    assert report["backup_restore_drill"]["error"] == "skipped because durable deployment path integrity failed"
    assert real_restore.exists() is False


def test_single_tenant_preflight_rejects_symlinked_summary_output_path(monkeypatch, tmp_path, capsys):
    from strategy_validator.cli.single_tenant_preflight import main

    _set_single_tenant_preflight_env(monkeypatch)
    real_summary = tmp_path / "real-summary.md"
    linked_summary = tmp_path / "summary.md"
    try:
        linked_summary.symlink_to(real_summary)
    except (OSError, NotImplementedError):
        return

    exit_code = main([
        "--repo-root",
        str(ROOT),
        "--database-path",
        str(tmp_path / "ledger.sqlite3"),
        "--backup-dir",
        str(tmp_path / "backups"),
        "--artifact-root",
        str(tmp_path / "artifacts"),
        "--summary-markdown-output-path",
        str(linked_summary),
        "--require-ready",
        "--json",
    ])
    payload = __import__("json").loads(capsys.readouterr().out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["checks"]["summary_markdown_output_path_not_symlinked"] is False
    assert any("SYMLINK_IN_OUTPUT_PATH" in error for error in payload["errors"])
    assert real_summary.exists() is False
