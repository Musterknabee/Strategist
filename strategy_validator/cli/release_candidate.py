from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "release_candidate"


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


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _which(tool: str) -> str | None:
    return shutil.which(tool)


def _is_windows() -> bool:
    return os.name == "nt"


def _candidate_dir(candidate: str) -> Path:
    return ARTIFACTS_ROOT / candidate


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    rels = [line.strip() for line in out.splitlines() if line.strip()]
    return [Path(rel) for rel in rels]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _build_bundle_manifest() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for rel in _tracked_files():
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            raise SystemExit(f"tracked file missing from worktree: {rel}")
        entries.append(
            {
                "path": rel.as_posix(),
                "size_bytes": abs_path.stat().st_size,
                "sha256": _sha256_file(abs_path),
            }
        )
    return {
        "schema": 1,
        "generated_at": _utc_now_iso(),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "entries": entries,
        "entry_count": len(entries),
    }


def _base_report(candidate: str) -> dict[str, Any]:
    describe = _git(["describe", "--tags", "--always", "--dirty"]) if _git(["rev-parse", "--is-inside-work-tree"]) else ""
    dirty = bool(_git(["status", "--porcelain=v1"]))
    return {
        "schema": 1,
        "candidate": candidate,
        "generated_at": _utc_now_iso(),
        "git": {
            "commit": _git(["rev-parse", "HEAD"]),
            "describe": describe,
            "dirty": dirty,
        },
        "tooling": {
            "python": sys.version.splitlines()[0],
            "npm_present": _which("npm") is not None,
            "node_present": _which("node") is not None,
        },
    }


def cmd_generate(candidate: str | None) -> Path:
    commit = _git(["rev-parse", "--short", "HEAD"])
    candidate_id = candidate or f"rc-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{commit}"
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


def cmd_assess(candidate: str, *, skip_frontend: bool) -> dict[str, Any]:
    out_dir = _candidate_dir(candidate)
    if not out_dir.exists():
        raise SystemExit(f"candidate directory does not exist: {out_dir}")
    _ensure_dir(out_dir / "checks")

    checks: list[dict[str, Any]] = []

    try:
        import pytest  # noqa: F401
    except Exception as e:
        raise SystemExit(f"assessment requires pytest to be installed (try `pip install -e \".[dev]\"`): {e}") from e

    def run_check(name: str, cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> None:
        res = _run(cmd, cwd=cwd, env=env, timeout_s=timeout_s)
        _write_check_log(out_dir, name, res)
        checks.append({"name": name, "ok": res.ok, "exit_code": res.exit_code, "duration_ms": res.duration_ms})
        if not res.ok:
            raise SystemExit(f"assessment failed at {name} (see {out_dir / 'checks' / f'{name}.log'})")

    run_check("hygiene", [sys.executable, "-c", "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"], cwd=REPO_ROOT)
    run_check("compileall", [sys.executable, "-m", "compileall", "strategy_validator"], cwd=REPO_ROOT)
    run_check(
        "constitutional",
        [sys.executable, "-m", "pytest", "-q", "tests/constitutional/test_anti_regression_invariants.py"],
        cwd=REPO_ROOT,
    )

    if not skip_frontend:
        if _which("npm") is None and _which("npm.cmd") is None:
            raise SystemExit("frontend assessment requested but npm not found on PATH")
        web_dir = REPO_ROOT / "ui" / "strategist-web"
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
        "schema": 1,
        "candidate": candidate,
        "assessed_at": _utc_now_iso(),
        "checks": checks,
        "architecture_health_report_ok": health.ok,
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
                "",
            ]
        ),
    )
    if not health.ok:
        raise SystemExit(f"assessment failed at architecture-health (see {out_dir / 'checks' / 'architecture-health.log'})")

    return assessment


def cmd_verify_bundle(candidate: str) -> dict[str, Any]:
    out_dir = _candidate_dir(candidate)
    manifest_path = out_dir / "bundle-manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"bundle manifest missing for candidate: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries") or []
    mismatches: list[str] = []
    missing: list[str] = []

    for entry in entries:
        rel = Path(entry["path"])
        expected_sha = entry["sha256"]
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            missing.append(str(rel))
            continue
        actual = _sha256_file(abs_path)
        if actual != expected_sha:
            mismatches.append(f"{rel} expected={expected_sha} actual={actual}")

    payload = {
        "schema": 1,
        "candidate": candidate,
        "verified_at": _utc_now_iso(),
        "missing_count": len(missing),
        "mismatch_count": len(mismatches),
        "missing": missing,
        "mismatches": mismatches,
        "ok": not missing and not mismatches,
    }
    _write_json(out_dir / "bundle-verify.json", payload)
    _write_text(
        out_dir / "bundle-verify.md",
        "\n".join(
            [
                f"# Bundle verification: `{candidate}`",
                "",
                f"- Verified: `{payload['verified_at']}`",
                f"- OK: `{payload['ok']}`",
                f"- Missing: `{payload['missing_count']}`",
                f"- Mismatches: `{payload['mismatch_count']}`",
                "",
                "## Notes",
                "",
                "This verifies the bundle manifest against the current worktree.",
                "",
            ]
        ),
    )
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

    rm_tree(Path(".import_linter_cache"))
    rm_tree(Path(".strategy_validator"))
    rm_tree(Path(".pytest_cache"))
    rm_tree(Path(".mypy_cache"))
    rm_tree(Path(".ruff_cache"))
    rm_glob("__pycache__/*.pyc")
    rm_glob("__pycache__/*.pyo")

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
        cmd_assess(args.candidate, skip_frontend=bool(args.skip_frontend))
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

