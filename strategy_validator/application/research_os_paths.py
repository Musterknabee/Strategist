"""Shared filesystem layout for Research OS artifacts (read-plane + CLI)."""
from __future__ import annotations

import os
from pathlib import Path


def artifact_root_directory(repo_root: Path | None = None) -> Path:
    """Canonical governed artifact root (Docker: STRATEGY_VALIDATOR_ARTIFACT_ROOT)."""
    raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    root = repo_root or Path.cwd()
    return (root / "artifacts").resolve()


def paper_tracking_root_directory(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (artifact_root_directory(repo_root) / "paper_tracking").resolve()


def strategy_data_directory(repo_root: Path | None = None) -> Path:
    return (artifact_root_directory(repo_root) / "strategy_data").resolve()


def provider_historical_snapshot_run_path(repo_root: Path | None = None) -> Path:
    return (
        artifact_root_directory(repo_root) / "provider_historical_snapshots" / "latest" / "provider_historical_snapshot_run.json"
    ).resolve()


def provider_paper_loop_manifest_path(repo_root: Path | None = None) -> Path:
    return (
        artifact_root_directory(repo_root) / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    ).resolve()


def paper_broker_status_artifact_path(repo_root: Path | None = None) -> Path:
    return (artifact_root_directory(repo_root) / "paper_broker" / "latest" / "paper_broker_status.json").resolve()


def research_os_runtime_manifest_path(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_RESEARCH_OS_RUNTIME_MANIFEST", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (artifact_root_directory(repo_root) / "research_os_runtime" / "latest" / "runtime_demo_manifest.json").resolve()


__all__ = [
    "artifact_root_directory",
    "paper_broker_status_artifact_path",
    "paper_tracking_root_directory",
    "provider_historical_snapshot_run_path",
    "provider_paper_loop_manifest_path",
    "research_os_runtime_manifest_path",
    "strategy_data_directory",
]
