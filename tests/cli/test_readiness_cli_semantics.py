from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.deployment_env_check import EnvCheckReport
from strategy_validator.cli.operator_doctor import build_operator_doctor_report


def test_deployment_env_check_report_exposes_canonical_status() -> None:
    ok_report = EnvCheckReport(
        schema_version="single_tenant_deployment_env_check/v1",
        ok=True,
        env_file="deployment.env",
        checked_key_count=1,
        required_key_count=1,
        issue_count=0,
        warning_count=1,
        issues=(),
        values={},
    )
    blocked_report = EnvCheckReport(
        schema_version="single_tenant_deployment_env_check/v1",
        ok=False,
        env_file="deployment.env",
        checked_key_count=1,
        required_key_count=1,
        issue_count=1,
        warning_count=0,
        issues=(),
        values={},
    )
    assert ok_report.to_payload()["canonical_status"] == "WARN"
    assert blocked_report.to_payload()["canonical_status"] == "BLOCKED"


def test_operator_doctor_exposes_canonical_status(tmp_path: Path) -> None:
    payload = build_operator_doctor_report(repo_root=tmp_path, env_file=tmp_path / "missing.env")
    assert payload["status"] in {"PASS", "WARN", "FAIL"}
    assert payload["canonical_status"] in {"OK", "WARN", "BLOCKED", "UNKNOWN"}
