#!/usr/bin/env python3
"""Run bounded certification/stability probes and persist a human/audit friendly report.

This is not a replacement for the raw commands in the release checklist. It is a
watchdog wrapper for proving whether those commands *finish*, timing each phase,
and capturing bounded output tails when a phase fails or times out.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, TextIO

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPO_ROOT / "ui" / "strategist-web"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "certification_stability" / "latest" / "certification_stability_report.json"
DEFAULT_CONSTITUTIONAL_SUMMARY_OUTPUT = REPO_ROOT / "artifacts" / "certification_stability" / "latest" / "constitutional_shards_summary.json"
DEFAULT_CONSTITUTIONAL_SHARD_COUNT = 32
DEFAULT_COLLECTION_SHARD_COUNT = 32
DEFAULT_COLLECTION_SUMMARY_OUTPUT = REPO_ROOT / "artifacts" / "certification_stability" / "latest" / "collection_shards_summary.json"
DEFAULT_PYTEST_EXECUTION_SHARD_COUNT = 32
DEFAULT_PYTEST_EXECUTION_SUMMARY_OUTPUT = REPO_ROOT / "artifacts" / "certification_stability" / "latest" / "pytest_execution_shards_summary.json"


def _node_version() -> str | None:
    if shutil.which("node") is None:
        return None
    try:
        result = subprocess.run(["node", "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return None
    return result.stdout.strip() or None



@dataclass(frozen=True)
class StabilityStep:
    name: str
    command: tuple[str, ...]
    cwd: str
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StabilityPlan:
    name: str
    steps: tuple[tuple[str, tuple[str, ...], Path], ...]


def _tail(value: str, limit: int = 8000) -> str:
    return value[-limit:]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json_digest(payload: object) -> str:
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _constitutional_source_manifest() -> tuple[dict[str, str], ...]:
    return tuple(
        {"path": _relative(path), "sha256": _sha256_file(path)}
        for path in sorted((REPO_ROOT / "tests" / "constitutional").glob("test_*.py"))
        if path.is_file()
    )


def _constitutional_source_manifest_digest() -> str:
    return _canonical_json_digest(list(_constitutional_source_manifest()))




def _shard_failure_detail(
    *,
    path: Path,
    shard_index: object,
    shard_count: object,
    step: dict[str, object],
    failed_step: object,
    timeout_seconds: object | None = None,
) -> dict[str, object]:
    return {
        "path": str(path),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "step_name": step.get("name"),
        "failed_step": failed_step,
        "exit_code": step.get("exit_code"),
        "timed_out": step.get("timed_out"),
        "duration_seconds": step.get("duration_seconds"),
        "timeout_seconds": step.get("timeout_seconds", timeout_seconds),
        "stdout_tail": step.get("stdout_tail"),
        "stderr_tail": step.get("stderr_tail"),
    }


def _verify_exact_shard_blocker_fields(
    *,
    payload: dict[str, object],
    blockers: list[str],
    prefix: str,
    detail_field: str,
    timed_out_field: str,
    nonzero_field: str,
) -> None:
    for field_name in (
        "passed_shard_count",
        "failed_shard_count",
        "timed_out_shard_count",
        "nonzero_shard_count",
        detail_field,
        timed_out_field,
        nonzero_field,
    ):
        if field_name not in payload:
            blockers.append(f"{prefix}_FIELD_MISSING:{field_name}")

    failed_details = payload.get(detail_field)
    timed_out_details = payload.get(timed_out_field)
    nonzero_details = payload.get(nonzero_field)
    if not isinstance(failed_details, list):
        blockers.append(f"{prefix}_FAILED_SHARDS_NOT_LIST")
        failed_details = []
    if not isinstance(timed_out_details, list):
        blockers.append(f"{prefix}_TIMED_OUT_SHARDS_NOT_LIST")
        timed_out_details = []
    if not isinstance(nonzero_details, list):
        blockers.append(f"{prefix}_NONZERO_SHARDS_NOT_LIST")
        nonzero_details = []
    if payload.get("failed_shard_count") != len(failed_details):
        blockers.append(f"{prefix}_FAILED_SHARD_COUNT_MISMATCH:{payload.get('failed_shard_count')}:expected={len(failed_details)}")
    if payload.get("timed_out_shard_count") != len(timed_out_details):
        blockers.append(f"{prefix}_TIMED_OUT_SHARD_COUNT_MISMATCH:{payload.get('timed_out_shard_count')}:expected={len(timed_out_details)}")
    if payload.get("nonzero_shard_count") != len(nonzero_details):
        blockers.append(f"{prefix}_NONZERO_SHARD_COUNT_MISMATCH:{payload.get('nonzero_shard_count')}:expected={len(nonzero_details)}")
    for detail in failed_details:
        if not isinstance(detail, dict):
            blockers.append(f"{prefix}_FAILED_SHARD_DETAIL_INVALID")
            continue
        for field_name in ("path", "shard_index", "step_name", "exit_code", "timed_out", "duration_seconds", "timeout_seconds"):
            if field_name not in detail:
                blockers.append(f"{prefix}_FAILED_SHARD_DETAIL_FIELD_MISSING:{field_name}")


def _collection_source_manifest() -> tuple[dict[str, str], ...]:
    return tuple(
        {"path": _relative(path), "sha256": _sha256_file(path)}
        for path in sorted((REPO_ROOT / "tests").rglob("test_*.py"))
        if path.is_file()
    )


def _collection_source_manifest_digest() -> str:
    return _canonical_json_digest(list(_collection_source_manifest()))


def _pytest_execution_source_manifest() -> tuple[dict[str, str], ...]:
    return _collection_source_manifest()


def _pytest_execution_source_manifest_digest() -> str:
    return _collection_source_manifest_digest()




def _summary_payload_digest(payload: dict[str, object]) -> str:
    seal_payload = dict(payload)
    seal_payload.pop("summary_payload_sha256", None)
    return _canonical_json_digest(seal_payload)


def _relative(path: Path) -> str:
    """Return ``path`` relative to ``REPO_ROOT`` using forward slashes (POSIX).

    Windows ``Path`` stringification uses backslashes; manifests, pytest command lines,
    and cross-platform summaries must use a single separator so shard aggregation matches.
    """
    try:
        rel = path.relative_to(REPO_ROOT) if path != REPO_ROOT else Path(".")
        return rel.as_posix()
    except ValueError:
        return path.as_posix()


def _execution_command(command: Sequence[str]) -> list[str]:
    # Run the audited command directly. The watchdog owns a fresh process group
    # per step (see ``_run_step``), so timeouts can terminate pytest and any
    # descendants without relying on an intermediate shell to forward signals.
    return list(command)


def _terminate(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        _cleanup_process_group(proc.pid)
        return
    try:
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGTERM)
        else:  # pragma: no cover - Windows-specific process handling
            proc.terminate()
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            if os.name != "nt":
                os.killpg(proc.pid, signal.SIGKILL)
            else:  # pragma: no cover - Windows-specific process handling
                proc.kill()
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
    _cleanup_process_group(proc.pid)


def _cleanup_process_group(pgid: int) -> None:
    """Best-effort cleanup for descendants left behind by a completed step."""
    if os.name == "nt":  # pragma: no cover - Windows-specific process handling
        return
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    time.sleep(0.2)
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError:
        return


def _windows_popen_redirected_stdio(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_file: TextIO,
    stderr_file: TextIO,
    start_new_session: bool,
) -> subprocess.Popen[str]:
    """Windows Popen flags aligned with ``local_certify._windows_subprocess_popen`` (keep in sync)."""
    popen_kw: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "stdout": stdout_file,
        "stderr": stderr_file,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "close_fds": True,
        "start_new_session": start_new_session,
    }
    new_group = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    breakaway = int(getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0))
    no_window = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    combos: list[int] = []
    seen: set[int] = set()

    def _add_flags(flags: int) -> None:
        if flags and flags not in seen:
            seen.add(flags)
            combos.append(flags)

    _add_flags(new_group | no_window | breakaway)
    _add_flags(new_group | no_window)
    _add_flags(new_group | breakaway)
    _add_flags(new_group)

    last_exc: OSError | None = None
    for creationflags in combos:
        try:
            return subprocess.Popen(argv, creationflags=creationflags, **popen_kw)
        except OSError as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    return subprocess.Popen(argv, **popen_kw)


def _run_step(
    name: str,
    command: Sequence[str],
    cwd: Path,
    *,
    timeout_seconds: int,
    heartbeat_seconds: int = 10,
) -> StabilityStep:
    started = time.monotonic()
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO_ROOT))
    start_new_session = os.name != "nt"
    # Capture to real files instead of PIPEs. Some certification tests launch
    # child processes; if those children inherit a pipe fd, communicate() can
    # wait forever even after the pytest process exits. File-backed capture
    # records the same audit tails without making orphaned descendants part of
    # the watchdog's EOF contract.
    with tempfile.TemporaryDirectory(prefix="strategy_validator_certification_") as tmp_dir:
        stdout_path = Path(tmp_dir) / "stdout.txt"
        stderr_path = Path(tmp_dir) / "stderr.txt"
        with stdout_path.open("w+", encoding="utf-8", errors="replace") as stdout_file, stderr_path.open(
            "w+", encoding="utf-8", errors="replace"
        ) as stderr_file:
            argv = _execution_command(command)
            if os.name == "nt":  # pragma: no cover - Windows-specific process handling
                proc = _windows_popen_redirected_stdio(
                    argv,
                    cwd=cwd,
                    env=env,
                    stdout_file=stdout_file,
                    stderr_file=stderr_file,
                    start_new_session=start_new_session,
                )
            else:
                proc = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    env=env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    close_fds=True,
                    start_new_session=start_new_session,
                )
            timed_out = False
            last_progress = started
            while proc.poll() is None:
                now = time.monotonic()
                if now - started >= timeout_seconds:
                    timed_out = True
                    _terminate(proc)
                    break
                if heartbeat_seconds > 0 and now - last_progress >= heartbeat_seconds:
                    print(f"... {name} still running after {round(now - started, 1)}s", flush=True)
                    last_progress = now
                time.sleep(0.5)
            if not timed_out:
                _cleanup_process_group(proc.pid)
            stdout_file.flush()
            stderr_file.flush()
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read()
            stderr = stderr_file.read()
    duration = time.monotonic() - started
    return StabilityStep(
        name=name,
        command=tuple(command),
        cwd=_relative(cwd),
        exit_code=proc.returncode,
        timed_out=timed_out,
        duration_seconds=round(duration, 3),
        stdout_tail=_tail(stdout or ""),
        stderr_tail=_tail(stderr or ""),
    )


def _python_core_plan(py: str) -> StabilityPlan:
    return StabilityPlan(
        name="python_core",
        steps=(
            ("compileall", (py, "-m", "compileall", "-q", "strategy_validator", "tests", "scripts"), REPO_ROOT),
            ("source_health", (py, "scripts/source_health.py"), REPO_ROOT),
            ("repository_truth", (py, "scripts/repository_truth_check.py"), REPO_ROOT),
            ("migration_truth", (py, "scripts/migration_truth_check.py"), REPO_ROOT),
            ("public_surface_dashboard", (py, "scripts/public_surface_dashboard.py", "--json"), REPO_ROOT),
        ),
    )


def _pytest_collect_plan(py: str) -> StabilityPlan:
    return StabilityPlan(
        name="pytest_collect",
        steps=(("pytest_collect_only", (py, "-m", "pytest", "--collect-only", "-q"), REPO_ROOT),),
    )


def _chunked_paths(paths: Sequence[Path], *, shard_count: int) -> tuple[tuple[Path, ...], ...]:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if not paths:
        return tuple()
    normalized = tuple(sorted(paths))
    shard_count = min(shard_count, len(normalized))
    chunks: list[tuple[Path, ...]] = []
    for index in range(shard_count):
        start = index * len(normalized) // shard_count
        end = (index + 1) * len(normalized) // shard_count
        chunks.append(tuple(normalized[start:end]))
    return tuple(chunk for chunk in chunks if chunk)


def _constitutional_shard_plan(
    py: str,
    *,
    shard_count: int = DEFAULT_CONSTITUTIONAL_SHARD_COUNT,
    shard_index: int | None = None,
) -> StabilityPlan:
    files = tuple((REPO_ROOT / "tests" / "constitutional").glob("test_*.py"))
    chunks = _chunked_paths(files, shard_count=shard_count)
    total = len(chunks)
    if shard_index is not None:
        if shard_index < 1 or shard_index > total:
            raise ValueError(f"constitutional shard index must be between 1 and {total}")
        indexed_chunks = ((shard_index, chunks[shard_index - 1]),)
    else:
        indexed_chunks = tuple(enumerate(chunks, start=1))
    return StabilityPlan(
        name="constitutional_shards",
        steps=tuple(
            (
                f"pytest_constitutional_{index:02d}_of_{total:02d}",
                (py, "-m", "pytest", "-q", "--tb=short", *(_relative(path) for path in chunk)),
                REPO_ROOT,
            )
            for index, chunk in indexed_chunks
        ),
    )


def _collection_shard_plan(
    py: str,
    *,
    shard_count: int = DEFAULT_COLLECTION_SHARD_COUNT,
    shard_index: int | None = None,
) -> StabilityPlan:
    files = tuple((REPO_ROOT / "tests").rglob("test_*.py"))
    chunks = _chunked_paths(files, shard_count=shard_count)
    total = len(chunks)
    if shard_index is not None:
        if shard_index < 1 or shard_index > total:
            raise ValueError(f"collection shard index must be between 1 and {total}")
        indexed_chunks = ((shard_index, chunks[shard_index - 1]),)
    else:
        indexed_chunks = tuple(enumerate(chunks, start=1))
    return StabilityPlan(
        name="collect_shards",
        steps=tuple(
            (
                f"pytest_collect_{index:02d}_of_{total:02d}",
                (py, "-m", "pytest", "--collect-only", "-q", *(_relative(path) for path in chunk)),
                REPO_ROOT,
            )
            for index, chunk in indexed_chunks
        ),
    )



def _pytest_execution_shard_plan(
    py: str,
    *,
    shard_count: int = DEFAULT_PYTEST_EXECUTION_SHARD_COUNT,
    shard_index: int | None = None,
) -> StabilityPlan:
    files = tuple((REPO_ROOT / "tests").rglob("test_*.py"))
    chunks = _chunked_paths(files, shard_count=shard_count)
    total = len(chunks)
    if shard_index is not None:
        if shard_index < 1 or shard_index > total:
            raise ValueError(f"pytest execution shard index must be between 1 and {total}")
        indexed_chunks = ((shard_index, chunks[shard_index - 1]),)
    else:
        indexed_chunks = tuple(enumerate(chunks, start=1))
    return StabilityPlan(
        name="pytest_execution_shards",
        steps=tuple(
            (
                f"pytest_execution_{index:02d}_of_{total:02d}",
                (py, "-m", "pytest", "-q", "--tb=short", *(_relative(path) for path in chunk)),
                REPO_ROOT,
            )
            for index, chunk in indexed_chunks
        ),
    )

def _pytest_shard_plan(py: str) -> StabilityPlan:
    shards = [
        "tests/api",
        "tests/application",
        "tests/cli",
        "tests/research",
        "tests/scripts",
    ]
    return StabilityPlan(
        name="pytest_shards",
        steps=tuple(
            (
                f"pytest_{Path(shard).name}",
                (py, "-m", "pytest", "-vv", "--tb=short", shard),
                REPO_ROOT,
            )
            for shard in shards
        ),
    )


def _researcher_fixture_plan(py: str, artifact_root: Path) -> StabilityPlan:
    return StabilityPlan(
        name="researcher_fixture",
        steps=(
            ("researcher_cycle_fixture", (py, "-m", "strategy_validator.cli.researcher_cycle", "--artifact-root", artifact_root.as_posix(), "--json"), REPO_ROOT),
            ("researcher_certify_fixture", (py, "-m", "strategy_validator.cli.researcher_certify", "--artifact-root", artifact_root.as_posix(), "--write", "--json"), REPO_ROOT),
        ),
    )


def _frontend_plan(*, include_install: bool) -> StabilityPlan:
    steps: list[tuple[str, tuple[str, ...], Path]] = []
    if include_install:
        steps.append(("frontend_npm_ci", ("npm", "ci"), FRONTEND_ROOT))
    steps.extend(
        [
            ("frontend_lint", ("npm", "run", "lint"), FRONTEND_ROOT),
            ("frontend_typecheck", ("npm", "run", "typecheck"), FRONTEND_ROOT),
            ("frontend_test", ("npm", "run", "test"), FRONTEND_ROOT),
            ("frontend_acceptance", ("npm", "run", "acceptance"), FRONTEND_ROOT),
            ("frontend_build", ("npm", "run", "build"), FRONTEND_ROOT),
        ]
    )
    return StabilityPlan(name="frontend", steps=tuple(steps))


def _copy_fixture(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    queue = REPO_ROOT / "tests" / "fixtures" / "researcher_cycle" / "full_cycle_candidate_queue.json"
    target = root / "researcher_cycle" / "candidate_queue.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(queue, target)


def _load_json_report(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON report {path}: {exc}") from exc


def _normalise_report_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate




def _expected_constitutional_test_files() -> tuple[str, ...]:
    return tuple(
        sorted(
            _relative(path)
            for path in (REPO_ROOT / "tests" / "constitutional").glob("test_*.py")
            if path.is_file()
        )
    )


def _normalise_constitutional_test_file(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(REPO_ROOT)
        except ValueError:
            return None
    normalized = candidate.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized.startswith("tests/constitutional/test_") or not normalized.endswith(".py"):
        return None
    return normalized


def _command_constitutional_test_files(command: object) -> tuple[str, ...]:
    if not isinstance(command, (list, tuple)):
        return tuple()
    files = []
    for part in command:
        normalized = _normalise_constitutional_test_file(part)
        if normalized is not None:
            files.append(normalized)
    return tuple(files)


def _expected_collection_test_files() -> tuple[str, ...]:
    return tuple(
        sorted(
            _relative(path)
            for path in (REPO_ROOT / "tests").rglob("test_*.py")
            if path.is_file()
        )
    )


def _normalise_collection_test_file(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(REPO_ROOT)
        except ValueError:
            return None
    normalized = candidate.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized.startswith("tests/") or not normalized.endswith(".py"):
        return None
    if not Path(normalized).name.startswith("test_"):
        return None
    return normalized


def _command_collection_test_files(command: object) -> tuple[str, ...]:
    if not isinstance(command, (list, tuple)):
        return tuple()
    files = []
    for part in command:
        normalized = _normalise_collection_test_file(part)
        if normalized is not None:
            files.append(normalized)
    return tuple(files)


def _aggregate_constitutional_shard_reports(
    report_paths: Sequence[str | Path],
    *,
    expected_shard_count: int | None = None,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    """Aggregate resumable constitutional shard reports into one proof artifact.

    A valid summary requires every shard index from 1..N exactly once.  Each
    source report must be a ``certification_stability/v2`` report from the
    ``constitutional_shards`` phase, must declare the same shard count, and must
    have passed without timed-out or non-zero steps.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    source_payloads: list[dict[str, object]] = []
    seen_indexes: dict[int, Path] = {}
    duplicate_indexes: list[int] = []
    observed_counts: set[int] = set()
    expected_test_files = set(_expected_constitutional_test_files())
    expected_source_manifest = _constitutional_source_manifest()
    expected_source_manifest_digest = _constitutional_source_manifest_digest()
    observed_test_files: dict[str, Path] = {}
    duplicate_test_files: dict[str, list[Path]] = {}
    unexpected_test_files: dict[str, Path] = {}
    failed_constitutional_shards: list[dict[str, object]] = []
    timed_out_constitutional_shards: list[dict[str, object]] = []
    nonzero_constitutional_shards: list[dict[str, object]] = []

    normalised_paths = tuple(_normalise_report_path(path) for path in report_paths)
    if not normalised_paths:
        blockers.append("NO_CONSTITUTIONAL_SHARD_REPORTS_PROVIDED")

    for path in normalised_paths:
        if not path.exists():
            blockers.append(f"CONSTITUTIONAL_SHARD_REPORT_MISSING:{path}")
            continue
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))
            continue

        schema = payload.get("schema_version")
        phases = payload.get("phases")
        status = payload.get("status")
        shard_count = payload.get("constitutional_shard_count")
        shard_index = payload.get("constitutional_shard_index")
        steps = payload.get("steps")
        repo_root = payload.get("repo_root")
        source_tree = payload.get("constitutional_source_tree")

        if schema != "certification_stability/v2":
            blockers.append(f"UNSUPPORTED_SHARD_REPORT_SCHEMA:{path}:{schema}")
        if repo_root != str(REPO_ROOT):
            blockers.append(f"CONSTITUTIONAL_SHARD_REPO_ROOT_MISMATCH:{path}:{repo_root}:expected={REPO_ROOT}")
        if not isinstance(source_tree, dict):
            blockers.append(f"CONSTITUTIONAL_SHARD_SOURCE_TREE_MISSING:{path}")
        else:
            observed_digest = source_tree.get("manifest_sha256")
            observed_count = source_tree.get("file_count")
            if observed_digest != expected_source_manifest_digest:
                blockers.append(
                    f"CONSTITUTIONAL_SHARD_SOURCE_TREE_MISMATCH:{path}:{observed_digest}:expected={expected_source_manifest_digest}"
                )
            if observed_count != len(expected_source_manifest):
                blockers.append(
                    f"CONSTITUTIONAL_SHARD_SOURCE_TREE_FILE_COUNT_MISMATCH:{path}:{observed_count}:expected={len(expected_source_manifest)}"
                )
        if phases != ["constitutional_shards"]:
            blockers.append(f"NON_CONSTITUTIONAL_SHARD_REPORT:{path}:{phases}")
        if not isinstance(shard_count, int) or shard_count <= 0:
            blockers.append(f"INVALID_CONSTITUTIONAL_SHARD_COUNT:{path}:{shard_count}")
        else:
            observed_counts.add(shard_count)
        if not isinstance(shard_index, int) or shard_index <= 0:
            blockers.append(f"INVALID_CONSTITUTIONAL_SHARD_INDEX:{path}:{shard_index}")
        elif isinstance(shard_count, int) and shard_index > shard_count:
            blockers.append(f"CONSTITUTIONAL_SHARD_INDEX_OUT_OF_RANGE:{path}:{shard_index}>{shard_count}")
        else:
            previous = seen_indexes.get(shard_index)
            if previous is not None:
                duplicate_indexes.append(shard_index)
                blockers.append(f"DUPLICATE_CONSTITUTIONAL_SHARD_INDEX:{shard_index}:{previous}:{path}")
            else:
                seen_indexes[shard_index] = path
        if status != "PASS":
            blockers.append(f"CONSTITUTIONAL_SHARD_REPORT_NOT_PASSING:{path}:{status}")
        if not isinstance(steps, list) or len(steps) != 1:
            blockers.append(f"CONSTITUTIONAL_SHARD_REPORT_EXPECTED_ONE_STEP:{path}")
        else:
            step = steps[0]
            if not isinstance(step, dict):
                blockers.append(f"CONSTITUTIONAL_SHARD_STEP_INVALID:{path}")
            else:
                timed_out = step.get("timed_out") is not False
                nonzero = step.get("exit_code") != 0
                if timed_out:
                    blockers.append(f"CONSTITUTIONAL_SHARD_TIMED_OUT:{path}:{step.get('name')}")
                if nonzero:
                    blockers.append(f"CONSTITUTIONAL_SHARD_NONZERO_EXIT:{path}:{step.get('name')}:{step.get('exit_code')}")
                if status != "PASS" or timed_out or nonzero:
                    shard_detail = _shard_failure_detail(
                        path=path,
                        shard_index=shard_index,
                        shard_count=shard_count,
                        step=step,
                        failed_step=payload.get("failed_step"),
                        timeout_seconds=payload.get("timeout_seconds"),
                    )
                    failed_constitutional_shards.append(shard_detail)
                    if timed_out:
                        timed_out_constitutional_shards.append(shard_detail)
                    if nonzero:
                        nonzero_constitutional_shards.append(shard_detail)
                command = step.get("command")
                command_files = _command_constitutional_test_files(command)
                if not command_files:
                    blockers.append(f"CONSTITUTIONAL_SHARD_COMMAND_MISSING_TEST_FILES:{path}")
                for test_file in command_files:
                    if test_file not in expected_test_files:
                        unexpected_test_files[test_file] = path
                    previous = observed_test_files.get(test_file)
                    if previous is not None:
                        duplicate_test_files.setdefault(test_file, [previous]).append(path)
                    else:
                        observed_test_files[test_file] = path

        source_payloads.append(
            {
                "path": str(path),
                "sha256": _sha256_file(path),
                "status": status,
                "failed_step": payload.get("failed_step"),
                "constitutional_shard_count": shard_count,
                "constitutional_shard_index": shard_index,
                "repo_root": repo_root,
                "constitutional_source_tree_manifest_sha256": (
                    source_tree.get("manifest_sha256") if isinstance(source_tree, dict) else None
                ),
                "step_names": [step.get("name") for step in steps if isinstance(step, dict)] if isinstance(steps, list) else [],
                "covered_constitutional_test_files": (
                    list(_command_constitutional_test_files(steps[0].get("command")))
                    if isinstance(steps, list) and len(steps) == 1 and isinstance(steps[0], dict)
                    else []
                ),
            }
        )

    missing_test_files = sorted(expected_test_files.difference(observed_test_files))
    for test_file in missing_test_files:
        blockers.append(f"CONSTITUTIONAL_TEST_FILE_MISSING_FROM_SHARDS:{test_file}")
    for test_file, paths in sorted(duplicate_test_files.items()):
        blockers.append(
            "CONSTITUTIONAL_TEST_FILE_DUPLICATED_ACROSS_SHARDS:"
            + test_file
            + ":"
            + ":".join(str(path) for path in paths)
        )
    for test_file, path in sorted(unexpected_test_files.items()):
        blockers.append(f"CONSTITUTIONAL_TEST_FILE_UNEXPECTED_IN_SHARD:{test_file}:{path}")

    inferred_count: int | None = expected_shard_count
    if inferred_count is None and len(observed_counts) == 1:
        inferred_count = next(iter(observed_counts))
    elif inferred_count is None and observed_counts:
        inferred_count = max(observed_counts)

    if expected_shard_count is not None and expected_shard_count <= 0:
        blockers.append(f"INVALID_EXPECTED_CONSTITUTIONAL_SHARD_COUNT:{expected_shard_count}")
    if expected_shard_count is not None and observed_counts and observed_counts != {expected_shard_count}:
        blockers.append(
            "CONSTITUTIONAL_SHARD_COUNT_MISMATCH:"
            + ",".join(str(item) for item in sorted(observed_counts))
            + f":expected={expected_shard_count}"
        )
    elif len(observed_counts) > 1:
        blockers.append(
            "CONSTITUTIONAL_SHARD_COUNT_MISMATCH:"
            + ",".join(str(item) for item in sorted(observed_counts))
        )

    missing_indexes: list[int] = []
    if inferred_count is not None and inferred_count > 0:
        missing_indexes = [index for index in range(1, inferred_count + 1) if index not in seen_indexes]
        for index in missing_indexes:
            blockers.append(f"CONSTITUTIONAL_SHARD_INDEX_MISSING:{index}")
    else:
        blockers.append("CONSTITUTIONAL_SHARD_COUNT_NOT_INFERRED")

    output = _normalise_report_path(output_path) if output_path is not None else DEFAULT_CONSTITUTIONAL_SUMMARY_OUTPUT
    source_report_seal = tuple(
        {
            "sha256": item.get("sha256"),
            "constitutional_shard_count": item.get("constitutional_shard_count"),
            "constitutional_shard_index": item.get("constitutional_shard_index"),
            "covered_constitutional_test_files": item.get("covered_constitutional_test_files"),
            "constitutional_source_tree_manifest_sha256": item.get("constitutional_source_tree_manifest_sha256"),
        }
        for item in sorted(
            source_payloads,
            key=lambda value: (value.get("constitutional_shard_index") or 0, value.get("path") or ""),
        )
    )
    payload = {
        "schema_version": "certification_stability_constitutional_summary/v2",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output),
        "constitutional_shard_count": inferred_count,
        "observed_shard_indexes": sorted(seen_indexes),
        "missing_shard_indexes": missing_indexes,
        "duplicate_shard_indexes": sorted(set(duplicate_indexes)),
        "passed_shard_count": max(0, len(seen_indexes) - len(failed_constitutional_shards)),
        "failed_shard_count": len(failed_constitutional_shards),
        "timed_out_shard_count": len(timed_out_constitutional_shards),
        "nonzero_shard_count": len(nonzero_constitutional_shards),
        "failed_constitutional_shards": failed_constitutional_shards,
        "timed_out_constitutional_shards": timed_out_constitutional_shards,
        "nonzero_constitutional_shards": nonzero_constitutional_shards,
        "first_failed_shard": failed_constitutional_shards[0] if failed_constitutional_shards else None,
        "next_diagnostic": "inspect failed_constitutional_shards and rerun the listed shard index with --constitutional-shard-index" if failed_constitutional_shards else None,
        "expected_constitutional_test_file_count": len(expected_test_files),
        "covered_constitutional_test_file_count": len(observed_test_files),
        "covered_constitutional_test_files": sorted(observed_test_files),
        "missing_constitutional_test_files": missing_test_files,
        "duplicate_constitutional_test_files": sorted(duplicate_test_files),
        "unexpected_constitutional_test_files": sorted(unexpected_test_files),
        "constitutional_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_report_count": len(source_payloads),
        "source_reports_sha256": _canonical_json_digest(list(source_report_seal)),
        "source_reports": source_payloads,
        "warnings": warnings,
        "blockers": blockers,
    }
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _verify_constitutional_summary_report(
    summary_path: str | Path,
    *,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    """Verify a constitutional shard summary against the current repo and source reports.

    The aggregate summary is an audit artifact, not a secret-bearing signature.
    Verification therefore checks tamper evidence and freshness: the summary
    self-digest, current repo root/source-tree identity, coverage invariants, and
    the content digests of every referenced shard report.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    path = _normalise_report_path(summary_path)
    payload: dict[str, object] | None = None

    if not path.exists():
        blockers.append(f"CONSTITUTIONAL_SUMMARY_REPORT_MISSING:{path}")
    else:
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))

    expected_source_manifest = _constitutional_source_manifest()
    expected_source_manifest_digest = _constitutional_source_manifest_digest()
    expected_test_files = set(_expected_constitutional_test_files())
    source_report_mismatches: list[str] = []
    source_reports_seal: tuple[dict[str, object], ...] = tuple()

    if payload is not None:
        schema = payload.get("schema_version")
        if schema != "certification_stability_constitutional_summary/v2":
            blockers.append(f"UNSUPPORTED_CONSTITUTIONAL_SUMMARY_SCHEMA:{schema}")
        if payload.get("status") != "PASS":
            blockers.append(f"CONSTITUTIONAL_SUMMARY_NOT_PASSING:{payload.get('status')}")
        if payload.get("repo_root") != str(REPO_ROOT):
            blockers.append(f"CONSTITUTIONAL_SUMMARY_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
        if payload.get("blockers") not in ([], None):
            blockers.append("CONSTITUTIONAL_SUMMARY_HAS_BLOCKERS")
        _verify_exact_shard_blocker_fields(
            payload=payload,
            blockers=blockers,
            prefix="CONSTITUTIONAL_SUMMARY",
            detail_field="failed_constitutional_shards",
            timed_out_field="timed_out_constitutional_shards",
            nonzero_field="nonzero_constitutional_shards",
        )

        declared_digest = payload.get("summary_payload_sha256")
        recomputed_digest = _summary_payload_digest(payload)
        if declared_digest != recomputed_digest:
            blockers.append(
                f"CONSTITUTIONAL_SUMMARY_PAYLOAD_DIGEST_MISMATCH:{declared_digest}:expected={recomputed_digest}"
            )

        source_tree = payload.get("constitutional_source_tree")
        if not isinstance(source_tree, dict):
            blockers.append("CONSTITUTIONAL_SUMMARY_SOURCE_TREE_MISSING")
        else:
            if source_tree.get("manifest_sha256") != expected_source_manifest_digest:
                blockers.append(
                    "CONSTITUTIONAL_SUMMARY_SOURCE_TREE_MISMATCH:"
                    + f"{source_tree.get('manifest_sha256')}:expected={expected_source_manifest_digest}"
                )
            if source_tree.get("file_count") != len(expected_source_manifest):
                blockers.append(
                    "CONSTITUTIONAL_SUMMARY_SOURCE_TREE_FILE_COUNT_MISMATCH:"
                    + f"{source_tree.get('file_count')}:expected={len(expected_source_manifest)}"
                )

        covered_files = payload.get("covered_constitutional_test_files")
        if not isinstance(covered_files, list):
            blockers.append("CONSTITUTIONAL_SUMMARY_COVERAGE_LIST_MISSING")
            covered_set: set[str] = set()
        else:
            covered_set = {item for item in covered_files if isinstance(item, str)}
            if len(covered_set) != len(covered_files):
                blockers.append("CONSTITUTIONAL_SUMMARY_COVERAGE_HAS_DUPLICATES_OR_INVALID_ITEMS")
        missing_from_summary = sorted(expected_test_files.difference(covered_set))
        unexpected_in_summary = sorted(covered_set.difference(expected_test_files))
        if missing_from_summary:
            blockers.extend(f"CONSTITUTIONAL_SUMMARY_MISSING_TEST_FILE:{item}" for item in missing_from_summary)
        if unexpected_in_summary:
            blockers.extend(f"CONSTITUTIONAL_SUMMARY_UNEXPECTED_TEST_FILE:{item}" for item in unexpected_in_summary)
        if payload.get("missing_constitutional_test_files") not in ([], None):
            blockers.append("CONSTITUTIONAL_SUMMARY_DECLARED_MISSING_TEST_FILES")
        if payload.get("duplicate_constitutional_test_files") not in ([], None):
            blockers.append("CONSTITUTIONAL_SUMMARY_DECLARED_DUPLICATE_TEST_FILES")
        if payload.get("unexpected_constitutional_test_files") not in ([], None):
            blockers.append("CONSTITUTIONAL_SUMMARY_DECLARED_UNEXPECTED_TEST_FILES")
        if payload.get("covered_constitutional_test_file_count") != len(covered_set):
            blockers.append(
                "CONSTITUTIONAL_SUMMARY_COVERED_COUNT_MISMATCH:"
                + f"{payload.get('covered_constitutional_test_file_count')}:expected={len(covered_set)}"
            )
        if payload.get("expected_constitutional_test_file_count") != len(expected_test_files):
            blockers.append(
                "CONSTITUTIONAL_SUMMARY_EXPECTED_COUNT_MISMATCH:"
                + f"{payload.get('expected_constitutional_test_file_count')}:expected={len(expected_test_files)}"
            )

        source_reports = payload.get("source_reports")
        if not isinstance(source_reports, list) or not source_reports:
            blockers.append("CONSTITUTIONAL_SUMMARY_SOURCE_REPORTS_MISSING")
            source_reports = []
        source_report_seal_items: list[dict[str, object]] = []
        for item in source_reports:
            if not isinstance(item, dict):
                blockers.append("CONSTITUTIONAL_SUMMARY_SOURCE_REPORT_INVALID")
                continue
            report_path_value = item.get("path")
            report_sha_value = item.get("sha256")
            if not isinstance(report_path_value, str):
                blockers.append("CONSTITUTIONAL_SUMMARY_SOURCE_REPORT_PATH_INVALID")
                continue
            report_path = _normalise_report_path(report_path_value)
            if not report_path.exists():
                blockers.append(f"CONSTITUTIONAL_SUMMARY_SOURCE_REPORT_MISSING:{report_path}")
                continue
            observed_sha = _sha256_file(report_path)
            if observed_sha != report_sha_value:
                source_report_mismatches.append(str(report_path))
                blockers.append(
                    f"CONSTITUTIONAL_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH:{report_path}:{observed_sha}:expected={report_sha_value}"
                )
            source_report_seal_items.append(
                {
                    "sha256": report_sha_value,
                    "constitutional_shard_count": item.get("constitutional_shard_count"),
                    "constitutional_shard_index": item.get("constitutional_shard_index"),
                    "covered_constitutional_test_files": item.get("covered_constitutional_test_files"),
                    "constitutional_source_tree_manifest_sha256": item.get("constitutional_source_tree_manifest_sha256"),
                }
            )
        source_reports_seal = tuple(
            sorted(
                source_report_seal_items,
                key=lambda value: (value.get("constitutional_shard_index") or 0, value.get("sha256") or ""),
            )
        )
        declared_source_reports_sha = payload.get("source_reports_sha256")
        recomputed_source_reports_sha = _canonical_json_digest(list(source_reports_seal))
        if declared_source_reports_sha != recomputed_source_reports_sha:
            blockers.append(
                f"CONSTITUTIONAL_SUMMARY_SOURCE_REPORTS_DIGEST_MISMATCH:{declared_source_reports_sha}:expected={recomputed_source_reports_sha}"
            )

    output = _normalise_report_path(output_path) if output_path is not None else path.with_name(path.stem + "_verification.json")
    verification = {
        "schema_version": "certification_stability_constitutional_summary_verification/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "summary_path": str(path),
        "output_path": str(output),
        "constitutional_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_report_mismatch_count": len(source_report_mismatches),
        "source_report_mismatches": source_report_mismatches,
        "warnings": warnings,
        "blockers": blockers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification



def _aggregate_collection_shard_reports(
    report_paths: Sequence[str | Path],
    *,
    expected_shard_count: int | None = None,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    """Aggregate resumable full-test collection shard reports into one proof artifact."""
    blockers: list[str] = []
    warnings: list[str] = []
    source_payloads: list[dict[str, object]] = []
    seen_indexes: dict[int, Path] = {}
    duplicate_indexes: list[int] = []
    observed_counts: set[int] = set()
    expected_test_files = set(_expected_collection_test_files())
    expected_source_manifest = _collection_source_manifest()
    expected_source_manifest_digest = _collection_source_manifest_digest()
    observed_test_files: dict[str, Path] = {}
    duplicate_test_files: dict[str, list[Path]] = {}
    unexpected_test_files: dict[str, Path] = {}
    failed_collection_shards: list[dict[str, object]] = []
    timed_out_collection_shards: list[dict[str, object]] = []
    nonzero_collection_shards: list[dict[str, object]] = []

    normalised_paths = tuple(_normalise_report_path(path) for path in report_paths)
    if not normalised_paths:
        blockers.append("NO_COLLECTION_SHARD_REPORTS_PROVIDED")

    for path in normalised_paths:
        if not path.exists():
            blockers.append(f"COLLECTION_SHARD_REPORT_MISSING:{path}")
            continue
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))
            continue

        schema = payload.get("schema_version")
        phases = payload.get("phases")
        status = payload.get("status")
        shard_count = payload.get("collection_shard_count")
        shard_index = payload.get("collection_shard_index")
        steps = payload.get("steps")
        repo_root = payload.get("repo_root")
        source_tree = payload.get("collection_source_tree")

        if schema != "certification_stability/v2":
            blockers.append(f"UNSUPPORTED_COLLECTION_SHARD_REPORT_SCHEMA:{path}:{schema}")
        if repo_root != str(REPO_ROOT):
            blockers.append(f"COLLECTION_SHARD_REPO_ROOT_MISMATCH:{path}:{repo_root}:expected={REPO_ROOT}")
        if not isinstance(source_tree, dict):
            blockers.append(f"COLLECTION_SHARD_SOURCE_TREE_MISSING:{path}")
        else:
            observed_digest = source_tree.get("manifest_sha256")
            observed_count = source_tree.get("file_count")
            if observed_digest != expected_source_manifest_digest:
                blockers.append(
                    f"COLLECTION_SHARD_SOURCE_TREE_MISMATCH:{path}:{observed_digest}:expected={expected_source_manifest_digest}"
                )
            if observed_count != len(expected_source_manifest):
                blockers.append(
                    f"COLLECTION_SHARD_SOURCE_TREE_FILE_COUNT_MISMATCH:{path}:{observed_count}:expected={len(expected_source_manifest)}"
                )
        if phases != ["collect_shards"]:
            blockers.append(f"NON_COLLECTION_SHARD_REPORT:{path}:{phases}")
        if not isinstance(shard_count, int) or shard_count <= 0:
            blockers.append(f"INVALID_COLLECTION_SHARD_COUNT:{path}:{shard_count}")
        else:
            observed_counts.add(shard_count)
        if not isinstance(shard_index, int) or shard_index <= 0:
            blockers.append(f"INVALID_COLLECTION_SHARD_INDEX:{path}:{shard_index}")
        elif isinstance(shard_count, int) and shard_index > shard_count:
            blockers.append(f"COLLECTION_SHARD_INDEX_OUT_OF_RANGE:{path}:{shard_index}>{shard_count}")
        else:
            previous = seen_indexes.get(shard_index)
            if previous is not None:
                duplicate_indexes.append(shard_index)
                blockers.append(f"DUPLICATE_COLLECTION_SHARD_INDEX:{shard_index}:{previous}:{path}")
            else:
                seen_indexes[shard_index] = path
        if status != "PASS":
            blockers.append(f"COLLECTION_SHARD_REPORT_NOT_PASSING:{path}:{status}")
        if not isinstance(steps, list) or len(steps) != 1:
            blockers.append(f"COLLECTION_SHARD_REPORT_EXPECTED_ONE_STEP:{path}")
        else:
            step = steps[0]
            if not isinstance(step, dict):
                blockers.append(f"COLLECTION_SHARD_STEP_INVALID:{path}")
            else:
                timed_out = step.get("timed_out") is not False
                nonzero = step.get("exit_code") != 0
                if timed_out:
                    blockers.append(f"COLLECTION_SHARD_TIMED_OUT:{path}:{step.get('name')}")
                if nonzero:
                    blockers.append(f"COLLECTION_SHARD_NONZERO_EXIT:{path}:{step.get('name')}:{step.get('exit_code')}")
                if status != "PASS" or timed_out or nonzero:
                    shard_detail = _shard_failure_detail(
                        path=path,
                        shard_index=shard_index,
                        shard_count=shard_count,
                        step=step,
                        failed_step=payload.get("failed_step"),
                        timeout_seconds=payload.get("timeout_seconds"),
                    )
                    failed_collection_shards.append(shard_detail)
                    if timed_out:
                        timed_out_collection_shards.append(shard_detail)
                    if nonzero:
                        nonzero_collection_shards.append(shard_detail)
                command = step.get("command")
                command_files = _command_collection_test_files(command)
                if not command_files:
                    blockers.append(f"COLLECTION_SHARD_COMMAND_MISSING_TEST_FILES:{path}")
                for test_file in command_files:
                    if test_file not in expected_test_files:
                        unexpected_test_files[test_file] = path
                    previous = observed_test_files.get(test_file)
                    if previous is not None:
                        duplicate_test_files.setdefault(test_file, [previous]).append(path)
                    else:
                        observed_test_files[test_file] = path

        source_payloads.append(
            {
                "path": str(path),
                "sha256": _sha256_file(path),
                "status": status,
                "failed_step": payload.get("failed_step"),
                "collection_shard_count": shard_count,
                "collection_shard_index": shard_index,
                "repo_root": repo_root,
                "collection_source_tree_manifest_sha256": (
                    source_tree.get("manifest_sha256") if isinstance(source_tree, dict) else None
                ),
                "step_names": [step.get("name") for step in steps if isinstance(step, dict)] if isinstance(steps, list) else [],
                "covered_collection_test_files": (
                    list(_command_collection_test_files(steps[0].get("command")))
                    if isinstance(steps, list) and len(steps) == 1 and isinstance(steps[0], dict)
                    else []
                ),
            }
        )

    missing_test_files = sorted(expected_test_files.difference(observed_test_files))
    for test_file in missing_test_files:
        blockers.append(f"COLLECTION_TEST_FILE_MISSING_FROM_SHARDS:{test_file}")
    for test_file, paths in sorted(duplicate_test_files.items()):
        blockers.append(
            "COLLECTION_TEST_FILE_DUPLICATED_ACROSS_SHARDS:"
            + test_file
            + ":"
            + ":".join(str(path) for path in paths)
        )
    for test_file, path in sorted(unexpected_test_files.items()):
        blockers.append(f"COLLECTION_TEST_FILE_UNEXPECTED_IN_SHARD:{test_file}:{path}")

    inferred_count: int | None = expected_shard_count
    if inferred_count is None and len(observed_counts) == 1:
        inferred_count = next(iter(observed_counts))
    elif inferred_count is None and observed_counts:
        inferred_count = max(observed_counts)

    if expected_shard_count is not None and expected_shard_count <= 0:
        blockers.append(f"INVALID_EXPECTED_COLLECTION_SHARD_COUNT:{expected_shard_count}")
    if expected_shard_count is not None and observed_counts and observed_counts != {expected_shard_count}:
        blockers.append(
            "COLLECTION_SHARD_COUNT_MISMATCH:"
            + ",".join(str(item) for item in sorted(observed_counts))
            + f":expected={expected_shard_count}"
        )
    elif len(observed_counts) > 1:
        blockers.append("COLLECTION_SHARD_COUNT_MISMATCH:" + ",".join(str(item) for item in sorted(observed_counts)))

    missing_indexes: list[int] = []
    if inferred_count is not None and inferred_count > 0:
        missing_indexes = [index for index in range(1, inferred_count + 1) if index not in seen_indexes]
        for index in missing_indexes:
            blockers.append(f"COLLECTION_SHARD_INDEX_MISSING:{index}")
    else:
        blockers.append("COLLECTION_SHARD_COUNT_NOT_INFERRED")

    output = _normalise_report_path(output_path) if output_path is not None else DEFAULT_COLLECTION_SUMMARY_OUTPUT
    source_report_seal = tuple(
        {
            "sha256": item.get("sha256"),
            "collection_shard_count": item.get("collection_shard_count"),
            "collection_shard_index": item.get("collection_shard_index"),
            "covered_collection_test_files": item.get("covered_collection_test_files"),
            "collection_source_tree_manifest_sha256": item.get("collection_source_tree_manifest_sha256"),
        }
        for item in sorted(source_payloads, key=lambda value: (value.get("collection_shard_index") or 0, value.get("path") or ""))
    )
    payload = {
        "schema_version": "certification_stability_collection_summary/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output),
        "collection_shard_count": inferred_count,
        "observed_shard_indexes": sorted(seen_indexes),
        "missing_shard_indexes": missing_indexes,
        "duplicate_shard_indexes": sorted(set(duplicate_indexes)),
        "passed_shard_count": max(0, len(seen_indexes) - len(failed_collection_shards)),
        "failed_shard_count": len(failed_collection_shards),
        "timed_out_shard_count": len(timed_out_collection_shards),
        "nonzero_shard_count": len(nonzero_collection_shards),
        "failed_collection_shards": failed_collection_shards,
        "timed_out_collection_shards": timed_out_collection_shards,
        "nonzero_collection_shards": nonzero_collection_shards,
        "first_failed_shard": failed_collection_shards[0] if failed_collection_shards else None,
        "next_diagnostic": "inspect failed_collection_shards and rerun the listed shard index with --collection-shard-index" if failed_collection_shards else None,
        "expected_collection_test_file_count": len(expected_test_files),
        "covered_collection_test_file_count": len(observed_test_files),
        "covered_collection_test_files": sorted(observed_test_files),
        "missing_collection_test_files": missing_test_files,
        "duplicate_collection_test_files": {key: [str(path) for path in paths] for key, paths in sorted(duplicate_test_files.items())},
        "unexpected_collection_test_files": {key: str(path) for key, path in sorted(unexpected_test_files.items())},
        "collection_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_reports": source_payloads,
        "source_reports_sha256": _canonical_json_digest(list(source_report_seal)),
        "warnings": warnings,
        "blockers": blockers,
    }
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _verify_collection_summary_report(summary_path: str | Path, *, output_path: str | Path | None = None) -> dict[str, object]:
    """Verify an aggregated collection shard summary against the current tree and source reports."""
    path = _normalise_report_path(summary_path)
    blockers: list[str] = []
    warnings: list[str] = []
    source_report_mismatches: list[str] = []
    expected_files = set(_expected_collection_test_files())
    expected_source_manifest = _collection_source_manifest()
    expected_source_manifest_digest = _collection_source_manifest_digest()

    if not path.exists():
        blockers.append(f"COLLECTION_SUMMARY_MISSING:{path}")
        payload: dict[str, object] | None = None
    else:
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))
            payload = None

    if payload is not None:
        if payload.get("schema_version") != "certification_stability_collection_summary/v1":
            blockers.append(f"COLLECTION_SUMMARY_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
        if payload.get("status") != "PASS":
            blockers.append(f"COLLECTION_SUMMARY_NOT_PASSING:{payload.get('status')}")
        if payload.get("blockers"):
            blockers.append("COLLECTION_SUMMARY_HAS_BLOCKERS")
        _verify_exact_shard_blocker_fields(
            payload=payload,
            blockers=blockers,
            prefix="COLLECTION_SUMMARY",
            detail_field="failed_collection_shards",
            timed_out_field="timed_out_collection_shards",
            nonzero_field="nonzero_collection_shards",
        )
        if payload.get("repo_root") != str(REPO_ROOT):
            blockers.append(f"COLLECTION_SUMMARY_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
        declared_payload_sha = payload.get("summary_payload_sha256")
        observed_payload_sha = _summary_payload_digest(payload)
        if declared_payload_sha != observed_payload_sha:
            blockers.append(f"COLLECTION_SUMMARY_PAYLOAD_DIGEST_MISMATCH:{declared_payload_sha}:expected={observed_payload_sha}")
        source_tree = payload.get("collection_source_tree")
        if not isinstance(source_tree, dict):
            blockers.append("COLLECTION_SUMMARY_SOURCE_TREE_MISSING")
        else:
            if source_tree.get("manifest_sha256") != expected_source_manifest_digest:
                blockers.append(
                    f"COLLECTION_SUMMARY_SOURCE_TREE_MISMATCH:{source_tree.get('manifest_sha256')}:expected={expected_source_manifest_digest}"
                )
            if source_tree.get("file_count") != len(expected_source_manifest):
                blockers.append(
                    f"COLLECTION_SUMMARY_SOURCE_TREE_FILE_COUNT_MISMATCH:{source_tree.get('file_count')}:expected={len(expected_source_manifest)}"
                )
        covered_files = payload.get("covered_collection_test_files")
        if not isinstance(covered_files, list):
            blockers.append("COLLECTION_SUMMARY_COVERED_FILES_NOT_LIST")
            covered_set: set[str] = set()
        else:
            covered_set = {item for item in covered_files if isinstance(item, str)}
        missing = sorted(expected_files.difference(covered_set))
        unexpected = sorted(covered_set.difference(expected_files))
        if missing:
            blockers.append("COLLECTION_SUMMARY_MISSING_TEST_FILES:" + ",".join(missing[:20]))
        if unexpected:
            blockers.append("COLLECTION_SUMMARY_UNEXPECTED_TEST_FILES:" + ",".join(unexpected[:20]))
        if isinstance(covered_files, list) and len(covered_set) != len(covered_files):
            blockers.append("COLLECTION_SUMMARY_DUPLICATED_COVERED_FILES")
        source_reports = payload.get("source_reports")
        source_report_seal_items: list[dict[str, object]] = []
        if not isinstance(source_reports, list):
            blockers.append("COLLECTION_SUMMARY_SOURCE_REPORTS_NOT_LIST")
            source_reports = []
        for item in source_reports:
            if not isinstance(item, dict):
                blockers.append("COLLECTION_SUMMARY_SOURCE_REPORT_INVALID")
                continue
            report_path_value = item.get("path")
            report_sha_value = item.get("sha256")
            if not isinstance(report_path_value, str):
                blockers.append("COLLECTION_SUMMARY_SOURCE_REPORT_PATH_INVALID")
                continue
            report_path = _normalise_report_path(report_path_value)
            if not report_path.exists():
                blockers.append(f"COLLECTION_SUMMARY_SOURCE_REPORT_MISSING:{report_path}")
                continue
            observed_sha = _sha256_file(report_path)
            if observed_sha != report_sha_value:
                source_report_mismatches.append(str(report_path))
                blockers.append(f"COLLECTION_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH:{report_path}:{observed_sha}:expected={report_sha_value}")
            source_report_seal_items.append(
                {
                    "sha256": report_sha_value,
                    "collection_shard_count": item.get("collection_shard_count"),
                    "collection_shard_index": item.get("collection_shard_index"),
                    "covered_collection_test_files": item.get("covered_collection_test_files"),
                    "collection_source_tree_manifest_sha256": item.get("collection_source_tree_manifest_sha256"),
                }
            )
        source_reports_seal = tuple(
            sorted(source_report_seal_items, key=lambda value: (value.get("collection_shard_index") or 0, value.get("sha256") or ""))
        )
        declared_source_reports_sha = payload.get("source_reports_sha256")
        recomputed_source_reports_sha = _canonical_json_digest(list(source_reports_seal))
        if declared_source_reports_sha != recomputed_source_reports_sha:
            blockers.append(f"COLLECTION_SUMMARY_SOURCE_REPORTS_DIGEST_MISMATCH:{declared_source_reports_sha}:expected={recomputed_source_reports_sha}")

    output = _normalise_report_path(output_path) if output_path is not None else path.with_name(path.stem + "_verification.json")
    verification = {
        "schema_version": "certification_stability_collection_summary_verification/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "summary_path": str(path),
        "output_path": str(output),
        "collection_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_report_mismatch_count": len(source_report_mismatches),
        "source_report_mismatches": source_report_mismatches,
        "warnings": warnings,
        "blockers": blockers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification



def _parse_pytest_test_count(stdout: object, stderr: object = "") -> int | None:
    import re

    text = "\n".join(part for part in (stdout, stderr) if isinstance(part, str))
    patterns = (
        r"(?P<count>\d+)\s+passed",
        r"(?P<count>\d+)\s+failed",
        r"(?P<count>\d+)\s+errors?",
        r"(?P<count>\d+)\s+skipped",
        r"(?P<count>\d+)\s+selected",
    )
    counts: list[int] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            counts.append(int(match.group("count")))
    if counts:
        return sum(counts)
    return None


def _aggregate_pytest_execution_shard_reports(
    report_paths: Sequence[str | Path],
    *,
    expected_shard_count: int | None = None,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    """Aggregate bounded backend pytest execution shard reports into one proof artifact."""
    blockers: list[str] = []
    warnings: list[str] = []
    source_payloads: list[dict[str, object]] = []
    seen_indexes: dict[int, Path] = {}
    duplicate_indexes: list[int] = []
    observed_counts: set[int] = set()
    expected_test_files = set(_expected_collection_test_files())
    expected_source_manifest = _pytest_execution_source_manifest()
    expected_source_manifest_digest = _pytest_execution_source_manifest_digest()
    observed_test_files: dict[str, Path] = {}
    duplicate_test_files: dict[str, list[Path]] = {}
    unexpected_test_files: dict[str, Path] = {}
    total_test_count = 0
    total_duration = 0.0
    test_count_unknown_shards: list[str] = []
    failed_pytest_execution_shards: list[dict[str, object]] = []
    timed_out_pytest_execution_shards: list[dict[str, object]] = []
    nonzero_pytest_execution_shards: list[dict[str, object]] = []

    normalised_paths = tuple(_normalise_report_path(path) for path in report_paths)
    if not normalised_paths:
        blockers.append("NO_PYTEST_EXECUTION_SHARD_REPORTS_PROVIDED")

    for path in normalised_paths:
        if not path.exists():
            blockers.append(f"PYTEST_EXECUTION_SHARD_REPORT_MISSING:{path}")
            continue
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))
            continue

        schema = payload.get("schema_version")
        phases = payload.get("phases")
        status = payload.get("status")
        shard_count = payload.get("pytest_shard_count")
        shard_index = payload.get("pytest_shard_index")
        steps = payload.get("steps")
        repo_root = payload.get("repo_root")
        source_tree = payload.get("pytest_execution_source_tree") or payload.get("collection_source_tree")

        if schema != "certification_stability/v2":
            blockers.append(f"UNSUPPORTED_PYTEST_EXECUTION_SHARD_REPORT_SCHEMA:{path}:{schema}")
        if repo_root != str(REPO_ROOT):
            blockers.append(f"PYTEST_EXECUTION_SHARD_REPO_ROOT_MISMATCH:{path}:{repo_root}:expected={REPO_ROOT}")
        if not isinstance(source_tree, dict):
            blockers.append(f"PYTEST_EXECUTION_SHARD_SOURCE_TREE_MISSING:{path}")
        else:
            observed_digest = source_tree.get("manifest_sha256")
            observed_count = source_tree.get("file_count")
            if observed_digest != expected_source_manifest_digest:
                blockers.append(
                    f"PYTEST_EXECUTION_SHARD_SOURCE_TREE_MISMATCH:{path}:{observed_digest}:expected={expected_source_manifest_digest}"
                )
            if observed_count != len(expected_source_manifest):
                blockers.append(
                    f"PYTEST_EXECUTION_SHARD_SOURCE_TREE_FILE_COUNT_MISMATCH:{path}:{observed_count}:expected={len(expected_source_manifest)}"
                )
        if phases != ["pytest_execution_shards"]:
            blockers.append(f"NON_PYTEST_EXECUTION_SHARD_REPORT:{path}:{phases}")
        if not isinstance(shard_count, int) or shard_count <= 0:
            blockers.append(f"INVALID_PYTEST_EXECUTION_SHARD_COUNT:{path}:{shard_count}")
        else:
            observed_counts.add(shard_count)
        if not isinstance(shard_index, int) or shard_index <= 0:
            blockers.append(f"INVALID_PYTEST_EXECUTION_SHARD_INDEX:{path}:{shard_index}")
        elif isinstance(shard_count, int) and shard_index > shard_count:
            blockers.append(f"PYTEST_EXECUTION_SHARD_INDEX_OUT_OF_RANGE:{path}:{shard_index}>{shard_count}")
        else:
            previous = seen_indexes.get(shard_index)
            if previous is not None:
                duplicate_indexes.append(shard_index)
                blockers.append(f"DUPLICATE_PYTEST_EXECUTION_SHARD_INDEX:{shard_index}:{previous}:{path}")
            else:
                seen_indexes[shard_index] = path
        if status != "PASS":
            blockers.append(f"PYTEST_EXECUTION_SHARD_REPORT_NOT_PASSING:{path}:{status}")
        if not isinstance(steps, list) or len(steps) != 1:
            blockers.append(f"PYTEST_EXECUTION_SHARD_REPORT_EXPECTED_ONE_STEP:{path}")
            step_payload: dict[str, object] | None = None
        else:
            step = steps[0]
            step_payload = step if isinstance(step, dict) else None
            if not isinstance(step, dict):
                blockers.append(f"PYTEST_EXECUTION_SHARD_STEP_INVALID:{path}")
            else:
                shard_detail = {
                    "path": str(path),
                    "shard_index": shard_index,
                    "shard_count": shard_count,
                    "step_name": step.get("name"),
                    "failed_step": payload.get("failed_step"),
                    "exit_code": step.get("exit_code"),
                    "timed_out": step.get("timed_out"),
                    "duration_seconds": step.get("duration_seconds"),
                    "timeout_seconds": payload.get("timeout_seconds"),
                    "stdout_tail": step.get("stdout_tail"),
                    "stderr_tail": step.get("stderr_tail"),
                }
                if status != "PASS" or step.get("timed_out") is not False or step.get("exit_code") != 0:
                    failed_pytest_execution_shards.append(shard_detail)
                if step.get("timed_out") is not False:
                    timed_out_pytest_execution_shards.append(shard_detail)
                    blockers.append(f"PYTEST_EXECUTION_SHARD_TIMED_OUT:{path}:{step.get('name')}")
                if step.get("exit_code") != 0:
                    nonzero_pytest_execution_shards.append(shard_detail)
                    blockers.append(f"PYTEST_EXECUTION_SHARD_NONZERO_EXIT:{path}:{step.get('name')}:{step.get('exit_code')}")
                duration = step.get("duration_seconds")
                if isinstance(duration, (int, float)):
                    total_duration += float(duration)
                command = step.get("command")
                command_files = _command_collection_test_files(command)
                if not command_files:
                    blockers.append(f"PYTEST_EXECUTION_SHARD_COMMAND_MISSING_TEST_FILES:{path}")
                for test_file in command_files:
                    if test_file not in expected_test_files:
                        unexpected_test_files[test_file] = path
                    previous = observed_test_files.get(test_file)
                    if previous is not None:
                        duplicate_test_files.setdefault(test_file, [previous]).append(path)
                    else:
                        observed_test_files[test_file] = path
                parsed_count = _parse_pytest_test_count(step.get("stdout_tail"), step.get("stderr_tail"))
                if parsed_count is None:
                    test_count_unknown_shards.append(str(path))
                else:
                    total_test_count += parsed_count

        covered_files = []
        if step_payload is not None:
            covered_files = list(_command_collection_test_files(step_payload.get("command")))
        source_payloads.append(
            {
                "path": str(path),
                "sha256": _sha256_file(path),
                "status": status,
                "failed_step": payload.get("failed_step"),
                "pytest_shard_count": shard_count,
                "pytest_shard_index": shard_index,
                "repo_root": repo_root,
                "pytest_execution_source_tree_manifest_sha256": (
                    source_tree.get("manifest_sha256") if isinstance(source_tree, dict) else None
                ),
                "step_names": [step.get("name") for step in steps if isinstance(step, dict)] if isinstance(steps, list) else [],
                "covered_pytest_execution_test_files": covered_files,
            }
        )

    missing_test_files = sorted(expected_test_files.difference(observed_test_files))
    for test_file in missing_test_files:
        blockers.append(f"PYTEST_EXECUTION_TEST_FILE_MISSING_FROM_SHARDS:{test_file}")
    for test_file, paths in sorted(duplicate_test_files.items()):
        blockers.append(
            "PYTEST_EXECUTION_TEST_FILE_DUPLICATED_ACROSS_SHARDS:"
            + test_file
            + ":"
            + ":".join(str(path) for path in paths)
        )
    for test_file, path in sorted(unexpected_test_files.items()):
        blockers.append(f"PYTEST_EXECUTION_TEST_FILE_UNEXPECTED_IN_SHARD:{test_file}:{path}")

    inferred_count: int | None = expected_shard_count
    if inferred_count is None and len(observed_counts) == 1:
        inferred_count = next(iter(observed_counts))
    elif inferred_count is None and observed_counts:
        inferred_count = max(observed_counts)
    if expected_shard_count is not None and expected_shard_count <= 0:
        blockers.append(f"INVALID_EXPECTED_PYTEST_EXECUTION_SHARD_COUNT:{expected_shard_count}")
    if expected_shard_count is not None and observed_counts and observed_counts != {expected_shard_count}:
        blockers.append(
            "PYTEST_EXECUTION_SHARD_COUNT_MISMATCH:"
            + ",".join(str(item) for item in sorted(observed_counts))
            + f":expected={expected_shard_count}"
        )
    elif len(observed_counts) > 1:
        blockers.append("PYTEST_EXECUTION_SHARD_COUNT_MISMATCH:" + ",".join(str(item) for item in sorted(observed_counts)))
    missing_indexes: list[int] = []
    if inferred_count is not None and inferred_count > 0:
        missing_indexes = [index for index in range(1, inferred_count + 1) if index not in seen_indexes]
        for index in missing_indexes:
            blockers.append(f"PYTEST_EXECUTION_SHARD_INDEX_MISSING:{index}")
    else:
        blockers.append("PYTEST_EXECUTION_SHARD_COUNT_NOT_INFERRED")

    output = _normalise_report_path(output_path) if output_path is not None else DEFAULT_PYTEST_EXECUTION_SUMMARY_OUTPUT
    source_report_seal = tuple(
        {
            "sha256": item.get("sha256"),
            "pytest_shard_count": item.get("pytest_shard_count"),
            "pytest_shard_index": item.get("pytest_shard_index"),
            "covered_pytest_execution_test_files": item.get("covered_pytest_execution_test_files"),
            "pytest_execution_source_tree_manifest_sha256": item.get("pytest_execution_source_tree_manifest_sha256"),
        }
        for item in sorted(source_payloads, key=lambda value: (value.get("pytest_shard_index") or 0, value.get("path") or ""))
    )
    payload = {
        "schema_version": "certification_stability_pytest_execution_summary/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output),
        "pytest_shard_count": inferred_count,
        "observed_shard_indexes": sorted(seen_indexes),
        "missing_shard_indexes": missing_indexes,
        "duplicate_shard_indexes": sorted(set(duplicate_indexes)),
        "passed_shard_count": len([item for item in source_payloads if item.get("status") == "PASS"]),
        "failed_shard_count": len(failed_pytest_execution_shards),
        "timed_out_shard_count": len(timed_out_pytest_execution_shards),
        "nonzero_shard_count": len(nonzero_pytest_execution_shards),
        "failed_pytest_execution_shards": failed_pytest_execution_shards,
        "timed_out_pytest_execution_shards": timed_out_pytest_execution_shards,
        "nonzero_pytest_execution_shards": nonzero_pytest_execution_shards,
        "first_failed_shard": failed_pytest_execution_shards[0] if failed_pytest_execution_shards else None,
        "next_diagnostic": "inspect failed_pytest_execution_shards and rerun the listed shard index with --pytest-shard-index" if failed_pytest_execution_shards else None,
        "expected_pytest_execution_test_file_count": len(expected_test_files),
        "covered_pytest_execution_test_file_count": len(observed_test_files),
        "covered_pytest_execution_test_files": sorted(observed_test_files),
        "missing_pytest_execution_test_files": missing_test_files,
        "duplicate_pytest_execution_test_files": {key: [str(path) for path in paths] for key, paths in sorted(duplicate_test_files.items())},
        "unexpected_pytest_execution_test_files": {key: str(path) for key, path in sorted(unexpected_test_files.items())},
        "total_test_count": total_test_count,
        "total_duration_seconds": round(total_duration, 3),
        "test_count_unknown_shards": test_count_unknown_shards,
        "pytest_execution_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_reports": source_payloads,
        "source_reports_sha256": _canonical_json_digest(list(source_report_seal)),
        "warnings": warnings,
        "blockers": blockers,
    }
    payload["summary_payload_sha256"] = _summary_payload_digest(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _verify_pytest_execution_summary_report(summary_path: str | Path, *, output_path: str | Path | None = None) -> dict[str, object]:
    """Verify an aggregated backend pytest execution shard summary."""
    path = _normalise_report_path(summary_path)
    blockers: list[str] = []
    warnings: list[str] = []
    source_report_mismatches: list[str] = []
    expected_files = set(_expected_collection_test_files())
    expected_source_manifest = _pytest_execution_source_manifest()
    expected_source_manifest_digest = _pytest_execution_source_manifest_digest()

    if not path.exists():
        blockers.append(f"PYTEST_EXECUTION_SUMMARY_MISSING:{path}")
        payload: dict[str, object] | None = None
    else:
        try:
            payload = _load_json_report(path)
        except ValueError as exc:
            blockers.append(str(exc))
            payload = None

    if payload is not None:
        if payload.get("schema_version") != "certification_stability_pytest_execution_summary/v1":
            blockers.append(f"PYTEST_EXECUTION_SUMMARY_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
        if payload.get("status") != "PASS":
            blockers.append(f"PYTEST_EXECUTION_SUMMARY_NOT_PASSING:{payload.get('status')}")
        if payload.get("blockers"):
            blockers.append("PYTEST_EXECUTION_SUMMARY_HAS_BLOCKERS")
        for field_name in (
            "passed_shard_count",
            "failed_shard_count",
            "timed_out_shard_count",
            "nonzero_shard_count",
            "failed_pytest_execution_shards",
            "timed_out_pytest_execution_shards",
            "nonzero_pytest_execution_shards",
        ):
            if field_name not in payload:
                blockers.append(f"PYTEST_EXECUTION_SUMMARY_FIELD_MISSING:{field_name}")
        failed_details = payload.get("failed_pytest_execution_shards")
        timed_out_details = payload.get("timed_out_pytest_execution_shards")
        nonzero_details = payload.get("nonzero_pytest_execution_shards")
        if not isinstance(failed_details, list):
            blockers.append("PYTEST_EXECUTION_SUMMARY_FAILED_SHARDS_NOT_LIST")
            failed_details = []
        if not isinstance(timed_out_details, list):
            blockers.append("PYTEST_EXECUTION_SUMMARY_TIMED_OUT_SHARDS_NOT_LIST")
            timed_out_details = []
        if not isinstance(nonzero_details, list):
            blockers.append("PYTEST_EXECUTION_SUMMARY_NONZERO_SHARDS_NOT_LIST")
            nonzero_details = []
        if payload.get("failed_shard_count") != len(failed_details):
            blockers.append(
                f"PYTEST_EXECUTION_SUMMARY_FAILED_SHARD_COUNT_MISMATCH:{payload.get('failed_shard_count')}:expected={len(failed_details)}"
            )
        if payload.get("timed_out_shard_count") != len(timed_out_details):
            blockers.append(
                f"PYTEST_EXECUTION_SUMMARY_TIMED_OUT_SHARD_COUNT_MISMATCH:{payload.get('timed_out_shard_count')}:expected={len(timed_out_details)}"
            )
        if payload.get("nonzero_shard_count") != len(nonzero_details):
            blockers.append(
                f"PYTEST_EXECUTION_SUMMARY_NONZERO_SHARD_COUNT_MISMATCH:{payload.get('nonzero_shard_count')}:expected={len(nonzero_details)}"
            )
        for detail in failed_details:
            if not isinstance(detail, dict):
                blockers.append("PYTEST_EXECUTION_SUMMARY_FAILED_SHARD_DETAIL_INVALID")
                continue
            for field_name in ("path", "shard_index", "step_name", "exit_code", "timed_out", "duration_seconds", "timeout_seconds"):
                if field_name not in detail:
                    blockers.append(f"PYTEST_EXECUTION_SUMMARY_FAILED_SHARD_DETAIL_FIELD_MISSING:{field_name}")
        if payload.get("repo_root") != str(REPO_ROOT):
            blockers.append(f"PYTEST_EXECUTION_SUMMARY_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
        declared_payload_sha = payload.get("summary_payload_sha256")
        observed_payload_sha = _summary_payload_digest(payload)
        if declared_payload_sha != observed_payload_sha:
            blockers.append(f"PYTEST_EXECUTION_SUMMARY_PAYLOAD_DIGEST_MISMATCH:{declared_payload_sha}:expected={observed_payload_sha}")
        source_tree = payload.get("pytest_execution_source_tree")
        if not isinstance(source_tree, dict):
            blockers.append("PYTEST_EXECUTION_SUMMARY_SOURCE_TREE_MISSING")
        else:
            if source_tree.get("manifest_sha256") != expected_source_manifest_digest:
                blockers.append(
                    f"PYTEST_EXECUTION_SUMMARY_SOURCE_TREE_MISMATCH:{source_tree.get('manifest_sha256')}:expected={expected_source_manifest_digest}"
                )
            if source_tree.get("file_count") != len(expected_source_manifest):
                blockers.append(
                    f"PYTEST_EXECUTION_SUMMARY_SOURCE_TREE_FILE_COUNT_MISMATCH:{source_tree.get('file_count')}:expected={len(expected_source_manifest)}"
                )
        covered_files = payload.get("covered_pytest_execution_test_files")
        if not isinstance(covered_files, list):
            blockers.append("PYTEST_EXECUTION_SUMMARY_COVERED_FILES_NOT_LIST")
            covered_set: set[str] = set()
        else:
            covered_set = {item for item in covered_files if isinstance(item, str)}
        missing = sorted(expected_files.difference(covered_set))
        unexpected = sorted(covered_set.difference(expected_files))
        if missing:
            blockers.append("PYTEST_EXECUTION_SUMMARY_MISSING_TEST_FILES:" + ",".join(missing[:20]))
        if unexpected:
            blockers.append("PYTEST_EXECUTION_SUMMARY_UNEXPECTED_TEST_FILES:" + ",".join(unexpected[:20]))
        if isinstance(covered_files, list) and len(covered_set) != len(covered_files):
            blockers.append("PYTEST_EXECUTION_SUMMARY_DUPLICATED_COVERED_FILES")
        source_reports = payload.get("source_reports")
        source_report_seal_items: list[dict[str, object]] = []
        if not isinstance(source_reports, list):
            blockers.append("PYTEST_EXECUTION_SUMMARY_SOURCE_REPORTS_NOT_LIST")
            source_reports = []
        for item in source_reports:
            if not isinstance(item, dict):
                blockers.append("PYTEST_EXECUTION_SUMMARY_SOURCE_REPORT_INVALID")
                continue
            report_path_value = item.get("path")
            report_sha_value = item.get("sha256")
            if not isinstance(report_path_value, str):
                blockers.append("PYTEST_EXECUTION_SUMMARY_SOURCE_REPORT_PATH_INVALID")
                continue
            report_path = _normalise_report_path(report_path_value)
            if not report_path.exists():
                blockers.append(f"PYTEST_EXECUTION_SUMMARY_SOURCE_REPORT_MISSING:{report_path}")
                continue
            observed_sha = _sha256_file(report_path)
            if observed_sha != report_sha_value:
                source_report_mismatches.append(str(report_path))
                blockers.append(f"PYTEST_EXECUTION_SUMMARY_SOURCE_REPORT_SHA256_MISMATCH:{report_path}:{observed_sha}:expected={report_sha_value}")
            source_report_seal_items.append(
                {
                    "sha256": report_sha_value,
                    "pytest_shard_count": item.get("pytest_shard_count"),
                    "pytest_shard_index": item.get("pytest_shard_index"),
                    "covered_pytest_execution_test_files": item.get("covered_pytest_execution_test_files"),
                    "pytest_execution_source_tree_manifest_sha256": item.get("pytest_execution_source_tree_manifest_sha256"),
                }
            )
        source_reports_seal = tuple(
            sorted(source_report_seal_items, key=lambda value: (value.get("pytest_shard_index") or 0, value.get("sha256") or ""))
        )
        declared_source_reports_sha = payload.get("source_reports_sha256")
        recomputed_source_reports_sha = _canonical_json_digest(list(source_reports_seal))
        if declared_source_reports_sha != recomputed_source_reports_sha:
            blockers.append(f"PYTEST_EXECUTION_SUMMARY_SOURCE_REPORTS_DIGEST_MISMATCH:{declared_source_reports_sha}:expected={recomputed_source_reports_sha}")

    output = _normalise_report_path(output_path) if output_path is not None else path.with_name(path.stem + "_verification.json")
    verification = {
        "schema_version": "certification_stability_pytest_execution_summary_verification/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "summary_path": str(path),
        "output_path": str(output),
        "pytest_execution_source_tree": {
            "file_count": len(expected_source_manifest),
            "manifest_sha256": expected_source_manifest_digest,
        },
        "source_report_mismatch_count": len(source_report_mismatches),
        "source_report_mismatches": source_report_mismatches,
        "warnings": warnings,
        "blockers": blockers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification



SHARD_SUITE_NAMES = ("collection", "constitutional", "pytest-execution")


def _shard_suite_paths(suite: str, *, output_root: Path) -> dict[str, Path]:
    if suite == "collection":
        return {
            "report_dir": output_root / "collection_shards",
            "summary": output_root / "latest" / "collection_shards_summary.json",
            "verification": output_root / "latest" / "collection_shards_summary_verification.json",
        }
    if suite == "constitutional":
        return {
            "report_dir": output_root / "constitutional_shards",
            "summary": output_root / "latest" / "constitutional_shards_summary.json",
            "verification": output_root / "latest" / "constitutional_shards_summary_verification.json",
        }
    if suite == "pytest-execution":
        return {
            "report_dir": output_root / "pytest_execution_shards",
            "summary": output_root / "latest" / "pytest_execution_shards_summary.json",
            "verification": output_root / "latest" / "pytest_execution_shards_summary_verification.json",
        }
    raise ValueError(f"unsupported shard suite: {suite}")


def _shard_suite_command_parts(
    suite: str,
    *,
    py: str,
    shard_count: int,
    shard_index: int,
    timeout_seconds: int,
    heartbeat_seconds: int,
    report_path: Path,
) -> tuple[str, ...]:
    script = "scripts/certification_stability.py"
    if suite == "collection":
        return (
            py,
            script,
            "--phase",
            "collect-shards",
            "--collection-shard-count",
            str(shard_count),
            "--collection-shard-index",
            str(shard_index),
            "--timeout-seconds",
            str(timeout_seconds),
            "--heartbeat-seconds",
            str(heartbeat_seconds),
            "--output",
            report_path.as_posix(),
            "--json",
        )
    if suite == "constitutional":
        return (
            py,
            script,
            "--phase",
            "constitutional-shards",
            "--constitutional-shard-count",
            str(shard_count),
            "--constitutional-shard-index",
            str(shard_index),
            "--timeout-seconds",
            str(timeout_seconds),
            "--heartbeat-seconds",
            str(heartbeat_seconds),
            "--output",
            report_path.as_posix(),
            "--json",
        )
    if suite == "pytest-execution":
        return (
            py,
            script,
            "--phase",
            "pytest-execution-shards",
            "--pytest-shard-count",
            str(shard_count),
            "--pytest-shard-index",
            str(shard_index),
            "--timeout-seconds",
            str(timeout_seconds),
            "--heartbeat-seconds",
            str(heartbeat_seconds),
            "--output",
            report_path.as_posix(),
            "--json",
        )
    raise ValueError(f"unsupported shard suite: {suite}")


def _aggregate_command_parts(suite: str, *, py: str, shard_count: int, report_paths: Sequence[Path], summary_path: Path) -> tuple[str, ...]:
    script = "scripts/certification_stability.py"
    if suite == "collection":
        return (
            py,
            script,
            "--aggregate-collection-shard-reports",
            *(path.as_posix() for path in report_paths),
            "--collection-shard-count",
            str(shard_count),
            "--output",
            summary_path.as_posix(),
            "--json",
        )
    if suite == "constitutional":
        return (
            py,
            script,
            "--aggregate-constitutional-shard-reports",
            *(path.as_posix() for path in report_paths),
            "--constitutional-shard-count",
            str(shard_count),
            "--output",
            summary_path.as_posix(),
            "--json",
        )
    if suite == "pytest-execution":
        return (
            py,
            script,
            "--aggregate-pytest-execution-shard-reports",
            *(path.as_posix() for path in report_paths),
            "--pytest-shard-count",
            str(shard_count),
            "--output",
            summary_path.as_posix(),
            "--json",
        )
    raise ValueError(f"unsupported shard suite: {suite}")


def _verify_command_parts(suite: str, *, py: str, summary_path: Path, verification_path: Path) -> tuple[str, ...]:
    script = "scripts/certification_stability.py"
    if suite == "collection":
        return (
            py,
            script,
            "--verify-collection-summary",
            summary_path.as_posix(),
            "--output",
            verification_path.as_posix(),
            "--json",
        )
    if suite == "constitutional":
        return (
            py,
            script,
            "--verify-constitutional-summary",
            summary_path.as_posix(),
            "--output",
            verification_path.as_posix(),
            "--json",
        )
    if suite == "pytest-execution":
        return (
            py,
            script,
            "--verify-pytest-execution-summary",
            summary_path.as_posix(),
            "--output",
            verification_path.as_posix(),
            "--json",
        )
    raise ValueError(f"unsupported shard suite: {suite}")


def _local_certify_command_parts(suite: str, *, py: str, shard_count: int) -> tuple[str, ...]:
    script = "scripts/local_certify.py"
    if suite == "collection":
        return (py, script, "--skip-frontend", "--include-collection-shards", "--collection-shard-count", str(shard_count), "--json")
    if suite == "constitutional":
        return (py, script, "--skip-frontend", "--include-constitutional-shards", "--constitutional-shard-count", str(shard_count), "--json")
    if suite == "pytest-execution":
        return (py, script, "--skip-frontend", "--include-pytest-shards", "--pytest-shard-count", str(shard_count), "--json")
    raise ValueError(f"unsupported shard suite: {suite}")


def _source_tree_for_shard_suite(suite: str) -> dict[str, object]:
    if suite == "collection":
        return {
            "scope": "tests/**/*.py collection inputs",
            "file_count": len(_collection_source_manifest()),
            "manifest_sha256": _collection_source_manifest_digest(),
        }
    if suite == "constitutional":
        return {
            "scope": "tests/constitutional/test_*.py",
            "file_count": len(_constitutional_source_manifest()),
            "manifest_sha256": _constitutional_source_manifest_digest(),
        }
    if suite == "pytest-execution":
        return {
            "scope": "tests/**/*.py execution inputs",
            "file_count": len(_pytest_execution_source_manifest()),
            "manifest_sha256": _pytest_execution_source_manifest_digest(),
        }
    raise ValueError(f"unsupported shard suite: {suite}")


def _build_shard_suite_manifest(
    *,
    suites: Sequence[str],
    py: str,
    output_root: Path,
    collection_shard_count: int,
    constitutional_shard_count: int,
    pytest_shard_count: int,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> dict[str, object]:
    normalized_suites: tuple[str, ...] = tuple(SHARD_SUITE_NAMES if "all" in suites else suites)
    suite_payloads: list[dict[str, object]] = []
    for suite in normalized_suites:
        if suite not in SHARD_SUITE_NAMES:
            raise ValueError(f"unsupported shard suite: {suite}")
        shard_count = {
            "collection": collection_shard_count,
            "constitutional": constitutional_shard_count,
            "pytest-execution": pytest_shard_count,
        }[suite]
        if shard_count <= 0:
            raise ValueError(f"{suite} shard count must be positive")
        paths = _shard_suite_paths(suite, output_root=output_root)
        report_dir = paths["report_dir"]
        report_paths = tuple(report_dir / f"shard_{index}.json" for index in range(1, shard_count + 1))
        summary_path = paths["summary"]
        verification_path = paths["verification"]
        shard_reports = [
            {
                "shard_index": index,
                "shard_count": shard_count,
                "output_path": report_path.as_posix(),
                "command": list(
                    _shard_suite_command_parts(
                        suite,
                        py=py,
                        shard_count=shard_count,
                        shard_index=index,
                        timeout_seconds=timeout_seconds,
                        heartbeat_seconds=heartbeat_seconds,
                        report_path=report_path,
                    )
                ),
            }
            for index, report_path in enumerate(report_paths, start=1)
        ]
        suite_payloads.append(
            {
                "suite": suite,
                "shard_count": shard_count,
                "timeout_seconds": timeout_seconds,
                "heartbeat_seconds": heartbeat_seconds,
                "source_tree": _source_tree_for_shard_suite(suite),
                "shard_reports": shard_reports,
                "aggregate": {
                    "output_path": summary_path.as_posix(),
                    "command": list(_aggregate_command_parts(suite, py=py, shard_count=shard_count, report_paths=report_paths, summary_path=summary_path)),
                },
                "verify": {
                    "output_path": verification_path.as_posix(),
                    "command": list(_verify_command_parts(suite, py=py, summary_path=summary_path, verification_path=verification_path)),
                },
                "local_certify": {
                    "command": list(_local_certify_command_parts(suite, py=py, shard_count=shard_count)),
                },
            }
        )
    return {
        "schema_version": "certification_stability_shard_suite_manifest/v1",
        "status": "PASS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_root": output_root.as_posix(),
        "suites": suite_payloads,
    }


def _verify_shard_suite_manifest(path: str | Path, *, output_path: str | Path | None = None) -> dict[str, object]:
    manifest_path = _normalise_report_path(path)
    blockers: list[str] = []
    try:
        payload = _load_json_report(manifest_path)
    except ValueError as exc:
        payload = {}
        blockers.append(f"SHARD_SUITE_MANIFEST_INVALID_JSON:{exc}")
    if payload.get("schema_version") != "certification_stability_shard_suite_manifest/v1":
        blockers.append(f"SHARD_SUITE_MANIFEST_SCHEMA_INVALID:{payload.get('schema_version')}")
    suites = payload.get("suites")
    if not isinstance(suites, list):
        blockers.append("SHARD_SUITE_MANIFEST_SUITES_NOT_LIST")
        suites = []
    seen_suites: set[str] = set()
    for suite_payload in suites:
        if not isinstance(suite_payload, dict):
            blockers.append("SHARD_SUITE_MANIFEST_SUITE_INVALID")
            continue
        suite = suite_payload.get("suite")
        if suite not in SHARD_SUITE_NAMES:
            blockers.append(f"SHARD_SUITE_MANIFEST_SUITE_UNKNOWN:{suite}")
            continue
        if str(suite) in seen_suites:
            blockers.append(f"SHARD_SUITE_MANIFEST_SUITE_DUPLICATE:{suite}")
        seen_suites.add(str(suite))
        shard_count = suite_payload.get("shard_count")
        if not isinstance(shard_count, int) or shard_count <= 0:
            blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_COUNT_INVALID:{suite}:{shard_count}")
            continue
        source_tree = suite_payload.get("source_tree")
        expected_source_tree = _source_tree_for_shard_suite(str(suite))
        if not isinstance(source_tree, dict):
            blockers.append(f"SHARD_SUITE_MANIFEST_SOURCE_TREE_INVALID:{suite}")
        elif source_tree.get("manifest_sha256") != expected_source_tree.get("manifest_sha256"):
            blockers.append(
                f"SHARD_SUITE_MANIFEST_SOURCE_TREE_STALE:{suite}:{source_tree.get('manifest_sha256')}:expected={expected_source_tree.get('manifest_sha256')}"
            )
        shard_reports = suite_payload.get("shard_reports")
        if not isinstance(shard_reports, list):
            blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_REPORTS_NOT_LIST:{suite}")
            shard_reports = []
        if len(shard_reports) != shard_count:
            blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_REPORT_COUNT_MISMATCH:{suite}:{len(shard_reports)}:expected={shard_count}")
        seen_indexes: set[int] = set()
        for report in shard_reports:
            if not isinstance(report, dict):
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_REPORT_INVALID:{suite}")
                continue
            index = report.get("shard_index")
            if not isinstance(index, int):
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_INDEX_INVALID:{suite}:{index}")
                continue
            seen_indexes.add(index)
            if report.get("shard_count") != shard_count:
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_COUNT_MISMATCH:{suite}:{index}:{report.get('shard_count')}:expected={shard_count}")
            output_value = report.get("output_path")
            if not isinstance(output_value, str) or not output_value.endswith(f"shard_{index}.json"):
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_OUTPUT_INVALID:{suite}:{index}:{output_value}")
            command = report.get("command")
            command_text = " ".join(str(part) for part in command) if isinstance(command, list) else ""
            if "scripts/certification_stability.py" not in command_text:
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_COMMAND_MISSING_DRIVER:{suite}:{index}")
            expected_flag = {
                "collection": "--collection-shard-index",
                "constitutional": "--constitutional-shard-index",
                "pytest-execution": "--pytest-shard-index",
            }[str(suite)]
            if expected_flag not in command_text or str(index) not in command_text:
                blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_COMMAND_INDEX_MISMATCH:{suite}:{index}")
        expected_indexes = set(range(1, shard_count + 1))
        if seen_indexes != expected_indexes:
            blockers.append(f"SHARD_SUITE_MANIFEST_SHARD_INDEX_COVERAGE_MISMATCH:{suite}:{sorted(seen_indexes)}:expected={sorted(expected_indexes)}")
        for command_section, required in (
            ("aggregate", "--aggregate-"),
            ("verify", "--verify-"),
            ("local_certify", "scripts/local_certify.py"),
        ):
            section = suite_payload.get(command_section)
            command = section.get("command") if isinstance(section, dict) else None
            command_text = " ".join(str(part) for part in command) if isinstance(command, list) else ""
            if required not in command_text:
                blockers.append(f"SHARD_SUITE_MANIFEST_{command_section.upper()}_COMMAND_INVALID:{suite}")
    output = _normalise_report_path(output_path) if output_path is not None else manifest_path.with_name(manifest_path.stem + "_verification.json")
    verification = {
        "schema_version": "certification_stability_shard_suite_manifest_verification/v1",
        "status": "PASS" if not blockers else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "manifest_path": str(manifest_path),
        "output_path": str(output),
        "suite_count": len(suites),
        "blockers": blockers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification


def _select_plans(args: argparse.Namespace, py: str) -> list[StabilityPlan]:
    selected = set(args.phase)
    plans: list[StabilityPlan] = []
    if "all" in selected or "python-core" in selected:
        plans.append(_python_core_plan(py))
    if "all" in selected or "collect" in selected:
        plans.append(_pytest_collect_plan(py))
    if "all" in selected or "collect-shards" in selected:
        plans.append(_collection_shard_plan(py, shard_count=args.collection_shard_count, shard_index=args.collection_shard_index))
    if "all" in selected or "constitutional-shards" in selected:
        plans.append(_constitutional_shard_plan(py, shard_count=args.constitutional_shard_count, shard_index=args.constitutional_shard_index))
    if "all" in selected or "pytest-shards" in selected:
        plans.append(_pytest_shard_plan(py))
    if "all" in selected or "pytest-execution-shards" in selected:
        plans.append(_pytest_execution_shard_plan(py, shard_count=args.pytest_shard_count, shard_index=args.pytest_shard_index))
    if "all" in selected or "researcher-fixture" in selected:
        artifact_root = Path(args.researcher_artifact_root)
        _copy_fixture(artifact_root)
        plans.append(_researcher_fixture_plan(py, artifact_root))
    if "all" in selected or "frontend" in selected:
        plans.append(_frontend_plan(include_install=not args.skip_frontend_install))
    return plans


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        action="append",
        choices=[
            "all",
            "python-core",
            "collect",
            "collect-shards",
            "constitutional-shards",
            "pytest-shards",
            "pytest-execution-shards",
            "researcher-fixture",
            "frontend",
        ],
        default=[],
        help="Phase to run. May be passed multiple times. Defaults to python-core + researcher-fixture.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900, help="Per-step watchdog timeout.")
    parser.add_argument("--heartbeat-seconds", type=int, default=10, help="Progress heartbeat interval while a step is running; set 0 to disable.")
    parser.add_argument(
        "--collection-shard-count",
        type=int,
        default=DEFAULT_COLLECTION_SHARD_COUNT,
        help="Number of bounded shards to use for the collect-shards phase.",
    )
    parser.add_argument(
        "--collection-shard-index",
        type=int,
        default=None,
        help=(
            "Optional 1-based collection shard index to run. "
            "Use this to prove full pytest collection through bounded, resumable invocations."
        ),
    )
    parser.add_argument(
        "--constitutional-shard-count",
        type=int,
        default=DEFAULT_CONSTITUTIONAL_SHARD_COUNT,
        help="Number of bounded shards to use for the constitutional-shards phase.",
    )
    parser.add_argument(
        "--constitutional-shard-index",
        type=int,
        default=None,
        help=(
            "Optional 1-based constitutional shard index to run. "
            "Use this to prove the constitutional suite through multiple bounded, resumable invocations."
        ),
    )
    parser.add_argument(
        "--pytest-shard-count",
        type=int,
        default=DEFAULT_PYTEST_EXECUTION_SHARD_COUNT,
        help="Number of bounded shards to use for the pytest-execution-shards phase.",
    )
    parser.add_argument(
        "--pytest-shard-index",
        type=int,
        default=None,
        help="Optional 1-based backend pytest execution shard index to run.",
    )
    parser.add_argument("--no-fail-fast", action="store_true", help="Continue after a failed/timed-out phase.")
    parser.add_argument(
        "--aggregate-constitutional-shard-reports",
        nargs="+",
        metavar="REPORT",
        help="Aggregate previously written constitutional shard JSON reports into one summary artifact and exit.",
    )
    parser.add_argument(
        "--verify-constitutional-summary",
        metavar="SUMMARY",
        help="Verify a previously aggregated constitutional shard summary artifact and exit.",
    )
    parser.add_argument(
        "--aggregate-collection-shard-reports",
        nargs="+",
        metavar="REPORT",
        help="Aggregate previously written collection shard JSON reports into one summary artifact and exit.",
    )
    parser.add_argument(
        "--verify-collection-summary",
        metavar="SUMMARY",
        help="Verify a previously aggregated collection shard summary artifact and exit.",
    )
    parser.add_argument(
        "--aggregate-pytest-execution-shard-reports",
        nargs="+",
        metavar="REPORT",
        help="Aggregate previously written backend pytest execution shard JSON reports into one summary artifact and exit.",
    )
    parser.add_argument(
        "--verify-pytest-execution-summary",
        metavar="SUMMARY",
        help="Verify a previously aggregated backend pytest execution shard summary artifact and exit.",
    )
    parser.add_argument(
        "--write-shard-suite-manifest",
        nargs="+",
        choices=["all", "collection", "constitutional", "pytest-execution"],
        help=(
            "Write a machine-readable runbook of per-shard, aggregate, verify, and local-certify commands "
            "for the requested shard proof suite(s), then exit."
        ),
    )
    parser.add_argument(
        "--verify-shard-suite-manifest",
        metavar="MANIFEST",
        help="Verify a previously written shard-suite manifest and exit.",
    )
    parser.add_argument(
        "--shard-suite-output-root",
        default=(REPO_ROOT / "artifacts" / "certification_stability").as_posix(),
        help="Artifact root used inside generated shard-suite manifest commands.",
    )
    parser.add_argument("--skip-frontend-install", action="store_true", help="Skip npm ci when frontend phase is selected.")
    parser.add_argument("--researcher-artifact-root", default="/tmp/strategy-validator-researcher-fixture-certification")
    parser.add_argument("--output", default=DEFAULT_OUTPUT.as_posix(), help="Where to persist the JSON report.")
    parser.add_argument("--json", action="store_true", help="Print the report JSON to stdout.")
    args = parser.parse_args(argv)

    if args.write_shard_suite_manifest:
        manifest_output = Path(args.output)
        payload = _build_shard_suite_manifest(
            suites=args.write_shard_suite_manifest,
            py=sys.executable,
            output_root=Path(args.shard_suite_output_root),
            collection_shard_count=args.collection_shard_count,
            constitutional_shard_count=args.constitutional_shard_count,
            pytest_shard_count=args.pytest_shard_count,
            timeout_seconds=args.timeout_seconds,
            heartbeat_seconds=args.heartbeat_seconds,
        )
        payload["output_path"] = manifest_output.as_posix()
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"shard_suite_manifest: {manifest_output}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.verify_shard_suite_manifest:
        payload = _verify_shard_suite_manifest(args.verify_shard_suite_manifest, output_path=args.output)
        print(f"shard_suite_manifest_verification: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.aggregate_constitutional_shard_reports:
        payload = _aggregate_constitutional_shard_reports(
            args.aggregate_constitutional_shard_reports,
            expected_shard_count=args.constitutional_shard_count,
            output_path=args.output,
        )
        print(f"constitutional_shards_summary: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.verify_constitutional_summary:
        payload = _verify_constitutional_summary_report(
            args.verify_constitutional_summary,
            output_path=args.output,
        )
        print(f"constitutional_shards_summary_verification: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.aggregate_collection_shard_reports:
        payload = _aggregate_collection_shard_reports(
            args.aggregate_collection_shard_reports,
            expected_shard_count=args.collection_shard_count,
            output_path=args.output,
        )
        print(f"collection_shards_summary: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.verify_collection_summary:
        payload = _verify_collection_summary_report(
            args.verify_collection_summary,
            output_path=args.output,
        )
        print(f"collection_shards_summary_verification: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.aggregate_pytest_execution_shard_reports:
        payload = _aggregate_pytest_execution_shard_reports(
            args.aggregate_pytest_execution_shard_reports,
            expected_shard_count=args.pytest_shard_count,
            output_path=args.output,
        )
        print(f"pytest_execution_shards_summary: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if args.verify_pytest_execution_summary:
        payload = _verify_pytest_execution_summary_report(
            args.verify_pytest_execution_summary,
            output_path=args.output,
        )
        print(f"pytest_execution_shards_summary_verification: {payload['output_path']}")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "PASS" else 1

    if not args.phase:
        args.phase = ["python-core", "researcher-fixture"]
    py = sys.executable
    plans = _select_plans(args, py)
    steps: list[StabilityStep] = []
    failed_step: StabilityStep | None = None

    for plan in plans:
        print(f"\n=== certification-stability: {plan.name} ===", flush=True)
        for name, command, cwd in plan.steps:
            print("+ " + " ".join(command), flush=True)
            step = _run_step(name, command, cwd, timeout_seconds=args.timeout_seconds, heartbeat_seconds=args.heartbeat_seconds)
            steps.append(step)
            print(
                f"{name}: exit={step.exit_code} timed_out={step.timed_out} duration={step.duration_seconds}s",
                flush=True,
            )
            if (step.timed_out or step.exit_code not in (0, None)) and failed_step is None:
                failed_step = step
                if not args.no_fail_fast:
                    break
        if failed_step is not None and not args.no_fail_fast:
            break

    output = Path(args.output)
    payload = {
        "schema_version": "certification_stability/v2",
        "status": "PASS" if failed_step is None else "FAIL",
        "failed_step": None if failed_step is None else failed_step.name,
        "timeout_seconds": args.timeout_seconds,
        "heartbeat_seconds": args.heartbeat_seconds,
        "collection_shard_count": args.collection_shard_count,
        "collection_shard_index": args.collection_shard_index,
        "pytest_shard_count": args.pytest_shard_count,
        "pytest_shard_index": args.pytest_shard_index,
        "researcher_artifact_root": args.researcher_artifact_root,
        "pytest_execution_source_tree": {
            "file_count": len(_pytest_execution_source_manifest()),
            "manifest_sha256": _pytest_execution_source_manifest_digest(),
        },
        "collection_source_tree": {
            "file_count": len(_collection_source_manifest()),
            "manifest_sha256": _collection_source_manifest_digest(),
        },
        "constitutional_shard_count": args.constitutional_shard_count,
        "constitutional_shard_index": args.constitutional_shard_index,
        "constitutional_source_tree": {
            "file_count": len(_constitutional_source_manifest()),
            "manifest_sha256": _constitutional_source_manifest_digest(),
        },
        "phases": [plan.name for plan in plans],
        "python_version": platform.python_version(),
        "node_version": _node_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output),
        "steps": [step.to_payload() for step in steps],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"certification_stability_report: {output}")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    if failed_step is not None:
        return failed_step.exit_code or 124
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
