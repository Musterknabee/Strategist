"""Shared path-integrity helpers for operator scripts.

Operator-facing scripts should reject symlinked inputs/outputs instead of
following them with ``Path.resolve()``.  This keeps secret-bearing env files and
generated evidence artifacts inside the reviewed operator workspace.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathIntegrityError(Exception):
    """Machine-readable path-integrity failure."""

    code: str
    path: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.detail} ({self.path})"


def absolute_path_preserving_symlink(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate


def symlink_components_preserving_path(path: str | Path) -> tuple[Path, ...]:
    absolute = absolute_path_preserving_symlink(path)
    parts = absolute.parts
    if not parts:
        return ()
    current = Path(parts[0])
    candidates: list[Path] = []
    for part in parts[1:]:
        current = current / part
        candidates.append(current)
    return tuple(candidate for candidate in candidates if candidate.is_symlink())


def _raise_for_symlinks(path: Path, *, label: str) -> None:
    symlinks = symlink_components_preserving_path(path)
    if not symlinks:
        return
    final_component = path in symlinks
    code = f"{label}_IS_SYMLINK" if final_component else f"{label}_PARENT_IS_SYMLINK"
    detail = "symlinked path" if final_component else "symlinked parent directories"
    raise PathIntegrityError(
        code=code,
        path=str(path),
        detail=f"{detail}: {', '.join(str(item) for item in symlinks)}",
    )


def safe_input_file(path: str | Path, *, label: str, required: bool = True) -> Path | None:
    target = absolute_path_preserving_symlink(path)
    _raise_for_symlinks(target, label=label)
    if target.exists() and not target.is_file():
        raise PathIntegrityError(code=f"{label}_NOT_FILE", path=str(target), detail="path exists but is not a regular file")
    if required and not target.is_file():
        raise PathIntegrityError(code=f"{label}_MISSING", path=str(target), detail="required input file is missing")
    if not target.exists():
        return None
    return target


def safe_input_dir(path: str | Path, *, label: str, required: bool = True) -> Path | None:
    target = absolute_path_preserving_symlink(path)
    _raise_for_symlinks(target, label=label)
    if target.exists() and not target.is_dir():
        raise PathIntegrityError(code=f"{label}_NOT_DIRECTORY", path=str(target), detail="path exists but is not a directory")
    if required and not target.is_dir():
        raise PathIntegrityError(code=f"{label}_MISSING", path=str(target), detail="required input directory is missing")
    if not target.exists():
        return None
    return target


def safe_output_file(path: str | Path, *, label: str) -> Path:
    target = absolute_path_preserving_symlink(path)
    _raise_for_symlinks(target, label=label)
    if target.exists() and not target.is_file():
        raise PathIntegrityError(code=f"{label}_NOT_FILE", path=str(target), detail="output path exists but is not a regular file")
    return target


def safe_output_dir(path: str | Path, *, label: str) -> Path:
    target = absolute_path_preserving_symlink(path)
    _raise_for_symlinks(target, label=label)
    if target.exists() and not target.is_dir():
        raise PathIntegrityError(code=f"{label}_NOT_DIRECTORY", path=str(target), detail="output path exists but is not a directory")
    return target


def path_error_payload(error: PathIntegrityError, *, schema_version: str = "operator_path_integrity_error/v1") -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "ok": False,
        "code": error.code,
        "path": error.path,
        "detail": error.detail,
    }
