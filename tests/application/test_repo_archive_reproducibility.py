from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.package_repo import build_clean_repo_zip, iter_clean_repo_files, main as package_repo_main
from scripts.verify_repo_archive import main as verify_repo_archive_main, verify_clean_repo_archive


def _make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    (repo / "strategy_validator").mkdir()
    (repo / "strategy_validator" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "tool.py").write_text("print('tool')\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return repo


def test_clean_archive_excludes_env_cache_and_secret_material(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".env").write_text("API_TOKEN=secret\n", encoding="utf-8")
    (repo / "deployment.env").write_text("STRATEGY_VALIDATOR_API_TOKEN=secret\n", encoding="utf-8")
    (repo / "ui").mkdir()
    (repo / "ui" / "strategist-web").mkdir(parents=True, exist_ok=True)
    (repo / "ui" / "strategist-web" / ".next").mkdir()
    (repo / "ui" / "strategist-web" / ".next" / "cache.bin").write_text("cache", encoding="utf-8")
    (repo / "strategy_validator" / "local.sqlite3").write_text("db", encoding="utf-8")
    (repo / "strategy_validator" / "private.key").write_text("key", encoding="utf-8")

    included = sorted(path.relative_to(repo).as_posix() for path in iter_clean_repo_files(repo))
    assert ".env" not in included
    assert "deployment.env" not in included
    assert "ui/strategist-web/.next/cache.bin" not in included
    assert "strategy_validator/local.sqlite3" not in included
    assert "strategy_validator/private.key" not in included
    assert "strategy_validator/app.py" in included


def test_clean_archive_is_reproducible(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    first_report = build_clean_repo_zip(repo_root=repo, output_path=first)
    second_report = build_clean_repo_zip(repo_root=repo, output_path=second)

    assert first_report.archive_sha256 is not None
    assert first_report.archive_sha256 == second_report.archive_sha256


def test_verify_rejects_path_traversal_entries(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as handle:
        info = zipfile.ZipInfo("../evil.txt")
        info.date_time = (1980, 1, 1, 0, 0, 0)
        info.external_attr = 0o644 << 16
        handle.writestr(info, b"evil")

    report = verify_clean_repo_archive(archive, repo_root=repo)
    assert report.status == "FAIL"
    assert any(f.name == "entry_path_traversal" for f in report.failures)
    assert report.schema_version == "repo_archive_verify/v1"


def test_package_repo_json_shape_on_check(tmp_path: Path, capsys) -> None:
    repo = _make_repo(tmp_path)
    code = package_repo_main(["--repo-root", str(repo), "--check", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "clean_repo_archive/v2"
    assert payload["status"] == "PASS"
    assert "exclusions_applied" in payload
    assert "warnings" in payload
    assert "blockers" in payload


def test_verify_repo_archive_main_non_zero_on_failure(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as handle:
        handle.writestr("extra.txt", b"x")

    code = verify_repo_archive_main([str(archive), "--repo-root", str(repo), "--json"])
    assert code == 1
