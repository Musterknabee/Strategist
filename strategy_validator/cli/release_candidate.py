from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "release_candidate"
_CANDIDATE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class CmdResult:
    ok: bool
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> CmdResult:
    started = datetime.now(timezone.utc)
    proc_env = os.environ.copy()
    # Release assessment must not create bytecode caches that subsequently trip
    # the repo hygiene gate or pollute source-archive handoffs.
    proc_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env:
        proc_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=proc_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_s,
        )
        ended = datetime.now(timezone.utc)
        duration_ms = int((ended - started).total_seconds() * 1000)
        return CmdResult(
            ok=proc.returncode == 0,
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )
    except subprocess.TimeoutExpired as e:
        ended = datetime.now(timezone.utc)
        duration_ms = int((ended - started).total_seconds() * 1000)
        return CmdResult(
            ok=False,
            exit_code=124,
            duration_ms=duration_ms,
            stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
            stderr=(e.stderr or "") if isinstance(e.stderr, str) else f"timeout after {timeout_s}s",
        )


def _git_available() -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0 and proc.stdout.strip() == 'true'


def _git(args: list[str], *, default: str = '') -> str:
    if not _git_available():
        return default
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()
    except subprocess.CalledProcessError:
        return default


def _which(tool: str) -> str | None:
    return shutil.which(tool)


def _is_windows() -> bool:
    return os.name == "nt"


def _safe_candidate_id(candidate: str) -> str:
    """Validate a release candidate identifier before using it as a path segment."""
    if (
        not isinstance(candidate, str)
        or not candidate
        or candidate in {".", ".."}
        or "/" in candidate
        or "\\" in candidate
        or _CANDIDATE_ID_PATTERN.fullmatch(candidate) is None
    ):
        raise SystemExit(
            "invalid release candidate id: use 1-128 characters from "
            "A-Z, a-z, 0-9, dot, underscore, and dash; path separators are forbidden"
        )
    return candidate


def _candidate_dir(candidate: str) -> Path:
    safe_candidate = _safe_candidate_id(candidate)
    candidate_dir = (ARTIFACTS_ROOT / safe_candidate).resolve()
    artifacts_root = ARTIFACTS_ROOT.resolve()
    if artifacts_root != candidate_dir and artifacts_root not in candidate_dir.parents:
        raise SystemExit("invalid release candidate id: resolved candidate path escapes release artifact root")
    return candidate_dir


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


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
                f"- Cleanup transients: `strategy-validator-release-candidate cleanup`",
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


def _write_check_log(out_dir: Path, name: str, result: CmdResult) -> None:
    log_path = out_dir / "checks" / f"{name}.log"
    _write_text(
        log_path,
        "\n".join(
            [
                f"command: {name}",
                f"ok: {result.ok}",
                f"exit_code: {result.exit_code}",
                f"duration_ms: {result.duration_ms}",
                "",
                "----- stdout -----",
                result.stdout.rstrip(),
                "",
                "----- stderr -----",
                result.stderr.rstrip(),
                "",
            ]
        ),
    )


def cmd_assess(candidate: str, *, skip_frontend: bool, full_suite: bool = False) -> dict[str, Any]:
    out_dir = _candidate_dir(candidate)
    if not out_dir.exists():
        raise SystemExit(f"candidate directory does not exist: {out_dir}")
    _ensure_dir(out_dir / "checks")

    checks: list[dict[str, Any]] = []

    started = datetime.now(timezone.utc)
    try:
        bundle_payload = cmd_verify_bundle(candidate)
        bundle_duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        checks.append(
            {
                "name": "bundle-verify",
                "ok": bool(bundle_payload.get("ok")),
                "exit_code": 0 if bundle_payload.get("ok") else 1,
                "duration_ms": bundle_duration_ms,
            }
        )
    except SystemExit:
        bundle_duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        checks.append({"name": "bundle-verify", "ok": False, "exit_code": 1, "duration_ms": bundle_duration_ms})
        _write_json(
            out_dir / "assessment.json",
            {
                "schema": 2,
                "candidate": candidate,
                "assessed_at": _utc_now_iso(),
                "checks": checks,
                "architecture_health_report_ok": False,
            },
        )
        raise

    def run_check(name: str, cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> None:
        res = _run(cmd, cwd=cwd, env=env, timeout_s=timeout_s)
        _write_check_log(out_dir, name, res)
        checks.append({"name": name, "ok": res.ok, "exit_code": res.exit_code, "duration_ms": res.duration_ms})
        if not res.ok:
            raise SystemExit(f"assessment failed at {name} (see {out_dir / 'checks' / f'{name}.log'})")

    run_check("source-health", [sys.executable, "scripts/source_health.py"], cwd=REPO_ROOT)
    run_check("repository-truth", [sys.executable, "scripts/repository_truth_check.py"], cwd=REPO_ROOT)
    run_check("migration-truth", [sys.executable, "scripts/migration_truth_check.py"], cwd=REPO_ROOT)
    run_check("environment-check", [sys.executable, "scripts/environment_check.py", "--include-extra", "dev"], cwd=REPO_ROOT)

    run_check(
        "hygiene",
        [sys.executable, "-c", "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"],
        cwd=REPO_ROOT,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    run_check(
        "constitutional",
        [sys.executable, "-m", "pytest", "-q", "tests/constitutional/test_anti_regression_invariants.py"],
        cwd=REPO_ROOT,
    )

    if full_suite:
        run_check(
            "full-suite",
            [sys.executable, "-m", "pytest", "-q"],
            cwd=REPO_ROOT,
        )

    web_dir = REPO_ROOT / "ui" / "strategist-web"
    frontend_status: dict[str, Any] = {
        "name": "frontend-operator-ui",
        "present": web_dir.exists(),
        "skipped": bool(skip_frontend),
        "status": "DEFERRED" if not web_dir.exists() else "PRESENT",
        "detail": "ui/strategist-web is absent; backend assessment cannot imply frontend readiness." if not web_dir.exists() else "ui/strategist-web package exists.",
    }
    if skip_frontend:
        checks.append({"name": "frontend-validate", "ok": True, "exit_code": 0, "duration_ms": 0, "skipped": True, "detail": frontend_status["detail"]})
    else:
        if _which("npm") is None and _which("npm.cmd") is None:
            raise SystemExit("frontend assessment requested but npm not found on PATH")
        if not web_dir.exists():
            raise SystemExit("frontend assessment requested but ui/strategist-web is missing")
        if _is_windows():
            run_check(
                "frontend-validate",
                ["cmd", "/d", "/s", "/c", "npm run validate"],
                cwd=web_dir,
            )
        else:
            run_check("frontend-validate", ["npm", "run", "validate"], cwd=web_dir)

    health = _run([sys.executable, "scripts/architecture_health_report.py"], cwd=REPO_ROOT)
    _write_check_log(out_dir, "architecture-health", health)

    assessment = {
        "schema": 2,
        "candidate": candidate,
        "assessed_at": _utc_now_iso(),
        "checks": checks,
        "architecture_health_report_ok": health.ok,
        "frontend_status": frontend_status,
        "full_suite_requested": bool(full_suite),
    }
    _write_json(out_dir / "assessment.json", assessment)
    _write_text(
        out_dir / "assessment.md",
        "\n".join(
            [
                f"# Production candidate assessment: `{candidate}`",
                "",
                f"- Assessed: `{assessment['assessed_at']}`",
                "",
                "## Checks",
                "",
                *[f"- {c['name']}: {'PASS' if c['ok'] else 'FAIL'} ({c['duration_ms']} ms)" for c in checks],
                "",
                f"- Architecture health report: {'PASS' if health.ok else 'FAIL'}",
                f"- Frontend operator UI: {frontend_status['status']} ({'skipped' if frontend_status['skipped'] else 'checked'})",
                f"  - {frontend_status['detail']}",
                "",
            ]
        ),
    )
    if not health.ok:
        raise SystemExit(f"assessment failed at architecture-health (see {out_dir / 'checks' / 'architecture-health.log'})")

    return assessment


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

def cmd_cleanup(*, aggressive_frontend: bool) -> dict[str, Any]:
    removed: list[str] = []

    def rm_tree(rel: Path) -> None:
        abs_path = REPO_ROOT / rel
        if abs_path.exists() and abs_path.is_dir():
            shutil.rmtree(abs_path, ignore_errors=True)
            removed.append(rel.as_posix() + "/")

    def rm_glob(pattern: str) -> None:
        for p in REPO_ROOT.rglob(pattern):
            if p.is_file():
                try:
                    p.unlink()
                    removed.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))
                except OSError:
                    continue

    def rm_named_dirs(name: str) -> None:
        for p in sorted(REPO_ROOT.rglob(name), key=lambda item: len(item.parts), reverse=True):
            if p.is_dir():
                rel = p.relative_to(REPO_ROOT).as_posix() + "/"
                shutil.rmtree(p, ignore_errors=True)
                removed.append(rel)

    rm_tree(Path(".import_linter_cache"))
    rm_tree(Path(".strategy_validator"))
    rm_tree(Path(".pytest_cache"))
    rm_tree(Path(".mypy_cache"))
    rm_tree(Path(".ruff_cache"))
    rm_named_dirs("__pycache__")
    rm_glob("*.pyc")
    rm_glob("*.pyo")

    if aggressive_frontend:
        rm_tree(Path("ui/strategist-web/.next"))
        rm_tree(Path("ui/strategist-web/node_modules"))

    payload = {"schema": 1, "cleaned_at": _utc_now_iso(), "removed": sorted(set(removed))}
    _ensure_dir(ARTIFACTS_ROOT)
    _write_json(ARTIFACTS_ROOT / "cleanup.json", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(description="Repo-native release candidate tooling (fail-closed).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="Generate release candidate packet (report + manifest + handoff).")
    p_gen.add_argument("--candidate", help="Candidate id (defaults to timestamp + short sha).")

    p_assess = sub.add_parser("assess", help="Assess production candidate readiness (fails closed).")
    p_assess.add_argument("--candidate", required=True, help="Candidate id (must already be generated).")
    p_assess.add_argument("--skip-frontend", action="store_true", help="Skip ui/strategist-web validation.")
    p_assess.add_argument("--full-suite", action="store_true", help="Run the complete pytest suite during candidate assessment.")

    p_verify = sub.add_parser("verify-bundle", help="Verify candidate bundle manifest against worktree.")
    p_verify.add_argument("--candidate", required=True, help="Candidate id (must already be generated).")

    p_clean = sub.add_parser("cleanup", help="Remove transient/generated artifacts from the worktree.")
    p_clean.add_argument("--aggressive-frontend", action="store_true", help="Also remove ui build caches and node_modules.")

    args = parser.parse_args(argv)

    if args.cmd == "generate":
        out_dir = cmd_generate(args.candidate)
        print(str(out_dir))
        return 0
    if args.cmd == "assess":
        cmd_assess(args.candidate, skip_frontend=bool(args.skip_frontend), full_suite=bool(args.full_suite))
        print("assessment passed")
        return 0
    if args.cmd == "verify-bundle":
        cmd_verify_bundle(args.candidate)
        print("bundle verification passed")
        return 0
    if args.cmd == "cleanup":
        cmd_cleanup(aggressive_frontend=bool(args.aggressive_frontend))
        print("cleanup complete")
        return 0

    raise SystemExit("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())

