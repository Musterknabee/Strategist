from __future__ import annotations

from pathlib import Path

from strategy_validator.application.ui_public_facade import (
    UI_FRONTEND_EXPECTED_PACKAGE,
    build_ui_public_facade_inventory,
)


def test_facade_payload_includes_detection_and_hint_fields() -> None:
    payload = build_ui_public_facade_inventory()
    assert payload["frontend_package_present"] is payload["frontend_package_detected_by_backend"]
    assert payload["frontend_readiness_claimed"] is False
    assert payload["read_plane_only"] is True
    assert payload["frontend_runtime_reachable"] is None
    assert isinstance(payload["frontend_operator_console_hint"], str)
    assert "api-only" in payload["frontend_operator_console_hint"].lower()


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
