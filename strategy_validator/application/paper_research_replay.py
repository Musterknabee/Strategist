"""Replay-manifest generation and offline verification for paper-research artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import re
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
    sensitive_flags = {
        "--token",
        "--api-token",
        "--api-key",
        "--key",
        "--secret",
        "--password",
        "--bearer",
    }
    key_value_pattern = re.compile(r"^([A-Za-z0-9_-]+)=(.*)$")
    redacted: list[str] = []
    redact_next = False
    for arg in args:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
            continue
        lower = arg.lower().strip()
        if lower in sensitive_flags:
            redacted.append(arg)
            redact_next = True
            continue
        if lower.startswith("--") and "=" in arg:
            key, _, _value = arg.partition("=")
            if key.lower() in sensitive_flags:
                redacted.append(f"{key}=<redacted>")
                continue
            redacted.append(arg)
            continue
        match = key_value_pattern.match(arg)
        if match:
            key = match.group(1)
            if re.search(r"(?i)(token|api[_-]?token|api[_-]?key|key|secret|password|bearer)", key):
                redacted.append(f"{key}=<redacted>")
                continue
            redacted.append(arg)
            continue
        if re.search(r"(?i)(token|api[_-]?token|api[_-]?key|key|secret|password|bearer)", lower):
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


class _PathSafetyError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _has_symlink_escape(candidate: Path, allowed_root: Path) -> bool:
    resolved_root = allowed_root.resolve()
    relative_parts = candidate.relative_to(resolved_root).parts
    current = resolved_root
    for part in relative_parts:
        current = current / part
        if current.exists() and current.is_symlink():
            target = current.resolve()
            if not _is_within(target, resolved_root):
                return True
    return False


def _resolve_artifact_target(
    path_text: str,
    *,
    allowed_root: Path,
    allow_absolute_paths: bool,
) -> Path:
    raw = Path(path_text)
    if raw.is_absolute() and not allow_absolute_paths:
        raise _PathSafetyError("UNSAFE_PATH", f"absolute path is not allowed: {path_text}")
    candidate = raw if raw.is_absolute() else (allowed_root / raw)
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise _PathSafetyError("UNSAFE_PATH", f"unable to resolve path: {path_text}: {type(exc).__name__}") from exc
    if not _is_within(resolved, allowed_root):
        if not raw.is_absolute() and _has_symlink_escape(candidate, allowed_root):
            raise _PathSafetyError("SYMLINK_OUTSIDE_ROOT", f"symlink resolves outside allowed root: {path_text}")
        raise _PathSafetyError("PATH_OUTSIDE_ROOT", f"path resolves outside allowed root: {path_text}")
    return resolved


def verify_replay_manifest(
    path: Path,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    allow_absolute_paths: bool = False,
) -> PaperResearchReplayVerificationSummary:
    root = (repo_root or Path.cwd()).resolve()
    allowed_root = (artifact_root or root).resolve()
    if not path.is_file():
        return PaperResearchReplayVerificationSummary(
            ok=False,
            replay_manifest_path=path.as_posix(),
            generated_at_utc=datetime.now(timezone.utc),
            input_artifact_count=0,
            output_artifact_count=0,
            missing_artifact_count=0,
            digest_mismatch_count=0,
            blockers=("REPLAY_MANIFEST_NOT_FOUND",),
            warnings=(),
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    manifest = PaperResearchReplayManifest.model_validate(raw)
    missing = 0
    mismatch = 0
    blockers: list[str] = []
    for row in [*manifest.input_artifacts, *manifest.output_artifacts]:
        try:
            target = _resolve_artifact_target(
                row.path,
                allowed_root=allowed_root,
                allow_absolute_paths=allow_absolute_paths,
            )
        except _PathSafetyError as exc:
            blockers.append(f"{exc.code}:{row.kind}:{row.path}")
            continue
        if not target.is_file():
            missing += 1
            blockers.append(f"MISSING_ARTIFACT:{row.kind}:{row.path}")
            continue
        got = sha256_file(target)
        if got != row.sha256:
            mismatch += 1
            blockers.append(f"DIGEST_MISMATCH:{row.kind}:{row.path}")

    return PaperResearchReplayVerificationSummary(
        ok=(missing == 0 and mismatch == 0 and not blockers),
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
    "discover_replay_manifest_path",
    "latest_replay_verification_summary",
    "redact_command_args",
    "verify_replay_manifest",
]


def discover_replay_manifest_path(
    *,
    repo_root: Path | None = None,
    replay_manifest_path: Path | None = None,
    artifact_root: Path | None = None,
) -> Path | None:
    root = (repo_root or Path.cwd()).resolve()
    if replay_manifest_path is not None:
        return replay_manifest_path.resolve() if replay_manifest_path.is_absolute() else (root / replay_manifest_path).resolve()
    if artifact_root is not None:
        return (artifact_root.resolve() / "provider_paper_loop" / "latest" / "replay_manifest.json").resolve()
    env_artifact_root = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if env_artifact_root:
        return (Path(env_artifact_root).resolve() / "provider_paper_loop" / "latest" / "replay_manifest.json").resolve()
    return (root / "artifacts" / "provider_paper_loop" / "latest" / "replay_manifest.json").resolve()


def latest_replay_verification_summary(*, repo_root: Path | None = None) -> dict[str, object]:
    root = (repo_root or Path.cwd()).resolve()
    replay = discover_replay_manifest_path(repo_root=root)
    if not replay.is_file():
        return {
            "status": "UNKNOWN",
            "replay_manifest_path": None,
            "input_artifact_count": 0,
            "output_artifact_count": 0,
            "missing_artifact_count": 0,
            "digest_mismatch_count": 0,
            "warnings": ["REPLAY_MANIFEST_NOT_FOUND", "PENDING_REPLAY_EVIDENCE"],
            "blockers": [],
        }
    summary = verify_replay_manifest(
        replay,
        repo_root=root,
        artifact_root=replay.parent.parent.parent,
    ).model_dump(mode="json")
    summary["status"] = "OK" if summary.get("ok") else "DEGRADED"
    return summary
