from __future__ import annotations

import tomllib
from pathlib import Path


def _load_pyproject() -> dict:
    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_runtime_dependencies_cover_yaml_config() -> None:
    project = _load_pyproject()["project"]
    dependencies = set(project["dependencies"])
    assert "PyYAML>=6.0" in dependencies


def test_dev_profile_covers_full_runtime_surface() -> None:
    optional = _load_pyproject()["project"]["optional-dependencies"]
    dev = set(optional["dev"])
    for requirement in (
        "cryptography>=42",
        "numpy>=1.26",
        "pandas>=2.2",
        "statsmodels>=0.14",
    ):
        assert requirement in dev


def test_brain_namespace_is_excluded_from_distribution() -> None:
    find_packages = _load_pyproject()["tool"]["setuptools"]["packages"]["find"]
    assert "strategy_validator.brain*" in set(find_packages["exclude"])
