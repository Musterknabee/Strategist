from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.application.ui_evidence_cockpit_summary import build_ui_evidence_cockpit_fields
from strategy_validator.application.ui_views import build_ui_evidence_payload


def test_cockpit_fields_unknown_when_no_artifacts(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=None,
    )
    assert fields["deployment_status"] == "UNKNOWN"
    assert fields["deployment_evidence_ok"] is None
    assert fields.get("deployment_evidence_manifest_path") is None
    assert fields["api_smoke_status"] == "UNKNOWN"
    assert fields["api_smoke_ok"] is None
    assert fields["frontend_readiness_status"] == "UNKNOWN"
    assert fields["operator_decision"] == "UNKNOWN"
    assert fields["manual_operator_signoff_present"] is None


def test_cockpit_from_deployment_manifest(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "single_tenant_deployment_evidence/v1",
        "ok": True,
        "generated_at_utc": "2026-04-01T12:00:00Z",
        "frontend_readiness_claimed": False,
        "files": [
            {"name": "api_smoke", "ok_field": True, "status": "PASS"},
            {"name": "ledger_verify", "ok_field": True, "status": "PASS"},
            {"name": "ledger_backup", "ok_field": False, "status": "FAIL"},
            {"name": "ci_local_verify", "ok_field": True, "status": "PASS"},
        ],
    }
    (tmp_path / "deployment-evidence.json").write_text(json.dumps(manifest), encoding="utf-8")
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=None,
    )
    assert fields["deployment_status"] == "PASS"
    assert fields["deployment_evidence_ok"] is True
    assert fields["api_smoke_ok"] is True
    assert fields["api_smoke_status"] == "PASS"
    assert fields["ledger_integrity_ok"] is True
    assert fields["backup_restore_ok"] is False
    assert fields["ci_local_verify_ok"] is True
    assert fields["frontend_readiness_status"] == "NOT_CLAIMED"
    assert fields["evidence_generated_at_utc"] == "2026-04-01T12:00:00Z"
    assert fields.get("deployment_evidence_manifest_path")
    assert str(tmp_path / "deployment-evidence.json") in str(fields["deployment_evidence_manifest_path"])


def test_cockpit_ignores_wrong_manifest_schema(tmp_path: Path) -> None:
    (tmp_path / "deployment-evidence.json").write_text(
        json.dumps({"schema_version": "other", "ok": True}),
        encoding="utf-8",
    )
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=None,
    )
    assert fields["deployment_status"] == "UNKNOWN"
    assert fields.get("deployment_evidence_manifest_path")
    assert "deployment-evidence.json" in str(fields["deployment_evidence_manifest_path"])


def test_cockpit_loose_api_smoke_without_manifest(tmp_path: Path) -> None:
    (tmp_path / "api-smoke.json").write_text(json.dumps({"schema_version": "single_tenant_api_http_smoke/v1", "ok": True}), encoding="utf-8")
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=None,
    )
    assert fields["api_smoke_ok"] is True


def test_cockpit_runtime_review_signoff(tmp_path: Path) -> None:
    review = {"decision": "KEEP_CURRENT_RELEASE", "signoff_status": "APPROVED"}
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=review,
    )
    assert fields["operator_decision"] == "KEEP_CURRENT_RELEASE"
    assert fields["manual_operator_signoff_present"] is True


def test_build_ui_evidence_payload_includes_cockpit_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full payload merge stays backward-compatible and never 500 on empty tree."""
    monkeypatch.chdir(tmp_path)
    payload = build_ui_evidence_payload(search_root=str(tmp_path))
    assert payload["schema_version"] == "ui_evidence_dashboard/v1"
    assert payload["deployment_status"] == "UNKNOWN"
    assert "deployment_evidence_ok" in payload
    assert "api_smoke_ok" in payload
    assert "evidence_generated_at_utc" in payload
    assert "deployment_evidence_manifest_path" in payload


def test_cockpit_payload_has_no_raw_secrets_from_manifest(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "single_tenant_deployment_evidence/v1",
        "ok": False,
        "generated_at_utc": "2026-04-01T12:00:00Z",
        "frontend_readiness_claimed": False,
        "files": [],
    }
    (tmp_path / "deployment-evidence.json").write_text(json.dumps(manifest), encoding="utf-8")
    fields = build_ui_evidence_cockpit_fields(
        search_root=tmp_path,
        projection_generated_at_utc="2099-01-01T00:00:00Z",
        disk_runtime_review=None,
    )
    blob = json.dumps(fields)
    assert "sk-" not in blob
    assert "secret-token-value" not in blob
