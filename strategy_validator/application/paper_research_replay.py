"""Replay-manifest generation and offline verification for paper-research artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.contracts.artifact_replay import (
    PaperResearchReplayManifest,
    PaperResearchReplayVerificationSummary,
    ReplayArtifactEntry,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_sha256(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _safe_rel(path: Path, repo_root: Path) -> str:
    rp = path.resolve()
    rr = repo_root.resolve()
    try:
        return rp.relative_to(rr).as_posix()
    except ValueError:
        return rp.as_posix()


def _artifact_entry(path: Path, *, kind: str, repo_root: Path) -> ReplayArtifactEntry | None:
    if not path.is_file():
        return None
    return ReplayArtifactEntry(kind=kind, path=_safe_rel(path, repo_root), sha256=sha256_file(path))


def _git_commit(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def config_fingerprint_from_env(env: dict[str, str]) -> str:
    safe_keys = (
        "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
        "STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT",
        "STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT",
        "STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST",
        "ALPACA_TRADING_MODE",
        "STRATEGY_VALIDATOR_MODE",
    )
    payload = {k: str(env.get(k, "")) for k in safe_keys}
    return _canonical_json_sha256(payload)


def redact_command_args(args: Iterable[str]) -> tuple[str, ...]:
    redacted: list[str] = []
    for arg in args:
        lower = arg.lower()
        if any(x in lower for x in ("key", "secret", "token", "password")):
            redacted.append("<redacted>")
        else:
            redacted.append(arg)
    return tuple(redacted)


def build_replay_manifest(
    *,
    repo_root: Path,
    artifact_id: str,
    command: str,
    command_args_redacted: tuple[str, ...],
    provider_id: str,
    provider_name: str,
    provider_mode: str,
    provider_key_required: bool,
    provider_key_present: bool,
    trust_banner: str,
    license_usage_caveat: str,
    source_label: str,
    config_fingerprint: str,
    input_paths: Iterable[tuple[str, Path]],
    output_paths: Iterable[tuple[str, Path]],
    warnings: Iterable[str] = (),
    blockers: Iterable[str] = (),
) -> PaperResearchReplayManifest:
    inputs = [
        e
        for e in (
            _artifact_entry(path, kind=kind, repo_root=repo_root) for kind, path in input_paths
        )
        if e is not None
    ]
    outputs = [
        e
        for e in (
            _artifact_entry(path, kind=kind, repo_root=repo_root) for kind, path in output_paths
        )
        if e is not None
    ]
    commit = _git_commit(repo_root)
    return PaperResearchReplayManifest(
        artifact_id=artifact_id,
        generated_at_utc=datetime.now(timezone.utc),
        command=command,
        command_args_redacted=command_args_redacted,
        git_commit=commit,
        code_fingerprint=commit,
        config_fingerprint=config_fingerprint,
        provider_id=provider_id,
        provider_name=provider_name or provider_id,
        provider_mode=provider_mode,
        provider_key_required=provider_key_required,
        provider_key_present=provider_key_present,
        trust_banner=trust_banner,
        license_usage_caveat=license_usage_caveat,
        source_label=source_label,
        input_artifacts=tuple(inputs),
        output_artifacts=tuple(outputs),
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )


def verify_replay_manifest(path: Path, *, repo_root: Path | None = None) -> PaperResearchReplayVerificationSummary:
    raw = json.loads(path.read_text(encoding="utf-8"))
    manifest = PaperResearchReplayManifest.model_validate(raw)
    missing = 0
    mismatch = 0
    blockers: list[str] = []
    root = (repo_root or Path.cwd()).resolve()
    for row in [*manifest.input_artifacts, *manifest.output_artifacts]:
        p = Path(row.path)
        target = p if p.is_absolute() else (root / p)
        if not target.is_file():
            missing += 1
            blockers.append(f"MISSING:{row.kind}:{row.path}")
            continue
        got = sha256_file(target)
        if got != row.sha256:
            mismatch += 1
            blockers.append(f"DIGEST_MISMATCH:{row.kind}:{row.path}")

    return PaperResearchReplayVerificationSummary(
        ok=(missing == 0 and mismatch == 0),
        replay_manifest_path=path.as_posix(),
        generated_at_utc=datetime.now(timezone.utc),
        input_artifact_count=len(manifest.input_artifacts),
        output_artifact_count=len(manifest.output_artifacts),
        missing_artifact_count=missing,
        digest_mismatch_count=mismatch,
        blockers=tuple(blockers),
        warnings=manifest.warnings,
    )


__all__ = [
    "build_replay_manifest",
    "config_fingerprint_from_env",
    "latest_replay_verification_summary",
    "redact_command_args",
    "verify_replay_manifest",
]


def latest_replay_verification_summary(*, repo_root: Path | None = None) -> dict[str, object]:
    root = (repo_root or Path.cwd()).resolve()
    replay = root / "artifacts" / "provider_paper_loop" / "latest" / "replay_manifest.json"
    if not replay.is_file():
        replay = Path("C:/var/lib/strategy-validator/artifacts/provider_paper_loop/latest/replay_manifest.json")
    if not replay.is_file():
        return {
            "status": "UNKNOWN",
            "replay_manifest_path": None,
            "input_artifact_count": 0,
            "output_artifact_count": 0,
            "missing_artifact_count": 0,
            "digest_mismatch_count": 0,
            "warnings": ["REPLAY_MANIFEST_NOT_FOUND"],
            "blockers": [],
        }
    summary = verify_replay_manifest(replay, repo_root=root).model_dump(mode="json")
    summary["status"] = "OK" if summary.get("ok") else "DEGRADED"
    return summary
