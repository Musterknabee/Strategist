"""Helpers for constitutional tests that inspect release-candidate CLI implementation sources."""

from __future__ import annotations

from pathlib import Path


def read_release_candidate_sources(repo_root: Path) -> str:
    """Concatenate the thin entrypoint and all release_candidate_* implementation modules."""
    cli = repo_root / "strategy_validator" / "cli"
    paths: list[Path] = [cli / "release_candidate.py", *sorted(cli.glob("release_candidate_*.py"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
