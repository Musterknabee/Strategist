from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from strategy_validator.cli.release_candidate_common import (
    REPO_ROOT,
    _candidate_dir,
    _ensure_dir,
    _git,
    _git_available,
    _safe_candidate_id,
    _utc_now_iso,
    _which,
    _write_json,
    _write_text,
)

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()



def _is_hex_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())




def _is_canonical_manifest_path(raw_path: str) -> bool:
    """Return true when a manifest path is a canonical repo-relative POSIX path."""
    if not isinstance(raw_path, str) or not raw_path:
        return False
    if "\\" in raw_path:
        return False
    rel = PurePosixPath(raw_path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        return False
    # Generated manifests use Path.as_posix(). Reject aliases such as ./a,
    # a//b, and a/./b so one source file has exactly one manifest identity.
    return rel.as_posix() == raw_path

def _normalize_bundle_digest_entry(entry: dict[str, Any], *, index: int) -> dict[str, Any]:
    """Return the canonical digest fields for one manifest entry.

    Bundle verification must fail closed with structured manifest errors rather
    than crashing on malformed values.  This helper is intentionally strict so
    ``content_sha256`` only seals entries with a valid path, non-negative integer
    size, and hexadecimal SHA-256 digest.
    """
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError(f"entry[{index}] path must be a non-empty string")
    if not _is_canonical_manifest_path(raw_path):
        raise ValueError(f"{raw_path!r} path must be a canonical repo-relative POSIX path")
    size_bytes = entry.get("size_bytes")
    if not isinstance(size_bytes, int) or size_bytes < 0:
        raise ValueError(f"{raw_path} size_bytes must be a non-negative integer")
    sha256 = entry.get("sha256")
    if not _is_hex_sha256(sha256):
        raise ValueError(f"{raw_path} sha256 must be a 64-character hexadecimal digest")
    return {"path": raw_path, "size_bytes": size_bytes, "sha256": sha256.lower()}


def _bundle_entries_content_sha256(entries: list[dict[str, Any]]) -> str:
    """Digest the normalized release bundle membership and file digests.

    The bundle manifest is intentionally not digested as raw JSON because fields
    such as ``generated_at`` and git metadata are time/environment dependent.
    This digest seals the source membership that matters for handoff integrity:
    path, size, and per-file SHA-256 for every included file.
    """
    normalized = [
        _normalize_bundle_digest_entry(entry, index=index)
        for index, entry in enumerate(sorted(entries, key=lambda item: str(item.get("path", ""))))
    ]
    payload = json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


_ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL = {".git", "artifacts", "scratch"}
_ARCHIVE_FALLBACK_EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".import_linter_cache",
    ".strategy_validator",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}
_ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".gz", ".tgz", ".sqlite", ".sqlite3", ".db", ".db-wal", ".db-shm", ".log", ".jsonl"}


def _include_in_archive_fallback_manifest(path: Path) -> bool:
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in _ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL:
        return False
    if any(part in _ARCHIVE_FALLBACK_EXCLUDED_DIR_NAMES for part in parts):
        return False
    if path.suffix in _ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES:
        return False
    if path.is_symlink():
        return False
    return path.is_file()


def _tracked_files() -> list[Path]:
    if not _git_available():
        rels = [
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob('*')
            if _include_in_archive_fallback_manifest(path)
        ]
        return [Path(rel) for rel in sorted(rels)]
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    rels = [line.strip() for line in out.splitlines() if line.strip()]
    return [Path(rel) for rel in rels]


def _build_bundle_manifest() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for rel in sorted(_tracked_files(), key=lambda item: item.as_posix()):
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            raise SystemExit(f"tracked file missing from worktree: {rel}")
        if abs_path.is_symlink():
            raise SystemExit(f"tracked file is a symbolic link and cannot be sealed: {rel}")
        if not abs_path.is_file():
            raise SystemExit(f"tracked path is not a regular file and cannot be sealed: {rel}")
        entries.append(
            {
                "path": rel.as_posix(),
                "size_bytes": abs_path.stat().st_size,
                "sha256": _sha256_file(abs_path),
            }
        )
    return {
        "schema": 2,
        "generated_at": _utc_now_iso(),
        "git_commit": _git(["rev-parse", "HEAD"], default='archive-no-git'),
        "entries": entries,
        "entry_count": len(entries),
        "content_sha256": _bundle_entries_content_sha256(entries),
    }


def _base_report(candidate: str) -> dict[str, Any]:
    git_available = _git_available()
    describe = _git(["describe", "--tags", "--always", "--dirty"], default='archive-no-git') if git_available else 'archive-no-git'
    dirty = bool(_git(["status", "--porcelain=v1"], default='')) if git_available else False
    return {
        "schema": 1,
        "candidate": candidate,
        "generated_at": _utc_now_iso(),
        "git": {
            "commit": _git(["rev-parse", "HEAD"], default='archive-no-git'),
            "describe": describe,
            "dirty": dirty,
            "available": git_available,
        },
        "tooling": {
            "python": sys.version.splitlines()[0],
            "npm_present": _which("npm") is not None,
            "node_present": _which("node") is not None,
        },
    }


def cmd_generate(candidate: str | None) -> Path:
    commit = _git(["rev-parse", "--short", "HEAD"], default='archive')
    default_candidate = f"rc-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{commit}"
    candidate_id = _safe_candidate_id(candidate) if candidate is not None else default_candidate
    out_dir = _candidate_dir(candidate_id)
    _ensure_dir(out_dir)
    _ensure_dir(out_dir / "checks")

    report = _base_report(candidate_id)
    manifest = _build_bundle_manifest()

    _write_json(out_dir / "report.json", report)
    _write_json(out_dir / "bundle-manifest.json", manifest)

    _write_text(
        out_dir / "report.md",
        "\n".join(
            [
                f"# Release candidate: `{candidate_id}`",
                "",
                f"- Generated: `{report['generated_at']}`",
                f"- Git: `{report['git']['describe']}`",
                f"- Dirty: `{report['git']['dirty']}`",
                f"- Bundle entries: `{manifest['entry_count']}`",
                "",
                "## Next commands",
                "",
                f"- Assess: `strategy-validator-release-candidate assess --candidate {candidate_id}`",
                f"- Verify bundle: `strategy-validator-release-candidate verify-bundle --candidate {candidate_id}`",
                "- Cleanup transients: `strategy-validator-release-candidate cleanup`",
                "",
            ]
        ),
    )

    _write_text(
        out_dir / "handoff.ps1",
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"strategy-validator-release-candidate assess --candidate {candidate_id}",
                f"strategy-validator-release-candidate verify-bundle --candidate {candidate_id}",
            ]
        ),
    )
    _write_text(
        out_dir / "handoff.sh",
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"strategy-validator-release-candidate assess --candidate {candidate_id}",
                f"strategy-validator-release-candidate verify-bundle --candidate {candidate_id}",
            ]
        ),
    )

    return out_dir
def _write_bundle_verify_report(out_dir: Path, candidate: str, payload: dict[str, Any]) -> None:
    _write_json(out_dir / "bundle-verify.json", payload)
    _write_text(
        out_dir / "bundle-verify.md",
        "\n".join(
            [
                f"# Bundle verification: `{candidate}`",
                "",
                f"- Verified: `{payload['verified_at']}`",
                f"- OK: `{payload['ok']}`",
                f"- Entries: `{payload['entry_count']}`",
                f"- Current files: `{payload['current_file_count']}`",
                f"- Missing: `{payload['missing_count']}`",
                f"- Mismatches: `{payload['mismatch_count']}`",
                f"- Malformed entries: `{payload['malformed_count']}`",
                f"- Duplicate paths: `{payload['duplicate_path_count']}`",
                f"- Manifest errors: `{payload['manifest_error_count']}`",
                f"- Missing from manifest: `{payload['missing_from_manifest_count']}`",
                f"- Stale manifest paths: `{payload['stale_manifest_path_count']}`",
                f"- Content digest OK: `{payload['content_sha256_ok']}`",
                "",
                "## Notes",
                "",
                "This verifies the bundle manifest against the current worktree and fails if the manifest omits current source files.",
                "",
            ]
        ),
    )


def _bundle_verify_failure_payload(candidate: str, *, manifest_errors: list[str]) -> dict[str, Any]:
    current_paths = {path.as_posix() for path in _tracked_files()}
    return {
        "schema": 2,
        "candidate": candidate,
        "verified_at": _utc_now_iso(),
        "entry_count": 0,
        "current_file_count": len(current_paths),
        "missing_count": 0,
        "mismatch_count": 0,
        "malformed_count": 0,
        "duplicate_path_count": 0,
        "manifest_error_count": len(manifest_errors),
        "missing_from_manifest_count": len(current_paths),
        "stale_manifest_path_count": 0,
        "manifest_errors": manifest_errors,
        "manifest_schema": None,
        "declared_entry_count": None,
        "content_sha256": None,
        "recomputed_content_sha256": None,
        "content_sha256_ok": False,
        "missing": [],
        "mismatches": [],
        "malformed": [],
        "duplicate_paths": [],
        "missing_from_manifest": sorted(current_paths),
        "stale_manifest_paths": [],
        "ok": False,
    }


def cmd_verify_bundle(candidate: str) -> dict[str, Any]:
    out_dir = _candidate_dir(candidate)
    manifest_path = out_dir / "bundle-manifest.json"
    if not manifest_path.exists():
        _ensure_dir(out_dir)
        payload = _bundle_verify_failure_payload(candidate, manifest_errors=[f"bundle manifest missing: {manifest_path}"])
        _write_bundle_verify_report(out_dir, candidate, payload)
        raise SystemExit("bundle verification failed (see bundle-verify.json for details)")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        payload = _bundle_verify_failure_payload(candidate, manifest_errors=[f"bundle manifest is not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"])
        _write_bundle_verify_report(out_dir, candidate, payload)
        raise SystemExit("bundle verification failed (see bundle-verify.json for details)")
    if not isinstance(manifest, dict):
        payload = _bundle_verify_failure_payload(candidate, manifest_errors=["bundle manifest must be a JSON object"])
        _write_bundle_verify_report(out_dir, candidate, payload)
        raise SystemExit("bundle verification failed (see bundle-verify.json for details)")
    raw_entries = manifest.get("entries")
    entries = raw_entries if isinstance(raw_entries, list) else []
    manifest_container_errors: list[str] = []
    if not isinstance(raw_entries, list):
        manifest_container_errors.append("entries must be a list")

    mismatches: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    duplicate_paths: list[str] = []
    manifest_errors: list[str] = []
    entry_paths: list[str] = []
    seen_paths: set[str] = set()

    manifest_errors.extend(manifest_container_errors)

    manifest_schema = manifest.get("schema")
    if manifest_schema != 2:
        manifest_errors.append(f"schema expected=2 actual={manifest_schema!r}")
    declared_entry_count = manifest.get("entry_count")
    if declared_entry_count != len(entries):
        manifest_errors.append(f"entry_count expected={len(entries)} actual={declared_entry_count!r}")
    content_sha256 = manifest.get("content_sha256")
    content_sha256_shape_ok = _is_hex_sha256(content_sha256)
    if not content_sha256_shape_ok:
        manifest_errors.append("content_sha256 must be a 64-character hexadecimal digest")

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            malformed.append(f"entry[{index}] is not an object")
            continue
        raw_path = entry.get("path")
        expected_sha = entry.get("sha256")
        expected_size = entry.get("size_bytes")
        if not isinstance(raw_path, str) or not raw_path:
            malformed.append(f"entry[{index}] missing path")
            continue
        if not _is_canonical_manifest_path(raw_path):
            malformed.append(f"{raw_path!r} path must be a canonical repo-relative POSIX path")
            continue
        if raw_path in seen_paths:
            duplicate_paths.append(raw_path)
        seen_paths.add(raw_path)
        entry_paths.append(raw_path)
        if not _is_hex_sha256(expected_sha):
            malformed.append(f"{raw_path} has invalid sha256")
            continue
        if not isinstance(expected_size, int) or expected_size < 0:
            malformed.append(f"{raw_path} has invalid size_bytes")
            continue
        try:
            rel = Path(raw_path)
        except TypeError:
            malformed.append(f"{raw_path!r} is not a valid path")
            continue
        if rel.is_absolute() or ".." in rel.parts:
            malformed.append(f"{raw_path} escapes repository root")
            continue
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            missing.append(str(rel))
            continue
        if abs_path.is_symlink():
            malformed.append(f"{raw_path} is a symbolic link")
            continue
        if not abs_path.is_file():
            malformed.append(f"{raw_path} is not a regular file")
            continue
        try:
            actual = _sha256_file(abs_path)
            actual_size = abs_path.stat().st_size
        except OSError as exc:
            malformed.append(f"{raw_path} could not be read: {exc.__class__.__name__}")
            continue
        if actual != expected_sha:
            mismatches.append(f"{rel} expected={expected_sha} actual={actual}")
        if isinstance(expected_size, int) and actual_size != expected_size:
            mismatches.append(f"{rel} size expected={expected_size} actual={actual_size}")

    current_paths = {path.as_posix() for path in _tracked_files()}
    if entry_paths != sorted(entry_paths):
        manifest_errors.append("entries must be sorted by canonical path")
    manifest_paths = set(entry_paths)
    missing_from_manifest = sorted(current_paths - manifest_paths)
    stale_manifest_paths = sorted(manifest_paths - current_paths)
    recomputed_content_sha256: str | None = None
    digest_normalization_errors: list[str] = []
    if all(isinstance(entry, dict) for entry in entries):
        try:
            recomputed_content_sha256 = _bundle_entries_content_sha256(entries)
        except ValueError as exc:
            digest_normalization_errors.append(str(exc))
    else:
        digest_normalization_errors.append("entries must all be objects before content_sha256 can be recomputed")
    manifest_errors.extend(f"content_sha256 cannot be recomputed: {error}" for error in digest_normalization_errors)
    content_sha256_ok = bool(content_sha256_shape_ok and recomputed_content_sha256 and content_sha256 == recomputed_content_sha256)
    if content_sha256_shape_ok and not content_sha256_ok:
        mismatches.append(f"content_sha256 expected={content_sha256} actual={recomputed_content_sha256}")

    payload = {
        "schema": 2,
        "candidate": candidate,
        "verified_at": _utc_now_iso(),
        "entry_count": len(entries),
        "current_file_count": len(current_paths),
        "missing_count": len(missing),
        "mismatch_count": len(mismatches),
        "malformed_count": len(malformed),
        "duplicate_path_count": len(duplicate_paths),
        "manifest_error_count": len(manifest_errors),
        "missing_from_manifest_count": len(missing_from_manifest),
        "stale_manifest_path_count": len(stale_manifest_paths),
        "manifest_errors": manifest_errors,
        "manifest_schema": manifest_schema,
        "declared_entry_count": declared_entry_count,
        "content_sha256": content_sha256,
        "recomputed_content_sha256": recomputed_content_sha256,
        "content_sha256_ok": content_sha256_ok,
        "missing": missing,
        "mismatches": mismatches,
        "malformed": malformed,
        "duplicate_paths": sorted(set(duplicate_paths)),
        "missing_from_manifest": missing_from_manifest,
        "stale_manifest_paths": stale_manifest_paths,
        "ok": not (
            missing
            or mismatches
            or malformed
            or duplicate_paths
            or manifest_errors
            or missing_from_manifest
            or stale_manifest_paths
            or not content_sha256_ok
        ),
    }
    _write_bundle_verify_report(out_dir, candidate, payload)
    if not payload["ok"]:
        raise SystemExit("bundle verification failed (see bundle-verify.json for details)")
    return payload
