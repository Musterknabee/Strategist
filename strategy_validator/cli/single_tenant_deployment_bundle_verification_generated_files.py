"""Generated-file shape and mode verification for single-tenant bundles."""
from __future__ import annotations

import os
from pathlib import Path

from strategy_validator.cli.single_tenant_deployment_bundle_common import _REQUIRED_GENERATED_FILES

def _verify_generated_file_shapes(out: Path) -> list[str]:
    """Require every generated bundle member to be a regular file, never a symlink."""

    errors: list[str] = []
    for relative in _REQUIRED_GENERATED_FILES:
        path = out / relative
        if path.is_symlink():
            errors.append(f"generated file is a symlink: {relative}")
            continue
        if not path.exists():
            errors.append(f"missing generated file: {relative}")
            continue
        if not path.is_file():
            errors.append(f"generated path is not a regular file: {relative}")
    return errors

def _verify_generated_command_modes(out: Path) -> list[str]:
    errors: list[str] = []
    if os.name == "nt":
        # Windows does not surface POSIX executable bits the way Linux bundle targets do.
        # Generated helpers are still chmod 755 on Unix; CI and the target host enforce this.
        return errors
    for relative in _REQUIRED_GENERATED_FILES:
        if not relative.startswith("commands/"):
            continue
        path = out / relative
        if path.exists() and not (path.stat().st_mode & 0o111):
            errors.append(f"generated command is not executable: {relative}")
    return errors
