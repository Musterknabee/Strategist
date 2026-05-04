from __future__ import annotations

from pathlib import Path

import pytest

from strategy_validator.ledger._append_only import resolve_database_path
from strategy_validator.validator.readiness import perform_readiness_check


def _configure_runtime_ledger(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "aB9xY7qP4mN2rS8tV6wZ3cD5eF1gH0jK")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN_SCOPES", "operator:command:write,operator:projection:read")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(path))


def test_runtime_ledger_resolver_rejects_symlinked_database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_db = tmp_path / "real.sqlite3"
    real_db.write_bytes(b"")
    linked_db = tmp_path / "ledger.sqlite3"
    linked_db.symlink_to(real_db)
    _configure_runtime_ledger(monkeypatch, linked_db)

    with pytest.raises(RuntimeError) as exc_info:
        resolve_database_path()

    assert "LEDGER_DATABASE_PATH_IS_SYMLINK" in str(exc_info.value)


def test_runtime_ledger_resolver_rejects_database_under_symlinked_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_dir = tmp_path / "real-ledger"
    real_dir.mkdir()
    linked_dir = tmp_path / "linked-ledger"
    linked_dir.symlink_to(real_dir, target_is_directory=True)
    _configure_runtime_ledger(monkeypatch, linked_dir / "ledger.sqlite3")

    with pytest.raises(RuntimeError) as exc_info:
        resolve_database_path()

    assert "LEDGER_DATABASE_PATH_PARENT_IS_SYMLINK" in str(exc_info.value)


def test_runtime_readiness_surfaces_ledger_symlink_blocker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_db = tmp_path / "real.sqlite3"
    real_db.write_bytes(b"")
    linked_db = tmp_path / "ledger.sqlite3"
    linked_db.symlink_to(real_db)
    _configure_runtime_ledger(monkeypatch, linked_db)

    readiness = perform_readiness_check()

    assert readiness.status == "BLOCKED"
    assert any("LEDGER_DATABASE_PATH_IS_SYMLINK" in blocker.message for blocker in readiness.blockers)
