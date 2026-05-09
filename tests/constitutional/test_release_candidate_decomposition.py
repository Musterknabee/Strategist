from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _module(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text(encoding="utf-8"))


def _function_names(path: str) -> set[str]:
    tree = _module(path)
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_release_candidate_entrypoint_is_phase_facade() -> None:
    source_path = ROOT / "strategy_validator/cli/release_candidate.py"
    source = source_path.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 180
    functions = _function_names("strategy_validator/cli/release_candidate.py")
    assert functions == {"main"}
    assert "import subprocess" not in source
    assert "import shutil" not in source
    assert "cmd_generate" in source
    assert "cmd_assess" in source
    assert "cmd_verify_bundle" in source
    assert "cmd_cleanup" in source


def test_release_candidate_phase_modules_own_expected_responsibilities() -> None:
    common = _function_names("strategy_validator/cli/release_candidate_common.py")
    bundle = _function_names("strategy_validator/cli/release_candidate_bundle.py")
    assessment = _function_names("strategy_validator/cli/release_candidate_assessment.py")
    cleanup = _function_names("strategy_validator/cli/release_candidate_cleanup.py")

    assert {"_run", "_git_available", "_candidate_dir", "_sha256_file"} <= common
    assert {"cmd_generate", "cmd_verify_bundle", "_build_bundle_manifest", "_tracked_files"} <= bundle
    assert {"cmd_assess", "_write_check_log"} <= assessment
    assert cleanup == {"cmd_cleanup"}


def test_release_candidate_legacy_import_surface_remains_available() -> None:
    from strategy_validator.cli.release_candidate import (  # noqa: PLC0415
        CmdResult,
        _bundle_entries_content_sha256,
        _candidate_dir,
        _safe_candidate_id,
        cmd_assess,
        cmd_cleanup,
        cmd_generate,
        cmd_verify_bundle,
        main,
    )

    assert CmdResult.__name__ == "CmdResult"
    assert callable(_bundle_entries_content_sha256)
    assert callable(_candidate_dir)
    assert _safe_candidate_id("rc-1") == "rc-1"
    assert callable(cmd_generate)
    assert callable(cmd_assess)
    assert callable(cmd_verify_bundle)
    assert callable(cmd_cleanup)
    assert callable(main)
