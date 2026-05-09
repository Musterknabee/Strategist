from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _git(args: list[str], *, default: str = "") -> str:
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


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
