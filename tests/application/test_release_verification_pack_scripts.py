from __future__ import annotations

import json
from pathlib import Path

from scripts.branch_cleanup_audit import classify_branch, main as branch_cleanup_main
from scripts.main_release_verification_pack import build_markdown_summary, main as release_pack_main, redacted_environment_snapshot
from strategy_validator.application.research_os_paths import (
    resolve_artifact_output_dir,
    resolve_artifact_root,
    safe_relative_artifact_path,
)


def test_redaction_hides_sensitive_env_values() -> None:
    snapshot = redacted_environment_snapshot(
        {
            "STRATEGY_VALIDATOR_API_TOKEN": "abc123",
            "MY_SECRET": "hidden",
            "NORMAL_FLAG": "ok",
        }
    )
    assert snapshot["STRATEGY_VALIDATOR_API_TOKEN"] == "<redacted>"
    assert snapshot["MY_SECRET"] == "<redacted>"
    assert "NORMAL_FLAG" not in snapshot


def test_markdown_summary_includes_status_and_omits_secret_values() -> None:
    payload = {
        "generated_at_utc": "2026-05-05T10:00:00Z",
        "status": "PASS",
        "required_failed_count": 0,
        "gates": [{"name": "source_health", "status": "PASS", "exit_code": 0, "duration_ms": 15}],
    }
    markdown = build_markdown_summary(payload)
    assert "PASS" in markdown
    assert "source_health" in markdown
    assert "abc123" not in markdown


def test_branch_classification_main() -> None:
    category, _note = classify_branch(
        branch_name="main",
        merged_into_main=False,
        has_open_pr=False,
        has_common_ancestor_with_main=True,
    )
    assert category == "KEEP_MAIN"


def test_branch_classification_merged_branch() -> None:
    category, _note = classify_branch(
        branch_name="release/example",
        merged_into_main=True,
        has_open_pr=False,
        has_common_ancestor_with_main=True,
    )
    assert category == "MERGED_SAFE_TO_DELETE"


def test_branch_classification_no_common_ancestor() -> None:
    category, _note = classify_branch(
        branch_name="weird/history",
        merged_into_main=False,
        has_open_pr=False,
        has_common_ancestor_with_main=False,
    )
    assert category == "NO_COMMON_ANCESTOR_DO_NOT_DELETE"


def test_branch_classification_unknown_when_gh_unavailable() -> None:
    category, _note = classify_branch(
        branch_name="release/maybe",
        merged_into_main=False,
        has_open_pr=None,
        has_common_ancestor_with_main=True,
    )
    assert category == "UNKNOWN_DO_NOT_DELETE"


def test_artifact_root_default_and_env_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", raising=False)
    assert resolve_artifact_root(tmp_path) == (tmp_path / "artifacts").resolve()

    custom = tmp_path / "custom-artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(custom))
    assert resolve_artifact_root(tmp_path) == custom.resolve()


def test_artifact_root_rejects_traversal_and_absolute_relative_guard(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "../escape")
    try:
        resolve_artifact_root(tmp_path)
        assert False, "expected ARTIFACT_PATH_TRAVERSAL_FORBIDDEN"
    except ValueError as exc:
        assert str(exc) == "ARTIFACT_PATH_TRAVERSAL_FORBIDDEN"

    try:
        safe_relative_artifact_path("C:/abs/path")
        assert False, "expected ARTIFACT_PATH_MUST_BE_RELATIVE"
    except ValueError as exc:
        assert str(exc) == "ARTIFACT_PATH_MUST_BE_RELATIVE"


def test_output_dir_created_only_when_writing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", raising=False)
    target = resolve_artifact_output_dir(output_dir="release_verification/latest", repo_root=tmp_path, create=False)
    assert target == (tmp_path / "artifacts" / "release_verification" / "latest").resolve()
    assert not target.exists()

    created = resolve_artifact_output_dir(output_dir="release_verification/latest", repo_root=tmp_path, create=True)
    assert created.exists()


def test_release_pack_rejects_output_path_outside_artifact_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.main_release_verification_pack._backend_commands", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._frontend_commands", lambda: [])
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    code = release_pack_main(["--output-dir", str(tmp_path / "outside"), "--no-frontend", "--no-pytest-full"])
    assert code == 2


def test_release_pack_default_output_uses_artifact_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.main_release_verification_pack._backend_commands", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._frontend_commands", lambda: [])
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    code = release_pack_main(["--json", "--no-frontend", "--no-pytest-full"])
    assert code == 0
    output_json = tmp_path / "artifacts" / "release_verification" / "latest" / "main-release-verification-pack.json"
    assert output_json.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["output_dir"].startswith(str((tmp_path / "artifacts").resolve()))


def test_branch_cleanup_rejects_output_outside_artifact_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    code = branch_cleanup_main(["--output-json-path", str(tmp_path / "outside" / "branch-audit.json")])
    assert code == 2
