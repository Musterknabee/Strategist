from __future__ import annotations

import json
from pathlib import Path

from scripts.branch_cleanup_audit import classify_branch
from scripts.main_release_verification_pack import (
    GateResult,
    _redact_text,
    _resolve_summary_path,
    build_markdown_summary,
    main,
    redacted_environment_snapshot,
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
    code = main(["--output-dir", str(output_dir), "--no-frontend", "--no-pytest-full"])
    assert code == 0

    payload = json.loads((output_dir / "main-release-verification-pack.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "main_release_verification_pack/v1"
    assert payload["status"] == "FAIL"
    assert payload["failed_step"] == "bad_step"
    assert isinstance(payload["command_results"], list)
    assert payload["command_results"][1]["name"] == "bad_step"
    assert "disclaimers" in payload and len(payload["disclaimers"]) >= 5

    code_require = main(["--output-dir", str(output_dir), "--no-frontend", "--no-pytest-full", "--require-pass"])
    assert code_require == 1


def test_main_writes_markdown_under_output_dir_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("scripts.main_release_verification_pack._backend_commands", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._frontend_commands", lambda: [])
    monkeypatch.setattr("scripts.main_release_verification_pack._git_head_sha", lambda: "abc123")
    monkeypatch.setattr("scripts.main_release_verification_pack._git_branch", lambda: "main")
    monkeypatch.setattr("scripts.main_release_verification_pack._dirty_tree_status", lambda: "CLEAN")

    output_dir = tmp_path / "evidence"
    outside_md = tmp_path / "outside.md"
    code = main(
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
