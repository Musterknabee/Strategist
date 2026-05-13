"""Helpers for constitutional tests that inspect single-tenant deployment bundle implementation sources."""

from __future__ import annotations

from pathlib import Path


def read_single_tenant_bundle_sources(repo_root: Path) -> str:
    """Concatenate the thin entrypoint and all single_tenant_deployment_bundle_* implementation modules."""
    cli = repo_root / "strategy_validator" / "cli"
    paths: list[Path] = [cli / "single_tenant_deployment_bundle.py", *sorted(cli.glob("single_tenant_deployment_bundle_*.py"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
