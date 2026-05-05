from scripts.branch_cleanup_audit import classify_branch
from scripts.main_release_verification_pack import build_markdown_summary, redacted_environment_snapshot


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
