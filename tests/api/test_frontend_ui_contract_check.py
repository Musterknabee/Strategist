"""Tests for scripts/frontend_ui_contract_check path matching and the check script exit code."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_checker():
    path = _REPO_ROOT / "scripts" / "frontend_ui_contract_check.py"
    spec = importlib.util.spec_from_file_location("frontend_ui_contract_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def chk():
    return _load_checker()


def test_path_matches_template_param_segment(chk):
    assert chk.path_matches_template("/ui/commands/claim-item", "/ui/commands/{action}")
    assert not chk.path_matches_template("/ui/commands/a/b", "/ui/commands/{action}")


def test_path_matches_template_static(chk):
    assert chk.path_matches_template("/ui/facade", "/ui/facade")
    assert not chk.path_matches_template("/ui/facade/extra", "/ui/facade")


def test_facade_route_match_paper_tracking(chk):
    routes = [
        {"method": "GET", "path": "/ui/paper-tracking/latest", "kind": "read", "auth_required": False, "payload_schema": "x"},
        {"method": "GET", "path": "/ui/paper-tracking/{tracking_id}", "kind": "read", "auth_required": False, "payload_schema": "x"},
    ]
    hit = chk.facade_route_match("GET", "/ui/paper-tracking/abc-123", routes)
    assert hit is not None
    assert hit["path"] == "/ui/paper-tracking/{tracking_id}"


def test_frontend_ui_contract_check_script_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "frontend_ui_contract_check.py")],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
