from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def test_release_candidate_generate_split_no_nameerror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: bundle module must import helpers moved to common (CI generate step)."""
    import strategy_validator.cli.release_candidate_common as common

    rc_root = tmp_path / "release_candidate_artifacts"
    rc_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(common, "ARTIFACTS_ROOT", rc_root)

    from strategy_validator.cli.release_candidate import main

    assert main(["generate", "--candidate", "ci-split-smoke"]) == 0
    candidate_dir = rc_root / "ci-split-smoke"
    assert candidate_dir.is_dir()
    assert (candidate_dir / "bundle-manifest.json").is_file()
    shutil.rmtree(candidate_dir, ignore_errors=True)
