from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from strategy_validator.application.frontend_readiness_claim import (
    FRONTEND_EXPECTED_PACKAGE,
    FRONTEND_READINESS_CLAIM_ENABLE_ENV,
    FRONTEND_READINESS_CLAIM_ENV,
    FRONTEND_READINESS_CLAIM_SCHEMA_VERSION,
    load_frontend_readiness_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _valid_claim(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": FRONTEND_READINESS_CLAIM_SCHEMA_VERSION,
                "deployment_model": "single_tenant",
                "frontend_expected_package": FRONTEND_EXPECTED_PACKAGE,
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


def _load_claim_script():
    path = REPO_ROOT / "scripts" / "claim_single_tenant_frontend_readiness.py"
    spec = importlib.util.spec_from_file_location("_claim_single_tenant_frontend_readiness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_runtime_loader_accepts_regular_enabled_claim(monkeypatch, tmp_path) -> None:
    claim = tmp_path / "claim.json"
    _valid_claim(claim)
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENABLE_ENV, "true")
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENV, str(claim))

    payload = load_frontend_readiness_claim(tmp_path)

    assert payload["frontend_readiness_claimed"] is True
    assert payload["claim_status"] == "CLAIMED"


def test_runtime_loader_rejects_symlinked_claim_path(monkeypatch, tmp_path) -> None:
    real_claim = tmp_path / "real" / "claim.json"
    _valid_claim(real_claim)
    claim_link = tmp_path / "claim.json"
    claim_link.symlink_to(real_claim)
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENABLE_ENV, "true")
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENV, str(claim_link))

    payload = load_frontend_readiness_claim(tmp_path)

    assert payload["frontend_readiness_claimed"] is False
    assert payload["frontend_runtime_reachable"] is None
    assert payload["claim_reason"] == "CLAIM_ARTIFACT_PATH_UNSAFE"
    assert payload["path_integrity"]["code"] == "FRONTEND_READINESS_CLAIM_PATH_IS_SYMLINK"


def test_runtime_loader_rejects_claim_under_symlinked_parent(monkeypatch, tmp_path) -> None:
    real_dir = tmp_path / "real"
    real_claim = real_dir / "claim.json"
    _valid_claim(real_claim)
    parent_link = tmp_path / "frontend_readiness"
    parent_link.symlink_to(real_dir, target_is_directory=True)
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENABLE_ENV, "true")
    monkeypatch.setenv(FRONTEND_READINESS_CLAIM_ENV, str(parent_link / "claim.json"))

    payload = load_frontend_readiness_claim(tmp_path)

    assert payload["frontend_readiness_claimed"] is False
    assert payload["claim_reason"] == "CLAIM_ARTIFACT_PATH_UNSAFE"
    assert payload["path_integrity"]["code"] == "FRONTEND_READINESS_CLAIM_PATH_PARENT_IS_SYMLINK"


def test_claim_script_rejects_symlinked_output_path(tmp_path, capsys) -> None:
    mod = _load_claim_script()
    real_output = tmp_path / "real-claim.json"
    real_output.write_text("{}", encoding="utf-8")
    output_link = tmp_path / "claim.json"
    output_link.symlink_to(real_output)

    rc = mod.main(["--output", str(output_link), "--skip-build"])

    assert rc == 2
    captured = capsys.readouterr()
    assert "frontend_readiness_claim_path_error/v1" in captured.err
    assert "FRONTEND_READINESS_CLAIM_OUTPUT_IS_SYMLINK" in captured.err


def test_claim_script_rejects_output_under_symlinked_parent(tmp_path, capsys) -> None:
    mod = _load_claim_script()
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    parent_link = tmp_path / "frontend_readiness"
    parent_link.symlink_to(real_dir, target_is_directory=True)

    rc = mod.main(["--output", str(parent_link / "claim.json"), "--skip-build"])

    assert rc == 2
    captured = capsys.readouterr()
    assert "frontend_readiness_claim_path_error/v1" in captured.err
    assert "FRONTEND_READINESS_CLAIM_OUTPUT_PARENT_IS_SYMLINK" in captured.err
