"""Filesystem boundary helpers for operator/artifact paths.

The API accepts a few operator-supplied paths for release publication and
projection discovery.  Those paths must resolve inside an explicit trusted root;
otherwise a token-protected endpoint can accidentally become an arbitrary
filesystem reader/writer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class PathBoundaryError(ValueError):
    """Raised when a path resolves outside an allowed filesystem boundary."""


@dataclass(frozen=True)
class ResolvedPathBoundary:
    """Resolved root/path pair returned by boundary-aware route adapters."""

    root: Path
    path: Path


def _resolve_existing_parent(path: Path) -> Path:
    """Resolve a path even when the final leaf does not exist yet."""

    if path.exists():
        return path.resolve()
    parent = path.parent if str(path.parent) else Path(".")
    return parent.resolve() / path.name


def resolve_within_root(path: str | Path, *, root: str | Path, label: str = "path") -> Path:
    """Resolve ``path`` and fail unless it is inside ``root``.

    ``path`` may point to a not-yet-created file.  The parent is still resolved
    so ``..`` traversal and symlink escapes are caught before writes occur.
    """

    root_path = Path(root).expanduser().resolve()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = _resolve_existing_parent(candidate)
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise PathBoundaryError(f"{label.upper()}_OUTSIDE_ALLOWED_ROOT: {resolved} is outside {root_path}") from exc
    return resolved


def infer_common_root(paths: list[str | Path], *, fallback: str | Path | None = None) -> Path:
    """Infer a conservative root from a set of operator-supplied artifact paths."""

    concrete = [Path(p).expanduser() for p in paths if str(p).strip()]
    if not concrete:
        if fallback is None:
            return Path.cwd().resolve()
        return Path(fallback).expanduser().resolve()
    parents = [_resolve_existing_parent(path).parent if path.suffix else _resolve_existing_parent(path) for path in concrete]
    common = Path(__import__("os").path.commonpath([str(p) for p in parents]))
    return common.resolve()


def resolve_boundary(path: str | Path, *, root: str | Path | None = None, label: str = "path") -> ResolvedPathBoundary:
    """Resolve a single path with an explicit or inferred root."""

    boundary_root = Path(root).expanduser().resolve() if root is not None else infer_common_root([path])
    return ResolvedPathBoundary(root=boundary_root, path=resolve_within_root(path, root=boundary_root, label=label))
