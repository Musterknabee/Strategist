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
from scripts.main_release_verification_pack import (
    GateResult,
    _redact_text,
    _resolve_summary_path,
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


def test_redaction_hides_sensitive_values_from_text() -> None:
    raw = "Authorization: Bearer abc123 token=my-token --api-key value password=letmein"
    sanitized = _redact_text(raw)
    assert "abc123" not in sanitized
    assert "my-token" not in sanitized
    assert "letmein" not in sanitized
    assert "Bearer <redacted>" in sanitized


def test_markdown_summary_includes_status_and_omits_secret_values() -> None:
    payload = {
        "generated_at_utc": "2026-05-05T10:00:00Z",
        "git_head_sha": "abc123def",
        "git_branch": "main",
        "dirty_tree_status": "CLEAN",
        "status": "PASS",
        "failed_step": None,
        "blockers": [],
        "warnings": [],
        "command_results": [
            {
                "name": "source_health",
                "status": "PASS",
                "exit_code": 0,
                "duration_seconds": 0.015,
                "stdout_tail": "token=<redacted>",
                "stderr_tail": "",
            }
        ],
    }
    markdown = build_markdown_summary(payload)
    assert "PASS" in markdown
    assert "source_health" in markdown
    assert "Git SHA" in markdown
    assert "Dirty tree status" in markdown
    assert "Not operator signoff." in markdown
    assert "my-secret-token" not in markdown


def test_markdown_summary_includes_failed_step_and_blockers() -> None:
    payload = {
        "generated_at_utc": "2026-05-05T10:00:00Z",
        "git_head_sha": "deadbeef",
        "git_branch": "hardening/test",
        "dirty_tree_status": "DIRTY",
        "status": "FAIL",
        "failed_step": "pytest_api",
        "blockers": ["REQUIRED_STEP_FAILURE"],
        "warnings": ["WORKTREE_DIRTY_DURING_VERIFICATION"],
        "command_results": [{"name": "pytest_api", "status": "FAIL", "exit_code": 1, "duration_seconds": 1.5}],
    }
    markdown = build_markdown_summary(payload)
    assert "Failed step" in markdown
    assert "pytest_api" in markdown
    assert "REQUIRED_STEP_FAILURE" in markdown
    assert "WORKTREE_DIRTY_DURING_VERIFICATION" in markdown


def test_resolve_summary_path_rejects_escape(tmp_path: Path) -> None:
    output_dir = tmp_path / "pack"
    output_dir.mkdir()
    outside = tmp_path / "outside.md"
    try:
        _resolve_summary_path(str(outside), output_dir=output_dir)
        assert False, "expected SUMMARY_PATH_OUTSIDE_OUTPUT_DIR"
    except ValueError as exc:
        assert str(exc) == "SUMMARY_PATH_OUTSIDE_OUTPUT_DIR"


def test_main_require_pass_exit_behavior_and_json_shape(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "scripts.main_release_verification_pack._backend_commands",
        lambda *_args, **_kwargs: [("ok_step", ["python", "-m", "ok"]), ("bad_step", ["python", "-m", "bad"])],
    )
    monkeypatch.setattr("scripts.main_release_verification_pack._frontend_commands", lambda: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._git_head_sha", lambda: "abc123")
    monkeypatch.setattr("scripts.main_release_verification_pack._git_branch", lambda: "hardening/test")
    monkeypatch.setattr("scripts.main_release_verification_pack._dirty_tree_status", lambda: "CLEAN")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path))

    def fake_run(name: str, command: list[str], *, cwd: Path) -> GateResult:
        if name == "bad_step":
            return GateResult(
                name=name,
                command="python -m bad --token <redacted>",
                cwd=str(cwd),
                exit_code=2,
                duration_seconds=0.2,
                status="FAIL",
                stdout_tail="token=<redacted>",
                stderr_tail="password=<redacted>",
            )
        return GateResult(
            name=name,
            command="python -m ok",
            cwd=str(cwd),
            exit_code=0,
            duration_seconds=0.1,
            status="PASS",
            stdout_tail="all good",
            stderr_tail="",
        )

    monkeypatch.setattr("scripts.main_release_verification_pack._run_gate", fake_run)
    output_dir = tmp_path / "evidence"
    code = release_pack_main(["--output-dir", str(output_dir), "--no-frontend", "--no-pytest-full"])
    assert code == 0

    payload = json.loads((output_dir / "main-release-verification-pack.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "main_release_verification_pack/v1"
    assert payload["status"] == "FAIL"
    assert payload["failed_step"] == "bad_step"
    assert isinstance(payload["command_results"], list)
    assert payload["command_results"][1]["name"] == "bad_step"
    assert "disclaimers" in payload and len(payload["disclaimers"]) >= 5

    code_require = release_pack_main(["--output-dir", str(output_dir), "--no-frontend", "--no-pytest-full", "--require-pass"])
    assert code_require == 1


def test_main_writes_markdown_under_output_dir_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("scripts.main_release_verification_pack._backend_commands", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._frontend_commands", lambda: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._git_head_sha", lambda: "abc123")
    monkeypatch.setattr("scripts.main_release_verification_pack._git_branch", lambda: "main")
    monkeypatch.setattr("scripts.main_release_verification_pack._dirty_tree_status", lambda: "CLEAN")

    output_dir = tmp_path / "evidence"
    outside_md = tmp_path / "outside.md"
    code = release_pack_main(
        [
            "--output-dir",
            str(output_dir),
            "--summary-markdown-output-path",
            str(outside_md),
            "--no-frontend",
            "--no-pytest-full",
        ]
    )
    assert code == 2
    assert not outside_md.exists()


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

    absolute_candidate = str((tmp_path / "abs-path-check").resolve())
    try:
        safe_relative_artifact_path(absolute_candidate)
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
