"""Shared filesystem layout for Research OS artifacts (read-plane + CLI)."""
from __future__ import annotations

import os
from pathlib import Path


def safe_relative_artifact_path(relative_path: str | Path) -> Path:
    candidate = Path(relative_path).expanduser()
    if candidate.is_absolute():
        raise ValueError("ARTIFACT_PATH_MUST_BE_RELATIVE")
    if ".." in candidate.parts:
        raise ValueError("ARTIFACT_PATH_TRAVERSAL_FORBIDDEN")
    return candidate


def resolve_artifact_root(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    base = (repo_root or Path.cwd()).resolve()
    if not raw:
        return (base / "artifacts").resolve()
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    rel = safe_relative_artifact_path(candidate)
    return (base / rel).resolve()


def resolve_artifact_output_dir(
    *,
    output_dir: str | Path | None,
    default_subdir: str | Path | None = None,
    repo_root: Path | None = None,
    create: bool = False,
) -> Path:
    artifact_root = resolve_artifact_root(repo_root)
    if output_dir is None:
        target = artifact_root if default_subdir is None else artifact_root / safe_relative_artifact_path(default_subdir)
    else:
        raw = Path(output_dir).expanduser()
        if raw.is_absolute():
            target = raw.resolve()
        else:
            target = (artifact_root / safe_relative_artifact_path(raw)).resolve()
    if target != artifact_root and artifact_root not in target.parents:
        raise ValueError("ARTIFACT_OUTPUT_OUTSIDE_ROOT")
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target


def artifact_root_directory(repo_root: Path | None = None) -> Path:
    """Canonical governed artifact root (Docker: STRATEGY_VALIDATOR_ARTIFACT_ROOT)."""
    return resolve_artifact_root(repo_root)


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
    "resolve_artifact_output_dir",
    "resolve_artifact_root",
    "safe_relative_artifact_path",
    "strategy_data_directory",
]
