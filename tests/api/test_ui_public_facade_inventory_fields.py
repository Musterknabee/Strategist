from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.ui_public_facade import (
    UI_FRONTEND_EXPECTED_PACKAGE,
    build_ui_public_facade_inventory,
)


def test_facade_payload_includes_detection_and_hint_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_PATH", str(tmp_path / "missing-claim.json"))
    payload = build_ui_public_facade_inventory()
    assert payload["frontend_package_present"] is payload["frontend_package_detected_by_backend"]
    assert payload["frontend_readiness_claimed"] is False
    assert payload["read_plane_only"] is True
    assert payload["frontend_runtime_reachable"] is None
    assert isinstance(payload["frontend_operator_console_hint"], str)
    assert "api-only" in payload["frontend_operator_console_hint"].lower()


def test_facade_claims_frontend_only_with_formal_single_tenant_artifact(tmp_path: Path, monkeypatch) -> None:
    pkg = tmp_path / UI_FRONTEND_EXPECTED_PACKAGE
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text("{}", encoding="utf-8")
    claim = tmp_path / "claim.json"
    claim.write_text(
        json.dumps(
            {
                "schema_version": "single_tenant_frontend_readiness/v1",
                "deployment_model": "single_tenant",
                "frontend_expected_package": UI_FRONTEND_EXPECTED_PACKAGE,
                "frontend_readiness_claimed": True,
                "frontend_runtime_reachable": True,
                "ok": True,
                "checks": {
                    "frontend_package_present": True,
                    "lint_passed": True,
                    "typecheck_passed": True,
                    "test_passed": True,
                    "build_passed": True,
                    "no_public_token_exposure": True,
                    "api_ready": True,
                    "facade_read_plane_only": True,
                    "frontend_runtime_reachable": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_PATH", str(claim))
    monkeypatch.setenv("STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_ENABLE", "true")
    payload = build_ui_public_facade_inventory(repo_root=tmp_path)
    assert payload["frontend_readiness_claimed"] is True
    assert payload["frontend_runtime_reachable"] is True


def test_facade_ignores_valid_claim_artifact_without_opt_in(tmp_path: Path, monkeypatch) -> None:
    pkg = tmp_path / UI_FRONTEND_EXPECTED_PACKAGE
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text("{}", encoding="utf-8")
    claim = tmp_path / "claim.json"
    claim.write_text(
        json.dumps(
            {
                "schema_version": "single_tenant_frontend_readiness/v1",
                "deployment_model": "single_tenant",
                "frontend_expected_package": UI_FRONTEND_EXPECTED_PACKAGE,
                "frontend_readiness_claimed": True,
                "frontend_runtime_reachable": True,
                "ok": True,
                "checks": {
                    "frontend_package_present": True,
                    "lint_passed": True,
                    "typecheck_passed": True,
                    "test_passed": True,
                    "build_passed": True,
                    "no_public_token_exposure": True,
                    "api_ready": True,
                    "facade_read_plane_only": True,
                    "frontend_runtime_reachable": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_PATH", str(claim))
    monkeypatch.delenv("STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_ENABLE", raising=False)
    payload = build_ui_public_facade_inventory(repo_root=tmp_path)
    assert payload["frontend_readiness_claimed"] is False
    assert payload["frontend_runtime_reachable"] is None


def test_facade_frontend_absent_when_package_not_under_repo_root(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    payload = build_ui_public_facade_inventory(repo_root=tmp_path / "empty")
    assert payload["frontend_package_present"] is False
    assert payload["frontend_package_detected_by_backend"] is False
    assert payload["frontend_status"] == "absent"


def test_facade_frontend_present_when_package_under_repo_root(tmp_path: Path) -> None:
    pkg = tmp_path / UI_FRONTEND_EXPECTED_PACKAGE
    pkg.mkdir(parents=True)
    (pkg / "package.json").write_text("{}", encoding="utf-8")
    payload = build_ui_public_facade_inventory(repo_root=tmp_path)
    assert payload["frontend_package_present"] is True
    assert payload["frontend_package_detected_by_backend"] is True
