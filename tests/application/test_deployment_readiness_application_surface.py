from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.readiness import get_deployment_readiness_payload
from strategy_validator.contracts.operational import DeploymentReadinessTierReport


class _FakeReport(DeploymentReadinessTierReport):
    pass


def test_deployment_readiness_payload_is_transport_neutral(monkeypatch) -> None:
    report = DeploymentReadinessTierReport(
        status="DEGRADED",
        checked_at_utc=datetime(2026, 4, 28, tzinfo=timezone.utc),
        runtime_readiness_status="READY",
        config_fingerprint="abc123",
        blockers=[],
        warnings=[],
        checks={"runtime_ready": True, "ledger_backup_dir_configured": False},
        ledger_database_path="/tmp/ledger.sqlite3",
        ledger_backup_dir=None,
        private_key_file_count=0,
        scanned_key_file_count=2,
    )
    monkeypatch.setattr(
        "strategy_validator.application.readiness.perform_deployment_readiness_check",
        lambda repo_root=None: report,
    )

    payload = get_deployment_readiness_payload(repo_root=".")

    assert payload["surface"] == "deployment_readiness"
    assert payload["ok"] is False
    assert payload["status"] == "DEGRADED"
    assert payload["canonical_status"] == "DEGRADED"
    assert payload["runtime_readiness_status"] == "READY"
    assert payload["checks"]["ledger_backup_dir_configured"] is False


def test_deployment_readiness_summary_reports_operator_action(monkeypatch) -> None:
    from strategy_validator.application.readiness import summarize_deployment_readiness_payload

    report = DeploymentReadinessTierReport(
        status="DEGRADED",
        checked_at_utc=datetime(2026, 4, 28, tzinfo=timezone.utc),
        runtime_readiness_status="READY",
        config_fingerprint="abc123",
        blockers=[],
        warnings=[],
        checks={"runtime_ready": True, "ledger_backup_dir_configured": False},
        ledger_database_path="/tmp/ledger.sqlite3",
        ledger_backup_dir=None,
    )
    monkeypatch.setattr(
        "strategy_validator.application.readiness.perform_deployment_readiness_check",
        lambda repo_root=None: report,
    )

    payload = summarize_deployment_readiness_payload(repo_root=".")

    assert payload["schema_version"] == "deployment_readiness_summary/v1"
    assert payload["ok"] is False
    assert payload["canonical_status"] == "DEGRADED"
    assert payload["recommended_action"] == "DEPLOY_WITH_GOVERNED_EXCEPTION_OR_FIX_WARNINGS"
    assert payload["failed_checks"] == ["ledger_backup_dir_configured"]
