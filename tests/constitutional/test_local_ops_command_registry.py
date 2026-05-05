"""Repository truth mapping for cockpit local-ops command registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.repository_truth_check import _local_ops_registry_errors, _load_pyproject


def _scripts_map(root: Path) -> dict[str, object]:
    pyproject = _load_pyproject(root)
    project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    return dict(scripts) if isinstance(scripts, dict) else {}


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def real_registry(repo_root: Path) -> dict[str, object]:
    path = repo_root / "ui/strategist-web/lib/operator/local-ops-command-registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_local_ops_registry_passes_truth_mapping(repo_root: Path, real_registry: dict[str, object]) -> None:
    errors = _local_ops_registry_errors(repo_root, _scripts_map(repo_root), real_registry)
    assert errors == [], "; ".join(errors)


def test_local_ops_registry_rejects_unknown_console_script(repo_root: Path, real_registry: dict[str, object]) -> None:
    scripts = _scripts_map(repo_root)
    bad = json.loads(json.dumps(real_registry))
    cmds = bad.get("commands")
    assert isinstance(cmds, list) and cmds
    first = cmds[0]
    assert isinstance(first, dict)
    first["primaryConsoleScript"] = "strategy-validator-nonexistent-cli-for-truth-test"
    errors = _local_ops_registry_errors(repo_root, scripts, bad)
    assert any("not in pyproject" in msg for msg in errors)


def test_local_ops_registry_rejects_missing_python_script(repo_root: Path, real_registry: dict[str, object]) -> None:
    scripts = _scripts_map(repo_root)
    bad = json.loads(json.dumps(real_registry))
    cmds = bad.get("commands")
    assert isinstance(cmds, list) and cmds
    first = cmds[0]
    assert isinstance(first, dict)
    first["primaryConsoleScript"] = ""
    first["pythonScriptPaths"] = ["scripts/__nope_missing_for_truth_test__.py"]
    errors = _local_ops_registry_errors(repo_root, scripts, bad)
    assert any("missing pythonScriptPaths" in msg for msg in errors)


def test_local_ops_registry_requires_production_warning(repo_root: Path, real_registry: dict[str, object]) -> None:
    scripts = _scripts_map(repo_root)
    bad = json.loads(json.dumps(real_registry))
    cmds = bad.get("commands")
    assert isinstance(cmds, list)
    for item in cmds:
        if not isinstance(item, dict):
            continue
        if item.get("safetyClass") == "PRODUCTION_SENSITIVE":
            item["productionWarning"] = None
            break
    else:
        pytest.fail("fixture registry has no PRODUCTION_SENSITIVE command")
    errors = _local_ops_registry_errors(repo_root, scripts, bad)
    assert any("PRODUCTION_SENSITIVE requires" in msg for msg in errors)
