#!/usr/bin/env python
"""Run the local certification gates that mirror CI validate.

This command is intentionally boring: it prints a phase label, runs the exact
subprocess, records a machine-readable report, and exits on the first failing
gate unless --no-fail-fast is used. It does not install Python dependencies;
run it from an environment where ``python -m pip install -e '.[dev]'`` has
already succeeded.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from functools import lru_cache
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, TextIO

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPO_ROOT / "ui" / "strategist-web"


@lru_cache(maxsize=1)
def _npm_executable() -> str:
    """Resolve npm for subprocess.

    On Windows, ``CreateProcess`` cannot always launch the bare ``npm`` token when
    npm is implemented as a ``.cmd`` shim and the active interpreter's environment
    does not expose it the same way as an interactive shell.
    """
    resolved = shutil.which("npm") or shutil.which("npm.cmd")
    return resolved if resolved else "npm"


def _npm_public_registry_env() -> dict[str, str]:
    """Pin npm's registry for frontend subprocesses.

    Inherited ``NPM_CONFIG_*`` values (for example a corporate mirror) can
    redirect fetches away from the ``resolved`` URLs in ``package-lock.json``,
    which breaks installs when that host is unreachable.
    """
    return {"NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/"}


REPORT_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "local_certify_report.json"
LOCAL_CERTIFY_REPORT_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "local_certify_report_verification.json"
RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_closure_report.json"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_evidence_bundle.json"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_evidence_bundle_seal.json"
RESEARCH_PAPER_DISCOVERY_CLOSURE_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_closure_report_verification.json"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_evidence_bundle_verification.json"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_evidence_bundle_export_verification.json"
RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_profile_plan.json"
RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_profile_plan_verification.json"
RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_phase_run_report.json"
RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_phase_run_report_verification.json"
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_PATH = REPO_ROOT / "docs" / "audits" / "final_research_paper_discovery_certification.md"
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "final_research_paper_discovery_certification_index.json"
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_VERIFICATION_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "final_research_paper_discovery_certification_verification.json"
PYTHON_CORE_REPORT_PATH = REPO_ROOT / "artifacts" / "local_certify" / "latest" / "python_core_report.json"
FRONTEND_CERTIFY_REPORT_PATH = REPO_ROOT / "artifacts" / "frontend_certify" / "latest" / "frontend_certify_report.json"
FRONTEND_CLEAN_WORKSPACE_REPORT_PATH = REPO_ROOT / "artifacts" / "frontend_certify" / "latest" / "frontend_clean_workspace_report.json"
FRONTEND_PREFLIGHT_REPORT_PATH = REPO_ROOT / "artifacts" / "frontend_certify" / "latest" / "frontend_preflight_report.json"
PUBLIC_SURFACE_DASHBOARD_REPORT_PATH = REPO_ROOT / "artifacts" / "public_surface_dashboard" / "latest" / "public_surface_dashboard.json"
PUBLIC_SURFACE_RATCHET_PATH = REPO_ROOT / "docs" / "governance" / "public_surface_budget_ratchet.json"
PACKAGE_REPO_CHECK_REPORT_PATH = REPO_ROOT / "artifacts" / "package_repo" / "latest" / "package_repo_check.json"
RESEARCHER_FIXTURE_ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "researcher_fixture" / "latest" / "fixture"
RESEARCHER_FIXTURE_REPORT_PATH = REPO_ROOT / "artifacts" / "researcher_fixture" / "latest" / "researcher_fixture_report.json"
CERTIFICATION_STABILITY_DIR = REPO_ROOT / "artifacts" / "certification_stability" / "latest"
COLLECTION_SHARDS_SUMMARY_PATH = CERTIFICATION_STABILITY_DIR / "collection_shards_summary.json"
COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH = CERTIFICATION_STABILITY_DIR / "collection_shards_summary_verification.json"
CONSTITUTIONAL_SHARDS_SUMMARY_PATH = CERTIFICATION_STABILITY_DIR / "constitutional_shards_summary.json"
CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH = CERTIFICATION_STABILITY_DIR / "constitutional_shards_summary_verification.json"
PYTEST_EXECUTION_SHARDS_SUMMARY_PATH = CERTIFICATION_STABILITY_DIR / "pytest_execution_shards_summary.json"
PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH = CERTIFICATION_STABILITY_DIR / "pytest_execution_shards_summary_verification.json"
TAIL_CHARS = 12_000
LOCAL_CERTIFY_SCHEMA_VERSION = "local_certify/v5"
LOCAL_CERTIFY_VERIFICATION_SCHEMA_VERSION = "local_certify_report_verification/v1"
RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION = "research_paper_discovery_closure/v1"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SCHEMA_VERSION = "research_paper_discovery_evidence_bundle/v1"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_VERSION = "research_paper_discovery_evidence_bundle_seal/v1"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_SCHEMA_VERSION = "research_paper_discovery_evidence_bundle_seal_subject/v1"
RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_VERSION = "research_paper_discovery_evidence_bundle_provenance/v1"
RESEARCH_PAPER_DISCOVERY_PROFILE = "RESEARCH_AND_PAPER_DISCOVERY"
RESEARCH_PAPER_DISCOVERY_PROFILE_VERSION = "research_paper_discovery_certification/v1"
RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_VERSION = "research_paper_discovery_profile_plan/v1"
RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_SCHEMA_VERSION = "research_paper_discovery_profile_plan_verification/v1"
RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_SCHEMA_VERSION = "research_paper_discovery_phase_run/v1"
RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_SCHEMA_VERSION = "research_paper_discovery_phase_run_verification/v1"
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_SCHEMA_VERSION = "final_research_paper_discovery_certification_index/v1"
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_VERIFICATION_SCHEMA_VERSION = "final_research_paper_discovery_certification_verification/v1"
RESEARCH_PAPER_DISCOVERY_REQUIRED_PROOFS = (
    "frontend_clean_workspace_report",
    "frontend_certify_report",
    "python_core_report",
    "public_surface_dashboard",
    "package_repo_check",
    "researcher_fixture_report",
    "collection_shards_proof",
    "constitutional_shards_proof",
    "pytest_execution_shards_proof",
)
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS = (
    "python scripts/local_certify.py --certify-research-paper-discovery --json",
    "python scripts/local_certify.py --verify-report artifacts/local_certify/latest/local_certify_report.json --json",
    "python scripts/local_certify.py --verify-phase-profile-plan artifacts/local_certify/latest/research_paper_discovery_profile_plan.json --json",
    "python scripts/local_certify.py --verify-phase-run-report artifacts/local_certify/latest/research_paper_discovery_phase_run_report.json --json",
    "python scripts/local_certify.py --verify-phase-closure-report artifacts/local_certify/latest/research_paper_discovery_closure_report.json --json",
    "python scripts/local_certify.py --verify-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json --json",
    "python scripts/local_certify.py --export-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle.json --phase-evidence-bundle-export-dir artifacts/local_certify/latest/research_paper_discovery_evidence_bundle_export --json",
    "python scripts/local_certify.py --verify-phase-evidence-bundle artifacts/local_certify/latest/research_paper_discovery_evidence_bundle_export/research_paper_discovery_evidence_bundle.json --json",
    "python scripts/local_certify.py --verify-final-phase-certificate docs/audits/final_research_paper_discovery_certification.md --json",
)
FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_PHRASES = (
    "not autonomous live trading",
    "no-live-authority confirmation",
    "paper/live firewall confirmation",
    "PAPER_EVIDENCE_PASSED is not LIVE_READY",
)
LOCAL_CERTIFY_BASE_REQUIRED_STEPS = (
    "compileall",
    "source_health",
    "repository_truth",
    "migration_truth",
    "public_surface_dashboard",
    "public_surface_dashboard_report_validation",
    "package_repo_check",
    "package_repo_check_report_validation",
    "pytest",
    "python_core_report_validation",
)
FRONTEND_CERTIFY_REQUIRED_STEPS = (
    "contract_check",
    "lint",
    "typecheck",
    "test",
    "acceptance",
    "build",
    "audit",
)
RESEARCHER_FIXTURE_REQUIRED_STEPS = (
    "researcher_cycle_fixture",
    "researcher_certify_fixture",
)
DEFAULT_LOCAL_CERTIFY_TIMEOUT_SECONDS = 900
LOCAL_CERTIFY_STEP_TIMEOUTS = {
    "compileall": 120,
    "source_health": 180,
    "repository_truth": 180,
    "migration_truth": 180,
    "public_surface_dashboard": 180,
    "package_repo_check": 180,
    "pytest": 900,
    "frontend_clean_workspace": 180,
    "frontend_npm_ci": 300,
    "frontend_certify": 900,
    "researcher_fixture": 900,
}
TIMEOUT_EXIT_CODE = 124


@dataclass(frozen=True)
class LocalCertifyStep:
    name: str
    command: tuple[str, ...]
    cwd: str
    exit_code: int
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str
    artifact_paths: tuple[str, ...] = ()
    timeout_seconds: int | None = None
    started_at: str | None = None
    ended_at: str | None = None
    timed_out: bool = False

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _tail(value: str, *, limit: int = TAIL_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _relative_cwd(cwd: Path) -> str:
    return str(cwd.relative_to(REPO_ROOT) if cwd != REPO_ROOT else Path("."))


def _repo_relative_or_absolute_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _is_safe_relative_artifact_reference(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in candidate.parts)


def _referenced_artifact_path(
    value: object,
    *,
    base_dir: Path | None = None,
    portable: bool = False,
) -> Path | None:
    """Resolve an artifact reference from repo-root or bundle/report-local context.

    Legacy reports store absolute paths or paths relative to the repository root.
    Exported proof bundles intentionally store paths relative to the exported
    manifest directory. For portable bundles, never fall back to the working
    tree and never accept absolute/path-traversing references.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    if portable:
        if base_dir is None or not _is_safe_relative_artifact_reference(value):
            return None
        resolved_base = base_dir.resolve()
        resolved = (base_dir / candidate).resolve()
        try:
            resolved.relative_to(resolved_base)
        except ValueError:
            return None
        return resolved
    if candidate.is_absolute():
        return candidate
    if base_dir is not None:
        local_candidate = base_dir / candidate
        if local_candidate.exists():
            return local_candidate
    repo_candidate = REPO_ROOT / candidate
    if repo_candidate.exists():
        return repo_candidate
    return (base_dir / candidate) if base_dir is not None else repo_candidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cleanup_process_group(pgid: int) -> None:
    if os.name == "nt":  # pragma: no cover - Windows-specific process handling
        return
    try:
        os.killpg(pgid, 0)
    except (ProcessLookupError, PermissionError):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    time.sleep(0.2)
    try:
        os.killpg(pgid, 0)
    except (ProcessLookupError, PermissionError):
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        return


def _terminate_process(proc: subprocess.Popen[str]) -> None:
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


def _configure_stdio_for_unicode() -> None:
    """Prefer UTF-8 stdio so Vitest/Next output (for example U+2713) does not crash Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                pass


def _print_console(text: str, *, file: TextIO) -> None:
    """Print subprocess-captured text; fall back if the console encoding cannot represent a code point."""
    if not text:
        return
    try:
        print(text, end="", file=file, flush=True)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "ascii"
        safe = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(safe, end="", file=file, flush=True)


def _timeout_for_step(name: str, override_seconds: int | None = None) -> int:
    if override_seconds is not None:
        if override_seconds <= 0:
            raise ValueError("timeout override must be positive")
        return override_seconds
    return LOCAL_CERTIFY_STEP_TIMEOUTS.get(name, DEFAULT_LOCAL_CERTIFY_TIMEOUT_SECONDS)


def _run(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    heartbeat_seconds: int = 10,
) -> LocalCertifyStep:
    print(f"\n=== local-certify: {name} ===", flush=True)
    print("+ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO_ROOT))
    if extra_env:
        env.update(extra_env)
    effective_timeout = _timeout_for_step(name, timeout_seconds)
    started_perf = time.perf_counter()
    started_at = _utc_now()
    creationflags = 0
    start_new_session = os.name != "nt"
    if os.name == "nt":  # pragma: no cover - Windows-specific process handling
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    timed_out = False
    exit_code = 0
    stdout = ""
    stderr = ""
    with tempfile.TemporaryDirectory(prefix="strategy_validator_local_certify_") as tmp_dir:
        stdout_path = Path(tmp_dir) / "stdout.txt"
        stderr_path = Path(tmp_dir) / "stderr.txt"
        with stdout_path.open("w+", encoding="utf-8", errors="replace") as stdout_file, stderr_path.open(
            "w+", encoding="utf-8", errors="replace"
        ) as stderr_file:
            proc = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                encoding="utf-8",
                errors="replace",
                close_fds=True,
                start_new_session=start_new_session,
                creationflags=creationflags,
            )
            last_progress = started_perf
            while proc.poll() is None:
                now = time.perf_counter()
                if now - started_perf >= effective_timeout:
                    timed_out = True
                    _terminate_process(proc)
                    break
                if heartbeat_seconds > 0 and now - last_progress >= heartbeat_seconds:
                    print(f"... {name} still running after {round(now - started_perf, 1)}s", flush=True)
                    last_progress = now
                time.sleep(0.25)
            if not timed_out:
                _cleanup_process_group(proc.pid)
            stdout_file.flush()
            stderr_file.flush()
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read()
            stderr = stderr_file.read()
            exit_code = TIMEOUT_EXIT_CODE if timed_out else int(proc.returncode or 0)
    duration = time.perf_counter() - started_perf
    ended_at = _utc_now()
    if stdout:
        _print_console(stdout, file=sys.stdout)
    if stderr:
        _print_console(stderr, file=sys.stderr)
    if timed_out:
        print(f"local_certify watchdog timed out step {name} after {effective_timeout}s", file=sys.stderr)
    return LocalCertifyStep(
        name=name,
        command=tuple(command),
        cwd=_relative_cwd(cwd),
        exit_code=exit_code,
        duration_seconds=round(duration, 3),
        stdout_tail=_tail(stdout or ""),
        stderr_tail=_tail(stderr or ""),
        timeout_seconds=effective_timeout,
        started_at=started_at,
        ended_at=ended_at,
        timed_out=timed_out,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _source_manifest_digest(paths: Sequence[Path]) -> str:
    manifest: list[dict[str, str]] = []
    unique = {item for item in paths if item.exists() and item.is_file()}

    def _repo_relative_sort_key(path: Path) -> tuple[str, ...]:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).parts
        return (path.as_posix(),)

    for path in sorted(unique, key=_repo_relative_sort_key):
        if path.is_relative_to(REPO_ROOT):
            rel_display = path.relative_to(REPO_ROOT).as_posix()
        else:
            rel_display = path.as_posix()
        manifest.append(
            {
                "path": rel_display,
                "sha256": _file_sha256(path),
            }
        )
    return _canonical_json_digest(manifest)


@lru_cache(maxsize=1)
def _python_core_source_tree_digest() -> str:
    paths = [
        *REPO_ROOT.joinpath("strategy_validator").rglob("*.py"),
        *REPO_ROOT.joinpath("tests").rglob("*.py"),
        *REPO_ROOT.joinpath("scripts").glob("*.py"),
        REPO_ROOT / "pyproject.toml",
    ]
    return _source_manifest_digest([path for path in paths if path.exists() and path.is_file()])


def _python_core_required_step_names() -> tuple[str, ...]:
    return tuple(name for name in LOCAL_CERTIFY_BASE_REQUIRED_STEPS if name != "python_core_report_validation")


def _write_python_core_report(
    *,
    results: Sequence[LocalCertifyStep],
    failed: LocalCertifyStep | None,
    report_path: Path = PYTHON_CORE_REPORT_PATH,
) -> dict[str, object]:
    required = _python_core_required_step_names()
    order = {name: index for index, name in enumerate(required)}
    selected = sorted((step for step in results if step.name in required), key=lambda step: order.get(step.name, len(order)))
    selected_payloads = [step.to_payload() for step in selected]
    step_names = [step.name for step in selected]
    missing = [name for name in required if name not in step_names]
    duplicates = sorted({name for name in step_names if step_names.count(name) > 1})
    nonzero = [
        f"{step.name}:{'TIMEOUT' if step.timed_out else step.exit_code}"
        for step in selected
        if step.timed_out or step.exit_code != 0
    ]
    blockers: list[str] = []
    if missing:
        blockers.append("PYTHON_CORE_REQUIRED_STEPS_MISSING:" + ",".join(missing))
    if duplicates:
        blockers.append("PYTHON_CORE_DUPLICATE_STEPS:" + ",".join(duplicates))
    if nonzero:
        blockers.append("PYTHON_CORE_NONZERO_STEPS:" + ",".join(nonzero))
    timed_out = any(step.timed_out for step in selected)
    status = "PASS" if not blockers else "TIMEOUT" if timed_out else "FAIL"
    payload: dict[str, object] = {
        "schema_version": "python_core_report/v1",
        "proof_name": "python_core_report",
        "status": status,
        "blockers": blockers,
        "failed_step": None if failed is None else failed.name,
        "repo_root": str(REPO_ROOT),
        "path": str(report_path),
        "required_step_names": list(required),
        "step_names": step_names,
        "missing_step_names": missing,
        "duplicate_step_names": duplicates,
        "nonzero_steps": nonzero,
        "step_count": len(selected_payloads),
        "steps": selected_payloads,
        "step_manifest_sha256": _step_manifest_digest(selected_payloads),
        "source_tree_digest": _python_core_source_tree_digest(),
        "created_at": _utc_now(),
    }
    payload["report_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "report_payload_sha256"})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_python_core_report(
    report_path: Path = PYTHON_CORE_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    payload, load_blockers = _load_json_object(report_path, blocker_prefix="PYTHON_CORE_REPORT")
    blockers.extend(load_blockers)
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != "python_core_report/v1":
        blockers.append(f"PYTHON_CORE_REPORT_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("proof_name") != "python_core_report":
        blockers.append(f"PYTHON_CORE_REPORT_PROOF_NAME_UNEXPECTED:{payload.get('proof_name')}")
    if payload.get("status") != "PASS":
        blockers.append(f"PYTHON_CORE_REPORT_NOT_PASSING:{payload.get('status')}")
    if payload.get("repo_root") != str(REPO_ROOT):
        blockers.append(f"PYTHON_CORE_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
    if payload.get("path") != str(report_path):
        blockers.append(f"PYTHON_CORE_REPORT_PATH_MISMATCH:{payload.get('path')}:expected={report_path}")
    declared_digest = payload.get("report_payload_sha256")
    observed_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "report_payload_sha256"})
    if declared_digest != observed_digest:
        blockers.append(f"PYTHON_CORE_REPORT_PAYLOAD_DIGEST_MISMATCH:{declared_digest}:expected={observed_digest}")
    required = list(_python_core_required_step_names())
    step_names = payload.get("step_names")
    if step_names != required:
        blockers.append(f"PYTHON_CORE_REPORT_STEP_NAMES_MISMATCH:{step_names}:expected={required}")
    if payload.get("missing_step_names") not in ([], None):
        blockers.append("PYTHON_CORE_REPORT_DECLARED_MISSING_STEPS")
    if payload.get("duplicate_step_names") not in ([], None):
        blockers.append("PYTHON_CORE_REPORT_DECLARED_DUPLICATE_STEPS")
    if payload.get("nonzero_steps") not in ([], None):
        blockers.append("PYTHON_CORE_REPORT_DECLARED_NONZERO_STEPS")
    steps = payload.get("steps")
    if not isinstance(steps, list):
        blockers.append("PYTHON_CORE_REPORT_STEPS_NOT_LIST")
        steps = []
    declared_step_manifest = payload.get("step_manifest_sha256")
    observed_step_manifest = _step_manifest_digest(steps)
    if declared_step_manifest != observed_step_manifest:
        blockers.append(f"PYTHON_CORE_REPORT_STEP_MANIFEST_MISMATCH:{declared_step_manifest}:expected={observed_step_manifest}")
    expected_tree = _python_core_source_tree_digest()
    if payload.get("source_tree_digest") != expected_tree:
        blockers.append(f"PYTHON_CORE_REPORT_SOURCE_TREE_MISMATCH:{payload.get('source_tree_digest')}:expected={expected_tree}")
    summary = {
        "proof_name": "python_core_report",
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers else "FAIL",
        "source_tree_digest": payload.get("source_tree_digest"),
        "created_at": payload.get("created_at"),
        "verified_at": _utc_now(),
        "step_count": payload.get("step_count"),
        "failed_step": payload.get("failed_step"),
    }
    return summary, blockers


def _frontend_source_tree_digest() -> str | None:
    if not FRONTEND_ROOT.exists():
        return None
    paths = [
        FRONTEND_ROOT / "package.json",
        FRONTEND_ROOT / "package-lock.json",
        FRONTEND_ROOT / "scripts" / "certify.mjs",
    ]
    paths.extend((FRONTEND_ROOT / "app").rglob("*.tsx") if (FRONTEND_ROOT / "app").exists() else [])
    paths.extend((FRONTEND_ROOT / "components").rglob("*.tsx") if (FRONTEND_ROOT / "components").exists() else [])
    return _source_manifest_digest(paths)


def _collection_tests_source_tree_digest() -> str:
    return _source_manifest_digest([path for path in (REPO_ROOT / "tests").rglob("test_*.py") if path.is_file()])


def _constitutional_tests_source_tree_digest() -> str:
    return _source_manifest_digest([path for path in (REPO_ROOT / "tests" / "constitutional").glob("test_*.py") if path.is_file()])


def _researcher_fixture_source_tree_digest() -> str:
    paths = [
        REPO_ROOT / "tests" / "fixtures" / "researcher_cycle" / "full_cycle_candidate_queue.json",
        REPO_ROOT / "strategy_validator" / "cli" / "researcher_cycle.py",
        REPO_ROOT / "strategy_validator" / "cli" / "researcher_certify.py",
        REPO_ROOT / "strategy_validator" / "application" / "researcher_cycle.py",
        REPO_ROOT / "strategy_validator" / "application" / "researcher_certification.py",
        REPO_ROOT / "strategy_validator" / "application" / "researcher_certification_candidate_evidence.py",
        REPO_ROOT / "strategy_validator" / "application" / "paper_evidence_feedback.py",
        REPO_ROOT / "strategy_validator" / "application" / "phase_doctrine.py",
        REPO_ROOT / "strategy_validator" / "contracts" / "researcher_certification.py",
        REPO_ROOT / "scripts" / "certification_stability.py",
    ]
    return _source_manifest_digest(paths)


def _expected_current_digest_for_embedded_proof(field_name: str) -> str | None:
    if field_name in {"collection_shards_proof", "pytest_execution_shards_proof"}:
        return _collection_tests_source_tree_digest()
    if field_name == "constitutional_shards_proof":
        return _constitutional_tests_source_tree_digest()
    if field_name == "python_core_report":
        return _python_core_source_tree_digest()
    if field_name in {"frontend_certify_report", "frontend_clean_workspace_report"}:
        return _frontend_source_tree_digest()
    if field_name == "public_surface_dashboard":
        return _source_manifest_digest(
            [
                REPO_ROOT / "strategy_validator" / "application" / "public_surface_dashboard.py",
                REPO_ROOT / "strategy_validator" / "application" / "public_surface.py",
                REPO_ROOT / "strategy_validator" / "cli_support" / "public_surface_inventory.py",
                REPO_ROOT / "scripts" / "public_surface_dashboard.py",
                REPO_ROOT / "docs" / "audits" / "public_surface_dashboard.md",
                PUBLIC_SURFACE_RATCHET_PATH,
            ]
        )
    if field_name == "package_repo_check":
        return _source_manifest_digest(
            [
                REPO_ROOT / "scripts" / "package_repo.py",
                REPO_ROOT / "scripts" / "_path_integrity.py",
                REPO_ROOT / ".gitignore",
                REPO_ROOT / ".dockerignore",
            ]
        )
    if field_name == "researcher_fixture_report":
        return _researcher_fixture_source_tree_digest()
    return None


def local_certify_payload_digest(payload: dict[str, object]) -> str:
    seal_payload = dict(payload)
    seal_payload.pop("report_payload_sha256", None)
    return _canonical_json_digest(seal_payload)


def _step_manifest_digest(steps: Sequence[dict[str, object]]) -> str:
    manifest = [
        {
            "name": step.get("name"),
            "command": step.get("command"),
            "cwd": step.get("cwd"),
            "exit_code": step.get("exit_code"),
            "artifact_paths": step.get("artifact_paths", []),
        }
        for step in steps
        if isinstance(step, dict)
    ]
    return _canonical_json_digest(manifest)


def _expected_local_certify_step_names(payload: dict[str, object]) -> list[str]:
    expected = list(LOCAL_CERTIFY_BASE_REQUIRED_STEPS)
    if payload.get("certification_profile") == RESEARCH_PAPER_DISCOVERY_PROFILE:
        expected.insert(0, "frontend_preflight")
    if payload.get("frontend_included") is True:
        if payload.get("frontend_clean_workspace_included") is True:
            expected.extend(["frontend_clean_workspace", "frontend_clean_workspace_report_validation"])
        expected.extend(["frontend_npm_ci", "frontend_certify", "frontend_certify_report_validation"])
    if payload.get("researcher_fixture_included") is True:
        expected.extend(["researcher_fixture", "researcher_fixture_report_validation"])
    if payload.get("collection_shards_included") is True:
        shard_count = payload.get("collection_shard_count")
        if isinstance(shard_count, int) and shard_count > 0:
            expected.extend([f"collection_shard_{index:02d}_of_{shard_count:02d}" for index in range(1, shard_count + 1)])
            expected.extend(["collection_shards_summary", "collection_shards_summary_verification", "collection_shards_report_validation"])
    if payload.get("constitutional_shards_included") is True:
        shard_count = payload.get("constitutional_shard_count")
        if isinstance(shard_count, int) and shard_count > 0:
            expected.extend([f"constitutional_shard_{index:02d}_of_{shard_count:02d}" for index in range(1, shard_count + 1)])
            expected.extend(["constitutional_shards_summary", "constitutional_shards_summary_verification", "constitutional_shards_report_validation"])
    if payload.get("pytest_execution_shards_included") is True:
        shard_count = payload.get("pytest_shard_count")
        if isinstance(shard_count, int) and shard_count > 0:
            expected.extend([f"pytest_execution_shard_{index:02d}_of_{shard_count:02d}" for index in range(1, shard_count + 1)])
            expected.extend(["pytest_execution_shards_summary", "pytest_execution_shards_summary_verification", "pytest_execution_shards_report_validation"])
    return expected


def _parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)



def write_frontend_preflight_report(*, skip_frontend_requested: bool, output_path: Path = FRONTEND_PREFLIGHT_REPORT_PATH) -> dict[str, object]:
    """Write a bounded frontend prerequisite report for full phase certification.

    This is deliberately a local preflight, not a dependency installer.  It
    prevents the Research-and-Paper-Discovery profile from spending time on
    expensive backend shards when the frontend proof cannot even start.
    """
    package_json = FRONTEND_ROOT / "package.json"
    package_lock = FRONTEND_ROOT / "package-lock.json"
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    blockers: list[str] = []
    if skip_frontend_requested:
        blockers.append("FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE")
    if not FRONTEND_ROOT.exists():
        blockers.append(f"FRONTEND_PREFLIGHT_FRONTEND_ROOT_MISSING:{FRONTEND_ROOT}")
    elif not FRONTEND_ROOT.is_dir():
        blockers.append(f"FRONTEND_PREFLIGHT_FRONTEND_ROOT_NOT_DIRECTORY:{FRONTEND_ROOT}")
    if not package_json.exists():
        blockers.append(f"FRONTEND_PREFLIGHT_PACKAGE_JSON_MISSING:{package_json}")
    if not package_lock.exists():
        blockers.append(f"FRONTEND_PREFLIGHT_PACKAGE_LOCK_MISSING:{package_lock}")
    if node_path is None:
        blockers.append("FRONTEND_PREFLIGHT_NODE_MISSING")
    if npm_path is None:
        blockers.append("FRONTEND_PREFLIGHT_NPM_MISSING")

    payload: dict[str, object] = {
        "schema_version": "frontend_preflight/v1",
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "frontend_root": str(FRONTEND_ROOT),
        "frontend_root_exists": FRONTEND_ROOT.exists(),
        "frontend_root_is_dir": FRONTEND_ROOT.is_dir(),
        "package_json_path": str(package_json),
        "package_json_exists": package_json.exists(),
        "package_json_sha256": _file_sha256(package_json) if package_json.exists() else None,
        "package_lock_path": str(package_lock),
        "package_lock_exists": package_lock.exists(),
        "package_lock_sha256": _file_sha256(package_lock) if package_lock.exists() else None,
        "node_available": node_path is not None,
        "node_path": node_path,
        "node_version": _node_version(),
        "npm_available": npm_path is not None,
        "npm_path": npm_path,
        "skip_frontend_requested": skip_frontend_requested,
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "created_at": _utc_now(),
        "report_path": str(output_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_frontend_preflight_report(path: Path = FRONTEND_PREFLIGHT_REPORT_PATH) -> tuple[dict[str, object] | None, list[str]]:
    payload, blockers = _load_json_object(path, blocker_prefix="FRONTEND_PREFLIGHT_REPORT")
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != "frontend_preflight/v1":
        blockers.append(f"FRONTEND_PREFLIGHT_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    expected_root = str(FRONTEND_ROOT)
    if payload.get("frontend_root") != expected_root:
        blockers.append(f"FRONTEND_PREFLIGHT_FRONTEND_ROOT_MISMATCH:{payload.get('frontend_root')}:expected={expected_root}")
    expected_report_path = str(path)
    if payload.get("report_path") != expected_report_path:
        blockers.append(f"FRONTEND_PREFLIGHT_REPORT_PATH_MISMATCH:{payload.get('report_path')}:expected={expected_report_path}")
    if payload.get("skip_frontend_requested") is True:
        blockers.append("FRONTEND_PREFLIGHT_SKIP_FRONTEND_FORBIDDEN_FOR_PHASE")
    if payload.get("frontend_root_exists") is not True:
        blockers.append(f"FRONTEND_PREFLIGHT_FRONTEND_ROOT_MISSING:{FRONTEND_ROOT}")
    if payload.get("frontend_root_is_dir") is not True:
        blockers.append(f"FRONTEND_PREFLIGHT_FRONTEND_ROOT_NOT_DIRECTORY:{FRONTEND_ROOT}")
    if payload.get("package_json_exists") is not True:
        blockers.append(f"FRONTEND_PREFLIGHT_PACKAGE_JSON_MISSING:{FRONTEND_ROOT / 'package.json'}")
    if payload.get("package_lock_exists") is not True:
        blockers.append(f"FRONTEND_PREFLIGHT_PACKAGE_LOCK_MISSING:{FRONTEND_ROOT / 'package-lock.json'}")
    if payload.get("node_available") is not True:
        blockers.append("FRONTEND_PREFLIGHT_NODE_MISSING")
    if payload.get("npm_available") is not True:
        blockers.append("FRONTEND_PREFLIGHT_NPM_MISSING")
    current_digest = _frontend_source_tree_digest()
    declared_digest = payload.get("frontend_source_tree_digest")
    if not isinstance(declared_digest, str) or not declared_digest:
        blockers.append("FRONTEND_PREFLIGHT_SOURCE_TREE_DIGEST_MISSING")
    elif current_digest is not None and declared_digest != current_digest:
        blockers.append(f"FRONTEND_PREFLIGHT_SOURCE_TREE_DIGEST_MISMATCH:{declared_digest}:expected={current_digest}")
    embedded_blockers = payload.get("blockers")
    if not isinstance(embedded_blockers, list) or not all(isinstance(item, str) for item in embedded_blockers):
        blockers.append("FRONTEND_PREFLIGHT_BLOCKERS_INVALID")
    elif embedded_blockers:
        blockers.extend(f"FRONTEND_PREFLIGHT_EMBEDDED_BLOCKER:{item}" for item in embedded_blockers)

    summary = {
        "proof_name": "frontend_preflight_report",
        "path": str(path),
        "sha256": _file_sha256(path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers else "FAIL",
        "source_tree_digest": declared_digest,
        "created_at": payload.get("created_at"),
        "verified_at": _utc_now(),
        "node_available": payload.get("node_available"),
        "npm_available": payload.get("npm_available"),
        "package_json_exists": payload.get("package_json_exists"),
        "package_lock_exists": payload.get("package_lock_exists"),
        "skip_frontend_requested": payload.get("skip_frontend_requested"),
        "blocker_count": len(blockers),
    }
    return summary, blockers


def validate_frontend_certify_report(
    report_path: Path = FRONTEND_CERTIFY_REPORT_PATH,
    *,
    max_report_age_seconds: int | None = None,
) -> tuple[dict[str, object] | None, list[str]]:
    """Return a normalized frontend certify report summary and validation blockers."""
    blockers: list[str] = []
    if max_report_age_seconds is not None and max_report_age_seconds <= 0:
        raise ValueError("max_report_age_seconds must be positive when provided")
    if not report_path.exists():
        return None, [f"FRONTEND_CERTIFY_REPORT_MISSING:{report_path}"]
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"FRONTEND_CERTIFY_REPORT_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["FRONTEND_CERTIFY_REPORT_NOT_OBJECT"]

    schema_version = payload.get("schema_version")
    status = payload.get("status")
    failed_step = payload.get("failed_step")
    steps = payload.get("steps")
    report_path_value = payload.get("report_path")
    started_at_value = payload.get("started_at")
    finished_at_value = payload.get("finished_at")
    started_at_dt = _parse_iso_datetime(started_at_value)
    finished_at_dt = _parse_iso_datetime(finished_at_value)
    if schema_version != "frontend_certify/v1":
        blockers.append(f"FRONTEND_CERTIFY_REPORT_SCHEMA_UNEXPECTED:{schema_version}")
    if status != "PASS":
        blockers.append(f"FRONTEND_CERTIFY_REPORT_NOT_PASSING:{status}")
    if not isinstance(steps, list):
        blockers.append("FRONTEND_CERTIFY_REPORT_STEPS_NOT_LIST")
        steps = []
    if not isinstance(report_path_value, str):
        blockers.append("FRONTEND_CERTIFY_REPORT_PATH_MISSING")
    elif str(report_path) != report_path_value:
        blockers.append(f"FRONTEND_CERTIFY_REPORT_PATH_MISMATCH:{report_path_value}:expected={report_path}")
    if started_at_dt is None:
        blockers.append(f"FRONTEND_CERTIFY_REPORT_STARTED_AT_INVALID:{started_at_value}")
    if finished_at_dt is None:
        blockers.append(f"FRONTEND_CERTIFY_REPORT_FINISHED_AT_INVALID:{finished_at_value}")
    if started_at_dt is not None and finished_at_dt is not None:
        if finished_at_dt < started_at_dt:
            blockers.append("FRONTEND_CERTIFY_REPORT_TIME_RANGE_INVALID:finished_before_started")
        if max_report_age_seconds is not None:
            age_seconds = (datetime.now(timezone.utc) - finished_at_dt).total_seconds()
            if age_seconds > max_report_age_seconds:
                blockers.append(
                    f"FRONTEND_CERTIFY_REPORT_STALE:{int(age_seconds)}s:max={max_report_age_seconds}s"
                )

    current_frontend_digest = _frontend_source_tree_digest()
    declared_frontend_digest = payload.get("frontend_source_tree_digest")
    if not isinstance(declared_frontend_digest, str) or not declared_frontend_digest:
        blockers.append("FRONTEND_CERTIFY_REPORT_SOURCE_TREE_DIGEST_MISSING")
    elif current_frontend_digest is not None and declared_frontend_digest != current_frontend_digest:
        blockers.append(
            f"FRONTEND_CERTIFY_REPORT_SOURCE_TREE_DIGEST_MISMATCH:{declared_frontend_digest}:expected={current_frontend_digest}"
        )
    for field_name, expected_path in (
        ("package_json_sha256", FRONTEND_ROOT / "package.json"),
        ("package_lock_sha256", FRONTEND_ROOT / "package-lock.json"),
    ):
        declared_package_digest = payload.get(field_name)
        expected_package_digest = _file_sha256(expected_path) if expected_path.exists() else None
        if not isinstance(declared_package_digest, str) or not declared_package_digest:
            blockers.append(f"FRONTEND_CERTIFY_REPORT_{field_name.upper()}_MISSING")
        elif expected_package_digest is not None and declared_package_digest != expected_package_digest:
            blockers.append(
                f"FRONTEND_CERTIFY_REPORT_{field_name.upper()}_MISMATCH:{declared_package_digest}:expected={expected_package_digest}"
            )

    step_names: list[str] = []
    nonzero_steps: list[str] = []
    timed_out_steps: list[str] = []
    malformed_step_fields: list[str] = []
    required_step_fields = (
        "name",
        "command",
        "cwd",
        "timeout_seconds",
        "started_at",
        "finished_at",
        "duration_seconds",
        "exit_code",
        "timed_out",
        "stdout_tail",
        "stderr_tail",
        "artifact_paths",
    )
    for step in steps:
        if not isinstance(step, dict):
            blockers.append("FRONTEND_CERTIFY_REPORT_STEP_NOT_OBJECT")
            continue
        name = step.get("name")
        label = name if isinstance(name, str) and name else "<unknown>"
        if isinstance(name, str):
            step_names.append(name)
        for field in required_step_fields:
            if field not in step:
                malformed_step_fields.append(f"{label}:{field}:missing")
        command = step.get("command")
        if "command" in step and (not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command)):
            malformed_step_fields.append(f"{label}:command:invalid")
        if "cwd" in step and not isinstance(step.get("cwd"), str):
            malformed_step_fields.append(f"{label}:cwd:invalid")
        timeout_seconds = step.get("timeout_seconds")
        if "timeout_seconds" in step and (not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0):
            malformed_step_fields.append(f"{label}:timeout_seconds:invalid")
        duration_seconds = step.get("duration_seconds")
        if "duration_seconds" in step and (not isinstance(duration_seconds, (int, float)) or duration_seconds < 0):
            malformed_step_fields.append(f"{label}:duration_seconds:invalid")
        if "started_at" in step and _parse_iso_datetime(step.get("started_at")) is None:
            malformed_step_fields.append(f"{label}:started_at:invalid")
        if "finished_at" in step and _parse_iso_datetime(step.get("finished_at")) is None:
            malformed_step_fields.append(f"{label}:finished_at:invalid")
        if "timed_out" in step and not isinstance(step.get("timed_out"), bool):
            malformed_step_fields.append(f"{label}:timed_out:invalid")
        if "stdout_tail" in step and not isinstance(step.get("stdout_tail"), str):
            malformed_step_fields.append(f"{label}:stdout_tail:invalid")
        if "stderr_tail" in step and not isinstance(step.get("stderr_tail"), str):
            malformed_step_fields.append(f"{label}:stderr_tail:invalid")
        artifact_paths = step.get("artifact_paths")
        if "artifact_paths" in step and (not isinstance(artifact_paths, list) or not all(isinstance(item, str) for item in artifact_paths)):
            malformed_step_fields.append(f"{label}:artifact_paths:invalid")
        exit_code = step.get("exit_code")
        if exit_code != 0 and isinstance(name, str):
            nonzero_steps.append(f"{name}:{exit_code}")
        if step.get("timed_out") is True and isinstance(name, str):
            timed_out_steps.append(name)

    expected_steps = list(FRONTEND_CERTIFY_REQUIRED_STEPS)
    missing_steps = [name for name in expected_steps if name not in step_names]
    unexpected_steps = [name for name in step_names if name not in expected_steps]
    duplicate_steps = sorted({name for name in step_names if step_names.count(name) > 1})
    if missing_steps:
        blockers.append("FRONTEND_CERTIFY_REPORT_REQUIRED_STEPS_MISSING:" + ",".join(missing_steps))
    if unexpected_steps:
        blockers.append("FRONTEND_CERTIFY_REPORT_UNEXPECTED_STEPS:" + ",".join(unexpected_steps))
    if duplicate_steps:
        blockers.append("FRONTEND_CERTIFY_REPORT_DUPLICATE_STEPS:" + ",".join(duplicate_steps))
    if nonzero_steps:
        blockers.append("FRONTEND_CERTIFY_REPORT_NONZERO_STEPS:" + ",".join(nonzero_steps))
    if timed_out_steps:
        blockers.append("FRONTEND_CERTIFY_REPORT_TIMED_OUT_STEPS:" + ",".join(timed_out_steps))
    if malformed_step_fields:
        blockers.append("FRONTEND_CERTIFY_REPORT_STEP_FIELDS_INVALID:" + ",".join(malformed_step_fields))

    verified_at = _utc_now()
    summary: dict[str, object] = {
        "proof_name": "frontend_certify_report",
        "schema_version": schema_version,
        "status": status,
        "failed_step": failed_step,
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "source_tree_digest": _frontend_source_tree_digest(),
        "created_at": payload.get("finished_at") or payload.get("started_at"),
        "verified_at": verified_at,
        "step_count": len(step_names),
        "step_names": step_names,
        "required_step_names": expected_steps,
        "missing_step_names": missing_steps,
        "unexpected_step_names": unexpected_steps,
        "duplicate_step_names": duplicate_steps,
        "nonzero_steps": nonzero_steps,
        "timed_out_steps": timed_out_steps,
        "malformed_step_fields": malformed_step_fields,
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "node_version": payload.get("node_version"),
        "report_path": payload.get("report_path"),
        "frontend_source_tree_digest": payload.get("frontend_source_tree_digest"),
        "package_json_sha256": payload.get("package_json_sha256"),
        "package_lock_sha256": payload.get("package_lock_sha256"),
        "default_step_timeout_seconds": payload.get("default_step_timeout_seconds"),
        "max_report_age_seconds": max_report_age_seconds,
    }
    return summary, blockers



def validate_frontend_clean_workspace_report(
    report_path: Path = FRONTEND_CLEAN_WORKSPACE_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    if not report_path.exists():
        return None, [f"FRONTEND_CLEAN_WORKSPACE_REPORT_MISSING:{report_path}"]
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"FRONTEND_CLEAN_WORKSPACE_REPORT_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["FRONTEND_CLEAN_WORKSPACE_REPORT_NOT_OBJECT"]

    schema_version = payload.get("schema_version")
    status = payload.get("status")
    paths = payload.get("paths")
    if schema_version != "frontend_clean_workspace/v1":
        blockers.append(f"FRONTEND_CLEAN_WORKSPACE_REPORT_SCHEMA_UNEXPECTED:{schema_version}")
    if status != "PASS":
        blockers.append(f"FRONTEND_CLEAN_WORKSPACE_REPORT_NOT_PASSING:{status}")
    if payload.get("repo_root") != str(REPO_ROOT):
        blockers.append(f"FRONTEND_CLEAN_WORKSPACE_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
    if payload.get("frontend_root") != str(FRONTEND_ROOT.resolve(strict=False)):
        blockers.append(
            f"FRONTEND_CLEAN_WORKSPACE_REPORT_FRONTEND_ROOT_MISMATCH:{payload.get('frontend_root')}:expected={FRONTEND_ROOT.resolve(strict=False)}"
        )
    if not isinstance(paths, list):
        blockers.append("FRONTEND_CLEAN_WORKSPACE_REPORT_PATHS_NOT_LIST")
        paths = []
    observed_names: list[str] = []
    malformed_paths: list[str] = []
    for item in paths:
        if not isinstance(item, dict):
            malformed_paths.append("<non-object>:invalid")
            continue
        name = item.get("name")
        label = name if isinstance(name, str) and name else "<unknown>"
        if isinstance(name, str):
            observed_names.append(name)
        for field_name in ("name", "path", "existed", "removed", "skipped_reason"):
            if field_name not in item:
                malformed_paths.append(f"{label}:{field_name}:missing")
        if "path" in item and not isinstance(item.get("path"), str):
            malformed_paths.append(f"{label}:path:invalid")
        if "existed" in item and not isinstance(item.get("existed"), bool):
            malformed_paths.append(f"{label}:existed:invalid")
        if "removed" in item and not isinstance(item.get("removed"), bool):
            malformed_paths.append(f"{label}:removed:invalid")
        skipped_reason = item.get("skipped_reason")
        if "skipped_reason" in item and skipped_reason is not None and not isinstance(skipped_reason, str):
            malformed_paths.append(f"{label}:skipped_reason:invalid")
        path_value = item.get("path")
        if isinstance(path_value, str):
            candidate = Path(path_value)
            try:
                candidate.resolve(strict=False).relative_to(FRONTEND_ROOT.resolve(strict=False))
            except ValueError:
                malformed_paths.append(f"{label}:path:escapes_frontend_root")
    expected_names = ["node_modules", ".next", "coverage"]
    missing_names = [name for name in expected_names if name not in observed_names]
    duplicate_names = sorted({name for name in observed_names if observed_names.count(name) > 1})
    unexpected_names = [name for name in observed_names if name not in expected_names]
    if missing_names:
        blockers.append("FRONTEND_CLEAN_WORKSPACE_REPORT_REQUIRED_PATHS_MISSING:" + ",".join(missing_names))
    if duplicate_names:
        blockers.append("FRONTEND_CLEAN_WORKSPACE_REPORT_DUPLICATE_PATHS:" + ",".join(duplicate_names))
    if unexpected_names:
        blockers.append("FRONTEND_CLEAN_WORKSPACE_REPORT_UNEXPECTED_PATHS:" + ",".join(unexpected_names))
    if malformed_paths:
        blockers.append("FRONTEND_CLEAN_WORKSPACE_REPORT_PATH_FIELDS_INVALID:" + ",".join(malformed_paths))
    blockers.extend(str(item) for item in payload.get("blockers", []) if isinstance(item, str))

    summary: dict[str, object] = {
        "proof_name": "frontend_clean_workspace_report",
        "schema_version": schema_version,
        "status": status,
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "source_tree_digest": _frontend_source_tree_digest(),
        "created_at": payload.get("finished_at") or payload.get("started_at"),
        "verified_at": _utc_now(),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "dry_run": payload.get("dry_run"),
        "cleaned_path_names": observed_names,
        "missing_path_names": missing_names,
        "unexpected_path_names": unexpected_names,
        "duplicate_path_names": duplicate_names,
        "frontend_root": payload.get("frontend_root"),
    }
    return summary, blockers



def validate_public_surface_dashboard_report(
    report_path: Path = PUBLIC_SURFACE_DASHBOARD_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    payload, load_blockers = _load_json_object(report_path, blocker_prefix="PUBLIC_SURFACE_DASHBOARD_REPORT")
    blockers.extend(load_blockers)
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != "public_surface_dashboard/v1":
        blockers.append(f"PUBLIC_SURFACE_DASHBOARD_REPORT_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("ok") is not True:
        blockers.append(f"PUBLIC_SURFACE_DASHBOARD_REPORT_NOT_OK:{payload.get('ok')}")
    if payload.get("repo_root") != str(REPO_ROOT):
        blockers.append(f"PUBLIC_SURFACE_DASHBOARD_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
    violations = payload.get("violations")
    if violations not in ([], ()):
        blockers.append("PUBLIC_SURFACE_DASHBOARD_REPORT_HAS_VIOLATIONS")
    ratchet = payload.get("ratchet_validation")
    if not isinstance(ratchet, dict):
        blockers.append("PUBLIC_SURFACE_DASHBOARD_RATCHET_VALIDATION_MISSING")
    else:
        if ratchet.get("schema_version") != "public_surface_ratchet_validation/v1":
            blockers.append(f"PUBLIC_SURFACE_DASHBOARD_RATCHET_SCHEMA_UNEXPECTED:{ratchet.get('schema_version')}")
        if ratchet.get("status") != "PASS":
            blockers.append(f"PUBLIC_SURFACE_DASHBOARD_RATCHET_NOT_PASSING:{ratchet.get('status')}")
        if ratchet.get("blockers"):
            blockers.append("PUBLIC_SURFACE_DASHBOARD_RATCHET_HAS_BLOCKERS")
    source_tree_digest = _source_manifest_digest(
        [
            REPO_ROOT / "strategy_validator" / "application" / "public_surface_dashboard.py",
            REPO_ROOT / "strategy_validator" / "application" / "public_surface.py",
            REPO_ROOT / "strategy_validator" / "cli_support" / "public_surface_inventory.py",
            REPO_ROOT / "scripts" / "public_surface_dashboard.py",
            REPO_ROOT / "docs" / "audits" / "public_surface_dashboard.md",
            PUBLIC_SURFACE_RATCHET_PATH,
        ]
    )
    summary = {
        "proof_name": "public_surface_dashboard",
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers else "FAIL",
        "source_tree_digest": source_tree_digest,
        "created_at": payload.get("generated_at"),
        "verified_at": _utc_now(),
        "ok": payload.get("ok"),
        "violation_count": len(violations) if isinstance(violations, list) else None,
        "ratchet_status": ratchet.get("status") if isinstance(ratchet, dict) else None,
    }
    return summary, blockers


def validate_package_repo_check_report(
    report_path: Path = PACKAGE_REPO_CHECK_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    payload, load_blockers = _load_json_object(report_path, blocker_prefix="PACKAGE_REPO_CHECK_REPORT")
    blockers.extend(load_blockers)
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != "clean_repo_archive/v2":
        blockers.append(f"PACKAGE_REPO_CHECK_REPORT_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("status") != "PASS":
        blockers.append(f"PACKAGE_REPO_CHECK_REPORT_NOT_PASSING:{payload.get('status')}")
    if payload.get("repo_root") != str(REPO_ROOT):
        blockers.append(f"PACKAGE_REPO_CHECK_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
    if payload.get("output_path") is not None:
        blockers.append(f"PACKAGE_REPO_CHECK_REPORT_OUTPUT_PATH_NOT_NONE:{payload.get('output_path')}")
    if payload.get("blockers"):
        blockers.append("PACKAGE_REPO_CHECK_REPORT_HAS_BLOCKERS")
    source_tree_digest = _source_manifest_digest(
        [
            REPO_ROOT / "scripts" / "package_repo.py",
            REPO_ROOT / "scripts" / "_path_integrity.py",
            REPO_ROOT / ".gitignore",
            REPO_ROOT / ".dockerignore",
        ]
    )
    summary = {
        "proof_name": "package_repo_check",
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers else "FAIL",
        "source_tree_digest": source_tree_digest,
        "created_at": payload.get("generated_at"),
        "verified_at": _utc_now(),
        "included_file_count": payload.get("included_file_count"),
        "skipped_file_count": payload.get("skipped_file_count"),
    }
    return summary, blockers



def _researcher_fixture_artifact_root_from_payload(payload: dict[str, object], report_path: Path) -> Path:
    value = payload.get("researcher_artifact_root")
    if isinstance(value, str) and value.strip():
        candidate = Path(value)
        return candidate if candidate.is_absolute() else REPO_ROOT / candidate
    for step in payload.get("steps", []):
        if not isinstance(step, dict):
            continue
        command = step.get("command")
        if not isinstance(command, list):
            continue
        tokens = [str(item) for item in command]
        if "--researcher-artifact-root" not in tokens:
            continue
        index = tokens.index("--researcher-artifact-root") + 1
        if index < len(tokens):
            candidate = Path(tokens[index])
            return candidate if candidate.is_absolute() else REPO_ROOT / candidate
    fallback = report_path.parent / "fixture"
    return fallback


def validate_researcher_fixture_report(
    report_path: Path = RESEARCHER_FIXTURE_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    payload, load_blockers = _load_json_object(report_path, blocker_prefix="RESEARCHER_FIXTURE_REPORT")
    blockers.extend(load_blockers)
    if payload is None:
        return None, blockers

    if payload.get("schema_version") != "certification_stability/v2":
        blockers.append(f"RESEARCHER_FIXTURE_REPORT_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("status") != "PASS":
        blockers.append(f"RESEARCHER_FIXTURE_REPORT_NOT_PASSING:{payload.get('status')}")
    if payload.get("repo_root") != str(REPO_ROOT):
        blockers.append(f"RESEARCHER_FIXTURE_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
    declared_output_path = _repo_relative_or_absolute_path(payload.get("output_path"))
    if declared_output_path != report_path:
        blockers.append(f"RESEARCHER_FIXTURE_REPORT_PATH_MISMATCH:{payload.get('output_path')}:expected={report_path}")
    if payload.get("phases") != ["researcher_fixture"]:
        blockers.append(f"RESEARCHER_FIXTURE_REPORT_PHASES_UNEXPECTED:{payload.get('phases')}")

    steps = payload.get("steps")
    if not isinstance(steps, list):
        blockers.append("RESEARCHER_FIXTURE_REPORT_STEPS_NOT_LIST")
        steps = []
    step_names: list[str] = []
    nonzero_steps: list[str] = []
    for step in steps:
        if not isinstance(step, dict):
            blockers.append("RESEARCHER_FIXTURE_REPORT_STEP_NOT_OBJECT")
            continue
        name = step.get("name")
        if isinstance(name, str):
            step_names.append(name)
        if step.get("timed_out") is True or step.get("exit_code") != 0:
            if isinstance(name, str):
                suffix = "TIMEOUT" if step.get("timed_out") is True else str(step.get("exit_code"))
                nonzero_steps.append(f"{name}:{suffix}")
    expected_steps = list(RESEARCHER_FIXTURE_REQUIRED_STEPS)
    missing_steps = [name for name in expected_steps if name not in step_names]
    duplicate_steps = sorted({name for name in step_names if step_names.count(name) > 1})
    unexpected_steps = [name for name in step_names if name not in expected_steps]
    if missing_steps:
        blockers.append("RESEARCHER_FIXTURE_REPORT_REQUIRED_STEPS_MISSING:" + ",".join(missing_steps))
    if duplicate_steps:
        blockers.append("RESEARCHER_FIXTURE_REPORT_DUPLICATE_STEPS:" + ",".join(duplicate_steps))
    if unexpected_steps:
        blockers.append("RESEARCHER_FIXTURE_REPORT_UNEXPECTED_STEPS:" + ",".join(unexpected_steps))
    if nonzero_steps:
        blockers.append("RESEARCHER_FIXTURE_REPORT_NONZERO_STEPS:" + ",".join(nonzero_steps))

    artifact_root = _researcher_fixture_artifact_root_from_payload(payload, report_path)
    certification_path = artifact_root / "researcher_certification" / "latest" / "researcher_certification_report.json"
    release_readiness_path = artifact_root / "research_os_release_readiness" / "latest" / "research_os_release_readiness_report.json"
    paper_evidence_root = artifact_root / "paper_evidence" / "latest"
    certification_payload: dict[str, object] | None = None
    if not certification_path.exists():
        blockers.append(f"RESEARCHER_FIXTURE_CERTIFICATION_REPORT_MISSING:{certification_path}")
    else:
        certification_payload, certification_load_blockers = _load_json_object(
            certification_path,
            blocker_prefix="RESEARCHER_FIXTURE_CERTIFICATION_REPORT",
        )
        blockers.extend(certification_load_blockers)
        if certification_payload is not None:
            if certification_payload.get("schema_version") != "researcher_certification_report/v1":
                blockers.append(
                    "RESEARCHER_FIXTURE_CERTIFICATION_SCHEMA_UNEXPECTED:"
                    f"{certification_payload.get('schema_version')}"
                )
            if certification_payload.get("decision") != "CERTIFIED":
                blockers.append(f"RESEARCHER_FIXTURE_CERTIFICATION_NOT_CERTIFIED:{certification_payload.get('decision')}")
            if certification_payload.get("blockers") not in ([], None):
                blockers.append("RESEARCHER_FIXTURE_CERTIFICATION_HAS_BLOCKERS")
            checks = certification_payload.get("checks")
            if not isinstance(checks, dict):
                blockers.append("RESEARCHER_FIXTURE_CERTIFICATION_CHECKS_NOT_OBJECT")
            else:
                failing_checks = [name for name, value in checks.items() if value != "PASS"]
                if failing_checks:
                    blockers.append("RESEARCHER_FIXTURE_CERTIFICATION_CHECKS_NOT_PASSING:" + ",".join(sorted(failing_checks)))
            if certification_payload.get("no_live_broker_authority") is not True:
                blockers.append("RESEARCHER_FIXTURE_CERTIFICATION_LIVE_AUTHORITY_NOT_DENIED")
            if certification_payload.get("read_plane_only") is not True:
                blockers.append("RESEARCHER_FIXTURE_CERTIFICATION_NOT_READ_PLANE_ONLY")

    if not release_readiness_path.exists():
        blockers.append(f"RESEARCHER_FIXTURE_RELEASE_READINESS_REPORT_MISSING:{release_readiness_path}")
    paper_evidence_reports = sorted(paper_evidence_root.glob("*_paper_evidence_evaluation.json")) if paper_evidence_root.exists() else []
    if not paper_evidence_reports:
        blockers.append(f"RESEARCHER_FIXTURE_PAPER_EVIDENCE_REPORT_MISSING:{paper_evidence_root}")

    summary = {
        "proof_name": "researcher_fixture_report",
        "path": str(report_path),
        "sha256": _file_sha256(report_path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers else "FAIL",
        "source_tree_digest": _researcher_fixture_source_tree_digest(),
        "created_at": payload.get("timestamp"),
        "verified_at": _utc_now(),
        "artifact_root": str(artifact_root),
        "step_count": len(step_names),
        "step_names": step_names,
        "required_step_names": expected_steps,
        "missing_step_names": missing_steps,
        "unexpected_step_names": unexpected_steps,
        "duplicate_step_names": duplicate_steps,
        "nonzero_steps": nonzero_steps,
        "certification_report_path": str(certification_path),
        "certification_report_sha256": _file_sha256(certification_path) if certification_path.exists() else None,
        "certification_decision": None if certification_payload is None else certification_payload.get("decision"),
        "release_readiness_report_path": str(release_readiness_path),
        "release_readiness_report_sha256": _file_sha256(release_readiness_path) if release_readiness_path.exists() else None,
        "paper_evidence_report_count": len(paper_evidence_reports),
    }
    return summary, blockers


def _proof_report_step(
    *,
    step_name: str,
    validator_name: str,
    summary: dict[str, object] | None,
    blockers: Sequence[str],
    report_path: Path,
    started: float,
) -> LocalCertifyStep:
    exit_code = 0 if not blockers else 1
    stdout = json.dumps(summary or {}, indent=2, sort_keys=True) if summary is not None else ""
    stderr = "\n".join(blockers)
    return LocalCertifyStep(
        name=step_name,
        command=("internal", validator_name, str(report_path)),
        cwd=_relative_cwd(REPO_ROOT),
        exit_code=exit_code,
        duration_seconds=round(time.perf_counter() - started, 3),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        artifact_paths=(str(report_path),) if report_path.exists() else (),
    )

def _frontend_certify_report_step(
    *,
    summary: dict[str, object] | None,
    blockers: Sequence[str],
    started: float,
) -> LocalCertifyStep:
    exit_code = 0 if not blockers else 1
    stdout = json.dumps(summary or {}, indent=2, sort_keys=True) if summary is not None else ""
    stderr = "\n".join(blockers)
    return LocalCertifyStep(
        name="frontend_certify_report_validation",
        command=("internal", "validate_frontend_certify_report", str(FRONTEND_CERTIFY_REPORT_PATH)),
        cwd=_relative_cwd(REPO_ROOT),
        exit_code=exit_code,
        duration_seconds=round(time.perf_counter() - started, 3),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        artifact_paths=(str(FRONTEND_CERTIFY_REPORT_PATH),) if FRONTEND_CERTIFY_REPORT_PATH.exists() else (),
    )


def _load_json_object(path: Path, *, blocker_prefix: str) -> tuple[dict[str, object] | None, list[str]]:
    if not path.exists():
        return None, [f"{blocker_prefix}_MISSING:{path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{blocker_prefix}_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, [f"{blocker_prefix}_NOT_OBJECT"]
    return payload, []


def validate_shard_proof_reports(
    *,
    proof_name: str,
    summary_path: Path,
    verification_path: Path,
    expected_summary_schema: str,
    expected_verification_schema: str,
) -> tuple[dict[str, object] | None, list[str]]:
    """Validate summary + verification artifacts for a resumable proof path."""
    prefix = proof_name.upper()
    blockers: list[str] = []
    summary_payload, summary_blockers = _load_json_object(summary_path, blocker_prefix=f"{prefix}_SUMMARY")
    verification_payload, verification_blockers = _load_json_object(
        verification_path,
        blocker_prefix=f"{prefix}_SUMMARY_VERIFICATION",
    )
    blockers.extend(summary_blockers)
    blockers.extend(verification_blockers)

    if summary_payload is not None:
        schema = summary_payload.get("schema_version")
        status = summary_payload.get("status")
        if schema != expected_summary_schema:
            blockers.append(f"{prefix}_SUMMARY_SCHEMA_UNEXPECTED:{schema}")
        if status != "PASS":
            blockers.append(f"{prefix}_SUMMARY_NOT_PASSING:{status}")
        summary_report_blockers = summary_payload.get("blockers")
        if summary_report_blockers:
            blockers.append(f"{prefix}_SUMMARY_HAS_BLOCKERS")
    if verification_payload is not None:
        schema = verification_payload.get("schema_version")
        status = verification_payload.get("status")
        if schema != expected_verification_schema:
            blockers.append(f"{prefix}_SUMMARY_VERIFICATION_SCHEMA_UNEXPECTED:{schema}")
        if status != "PASS":
            blockers.append(f"{prefix}_SUMMARY_VERIFICATION_NOT_PASSING:{status}")
        verification_report_blockers = verification_payload.get("blockers")
        if verification_report_blockers:
            blockers.append(f"{prefix}_SUMMARY_VERIFICATION_HAS_BLOCKERS")
        verification_summary_path = verification_payload.get("summary_path")
        if verification_summary_path is not None and str(summary_path) != str(verification_summary_path):
            blockers.append(f"{prefix}_SUMMARY_VERIFICATION_PATH_MISMATCH:{verification_summary_path}:expected={summary_path}")

    if summary_payload is None or verification_payload is None:
        return None, blockers

    summary_sha256 = _file_sha256(summary_path)
    summary_schema_version = summary_payload.get("schema_version")
    summary: dict[str, object] = {
        "proof_name": proof_name,
        "status": "PASS" if not blockers else "FAIL",
        "path": str(summary_path),
        "sha256": summary_sha256,
        "schema_version": summary_schema_version,
        "summary_path": str(summary_path),
        "summary_sha256": summary_sha256,
        "summary_schema_version": summary_schema_version,
        "summary_status": summary_payload.get("status"),
        "summary_blocker_count": len(summary_payload.get("blockers") or []),
        "summary_source_tree": (
            summary_payload.get("collection_source_tree")
            or summary_payload.get("constitutional_source_tree")
            or summary_payload.get("pytest_execution_source_tree")
        ),
        "source_tree_digest": (
            (summary_payload.get("collection_source_tree") or {}).get("manifest_sha256")
            if isinstance(summary_payload.get("collection_source_tree"), dict)
            else (summary_payload.get("constitutional_source_tree") or {}).get("manifest_sha256")
            if isinstance(summary_payload.get("constitutional_source_tree"), dict)
            else (summary_payload.get("pytest_execution_source_tree") or {}).get("manifest_sha256")
            if isinstance(summary_payload.get("pytest_execution_source_tree"), dict)
            else None
        ),
        "created_at": summary_payload.get("timestamp") or summary_payload.get("created_at"),
        "verification_path": str(verification_path),
        "verification_sha256": _file_sha256(verification_path),
        "verification_schema_version": verification_payload.get("schema_version"),
        "verification_status": verification_payload.get("status"),
        "verification_blocker_count": len(verification_payload.get("blockers") or []),
        "verified_at": verification_payload.get("timestamp") or verification_payload.get("verified_at"),
    }
    for optional_field in (
        "collection_shard_count",
        "constitutional_shard_count",
        "pytest_shard_count",
        "passed_shard_count",
        "failed_shard_count",
        "timed_out_shard_count",
        "nonzero_shard_count",
        "total_test_count",
        "total_duration_seconds",
        "first_failed_shard",
        "next_diagnostic",
    ):
        if optional_field in summary_payload:
            summary[optional_field] = summary_payload.get(optional_field)
    return summary, blockers


def validate_collection_shards_proof(
    summary_path: Path = COLLECTION_SHARDS_SUMMARY_PATH,
    verification_path: Path = COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    return validate_shard_proof_reports(
        proof_name="collection_shards_proof",
        summary_path=summary_path,
        verification_path=verification_path,
        expected_summary_schema="certification_stability_collection_summary/v1",
        expected_verification_schema="certification_stability_collection_summary_verification/v1",
    )


def validate_constitutional_shards_proof(
    summary_path: Path = CONSTITUTIONAL_SHARDS_SUMMARY_PATH,
    verification_path: Path = CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    return validate_shard_proof_reports(
        proof_name="constitutional_shards_proof",
        summary_path=summary_path,
        verification_path=verification_path,
        expected_summary_schema="certification_stability_constitutional_summary/v2",
        expected_verification_schema="certification_stability_constitutional_summary_verification/v1",
    )



def validate_pytest_execution_shards_proof(
    summary_path: Path = PYTEST_EXECUTION_SHARDS_SUMMARY_PATH,
    verification_path: Path = PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    return validate_shard_proof_reports(
        proof_name="pytest_execution_shards_proof",
        summary_path=summary_path,
        verification_path=verification_path,
        expected_summary_schema="certification_stability_pytest_execution_summary/v1",
        expected_verification_schema="certification_stability_pytest_execution_summary_verification/v1",
    )

def _shard_proof_report_step(
    *,
    step_name: str,
    validator_name: str,
    summary: dict[str, object] | None,
    blockers: Sequence[str],
    summary_path: Path,
    verification_path: Path,
    started: float,
) -> LocalCertifyStep:
    exit_code = 0 if not blockers else 1
    stdout = json.dumps(summary or {}, indent=2, sort_keys=True) if summary is not None else ""
    stderr = "\n".join(blockers)
    artifact_paths = tuple(str(path) for path in (summary_path, verification_path) if path.exists())
    return LocalCertifyStep(
        name=step_name,
        command=("internal", validator_name, str(summary_path), str(verification_path)),
        cwd=_relative_cwd(REPO_ROOT),
        exit_code=exit_code,
        duration_seconds=round(time.perf_counter() - started, 3),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        artifact_paths=artifact_paths,
    )


def _pytest_execution_shards_replacement_step(
    *,
    summary: dict[str, object] | None,
    blockers: Sequence[str],
    started: float,
) -> LocalCertifyStep:
    """Record that backend pytest execution was proven by bounded shards.

    The step intentionally uses the canonical ``pytest`` step name so the Python
    core report keeps one backend-test gate while the command documents that the
    gate was satisfied by sealed execution-shard proof rather than an opaque
    monolithic pytest invocation.
    """
    exit_code = 0 if not blockers else 1
    stdout = json.dumps(summary or {}, indent=2, sort_keys=True) if summary is not None else ""
    stderr = "\n".join(blockers)
    artifact_paths = tuple(
        str(path)
        for path in (PYTEST_EXECUTION_SHARDS_SUMMARY_PATH, PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH)
        if path.exists()
    )
    return LocalCertifyStep(
        name="pytest",
        command=(
            "internal",
            "pytest_execution_shards_replace_monolith",
            str(PYTEST_EXECUTION_SHARDS_SUMMARY_PATH),
            str(PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH),
        ),
        cwd=_relative_cwd(REPO_ROOT),
        exit_code=exit_code,
        duration_seconds=round(time.perf_counter() - started, 3),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        artifact_paths=artifact_paths,
    )


def planned_steps(*, include_frontend: bool, include_pytest: bool = True, clean_frontend_workspace: bool = False) -> list[tuple[str, tuple[str, ...], Path]]:
    """Return the canonical local certification plan.

    Tests compare this plan with the CI validate job so local certification does
    not silently drift away from the gates treated as canonical in CI.
    """
    py = sys.executable
    steps: list[tuple[str, tuple[str, ...], Path]] = [
        (
            "compileall",
            (py, "-m", "compileall", "-q", "strategy_validator", "tests", "scripts"),
            REPO_ROOT,
        ),
        ("source_health", (py, "scripts/source_health.py"), REPO_ROOT),
        ("repository_truth", (py, "scripts/repository_truth_check.py"), REPO_ROOT),
        ("migration_truth", (py, "scripts/migration_truth_check.py"), REPO_ROOT),
        (
            "public_surface_dashboard",
            (
                py,
                "scripts/public_surface_dashboard.py",
                "--check-doc",
                "docs/audits/public_surface_dashboard.md",
                "--check-ratchet",
                PUBLIC_SURFACE_RATCHET_PATH.as_posix(),
                "--output-json",
                PUBLIC_SURFACE_DASHBOARD_REPORT_PATH.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        ),
        (
            "package_repo_check",
            (
                py,
                "scripts/package_repo.py",
                "--check",
                "--json",
                "--report-output",
                PACKAGE_REPO_CHECK_REPORT_PATH.as_posix(),
            ),
            REPO_ROOT,
        ),
    ]
    if include_pytest:
        steps.append(("pytest", (py, "-m", "pytest", "-q"), REPO_ROOT))
    if include_frontend and (FRONTEND_ROOT / "package-lock.json").exists():
        if clean_frontend_workspace:
            steps.append(
                (
                    "frontend_clean_workspace",
                    (
                        py,
                        "scripts/clean_frontend_workspace.py",
                        "--output",
                        FRONTEND_CLEAN_WORKSPACE_REPORT_PATH.as_posix(),
                        "--json",
                    ),
                    REPO_ROOT,
                )
            )
        steps.extend(
            [
                ("frontend_npm_ci", (_npm_executable(), "ci"), FRONTEND_ROOT),
                ("frontend_certify", (_npm_executable(), "run", "certify"), FRONTEND_ROOT),
            ]
        )
    return steps


def planned_researcher_fixture_steps(
    *,
    artifact_root: Path = RESEARCHER_FIXTURE_ARTIFACT_ROOT,
    report_path: Path = RESEARCHER_FIXTURE_REPORT_PATH,
    timeout_seconds: int = 900,
    heartbeat_seconds: int = 10,
) -> list[tuple[str, tuple[str, ...], Path]]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if heartbeat_seconds < 0:
        raise ValueError("heartbeat_seconds must be non-negative")
    py = sys.executable
    return [
        (
            "researcher_fixture",
            (
                py,
                "scripts/certification_stability.py",
                "--phase",
                "researcher-fixture",
                "--researcher-artifact-root",
                artifact_root.as_posix(),
                "--timeout-seconds",
                str(timeout_seconds),
                "--heartbeat-seconds",
                str(heartbeat_seconds),
                "--output",
                report_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    ]


def planned_collection_shard_steps(
    *,
    shard_count: int,
    timeout_seconds: int,
    heartbeat_seconds: int = 5,
) -> list[tuple[str, tuple[str, ...], Path]]:
    """Return optional resumable full pytest collection proof steps."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if heartbeat_seconds < 0:
        raise ValueError("heartbeat_seconds must be non-negative")
    py = sys.executable
    report_paths = [CERTIFICATION_STABILITY_DIR / f"collection_shard_{index}.json" for index in range(1, shard_count + 1)]
    steps: list[tuple[str, tuple[str, ...], Path]] = []
    for index, report_path in enumerate(report_paths, start=1):
        steps.append(
            (
                f"collection_shard_{index:02d}_of_{shard_count:02d}",
                (
                    py,
                    "scripts/certification_stability.py",
                    "--phase",
                    "collect-shards",
                    "--collection-shard-count",
                    str(shard_count),
                    "--collection-shard-index",
                    str(index),
                    "--timeout-seconds",
                    str(timeout_seconds),
                    "--heartbeat-seconds",
                    str(heartbeat_seconds),
                    "--output",
                    report_path.as_posix(),
                    "--json",
                ),
                REPO_ROOT,
            )
        )
    summary_path = COLLECTION_SHARDS_SUMMARY_PATH
    verification_path = COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH
    steps.append(
        (
            "collection_shards_summary",
            (
                py,
                "scripts/certification_stability.py",
                "--aggregate-collection-shard-reports",
                *(path.as_posix() for path in report_paths),
                "--collection-shard-count",
                str(shard_count),
                "--output",
                summary_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    steps.append(
        (
            "collection_shards_summary_verification",
            (
                py,
                "scripts/certification_stability.py",
                "--verify-collection-summary",
                summary_path.as_posix(),
                "--output",
                verification_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    return steps


def planned_constitutional_shard_steps(
    *,
    shard_count: int,
    timeout_seconds: int,
    heartbeat_seconds: int = 5,
) -> list[tuple[str, tuple[str, ...], Path]]:
    """Return optional resumable constitutional proof steps for local certify.

    These steps are intentionally opt-in: the canonical local/CI parity plan still
    contains the raw full pytest gate, while operators can request this bounded
    proof path when they need auditable constitutional attribution on hosts with
    short process windows.
    """
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if heartbeat_seconds < 0:
        raise ValueError("heartbeat_seconds must be non-negative")
    py = sys.executable
    report_paths = [CERTIFICATION_STABILITY_DIR / f"constitutional_shard_{index}.json" for index in range(1, shard_count + 1)]
    steps: list[tuple[str, tuple[str, ...], Path]] = []
    for index, report_path in enumerate(report_paths, start=1):
        steps.append(
            (
                f"constitutional_shard_{index:02d}_of_{shard_count:02d}",
                (
                    py,
                    "scripts/certification_stability.py",
                    "--phase",
                    "constitutional-shards",
                    "--constitutional-shard-count",
                    str(shard_count),
                    "--constitutional-shard-index",
                    str(index),
                    "--timeout-seconds",
                    str(timeout_seconds),
                    "--heartbeat-seconds",
                    str(heartbeat_seconds),
                    "--output",
                    report_path.as_posix(),
                    "--json",
                ),
                REPO_ROOT,
            )
        )
    summary_path = CONSTITUTIONAL_SHARDS_SUMMARY_PATH
    verification_path = CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH
    steps.append(
        (
            "constitutional_shards_summary",
            (
                py,
                "scripts/certification_stability.py",
                "--aggregate-constitutional-shard-reports",
                *(path.as_posix() for path in report_paths),
                "--constitutional-shard-count",
                str(shard_count),
                "--output",
                summary_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    steps.append(
        (
            "constitutional_shards_summary_verification",
            (
                py,
                "scripts/certification_stability.py",
                "--verify-constitutional-summary",
                summary_path.as_posix(),
                "--output",
                verification_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    return steps


def planned_pytest_execution_shard_steps(
    *,
    shard_count: int,
    timeout_seconds: int,
    heartbeat_seconds: int = 5,
) -> list[tuple[str, tuple[str, ...], Path]]:
    """Return optional resumable backend pytest execution proof steps."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if heartbeat_seconds < 0:
        raise ValueError("heartbeat_seconds must be non-negative")
    py = sys.executable
    report_paths = [CERTIFICATION_STABILITY_DIR / f"pytest_execution_shard_{index}.json" for index in range(1, shard_count + 1)]
    steps: list[tuple[str, tuple[str, ...], Path]] = []
    for index, report_path in enumerate(report_paths, start=1):
        steps.append(
            (
                f"pytest_execution_shard_{index:02d}_of_{shard_count:02d}",
                (
                    py,
                    "scripts/certification_stability.py",
                    "--phase",
                    "pytest-execution-shards",
                    "--pytest-shard-count",
                    str(shard_count),
                    "--pytest-shard-index",
                    str(index),
                    "--timeout-seconds",
                    str(timeout_seconds),
                    "--heartbeat-seconds",
                    str(heartbeat_seconds),
                    "--output",
                    report_path.as_posix(),
                    "--json",
                ),
                REPO_ROOT,
            )
        )
    summary_path = PYTEST_EXECUTION_SHARDS_SUMMARY_PATH
    verification_path = PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH
    steps.append(
        (
            "pytest_execution_shards_summary",
            (
                py,
                "scripts/certification_stability.py",
                "--aggregate-pytest-execution-shard-reports",
                *(path.as_posix() for path in report_paths),
                "--pytest-shard-count",
                str(shard_count),
                "--output",
                summary_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    steps.append(
        (
            "pytest_execution_shards_summary_verification",
            (
                py,
                "scripts/certification_stability.py",
                "--verify-pytest-execution-summary",
                summary_path.as_posix(),
                "--output",
                verification_path.as_posix(),
                "--json",
            ),
            REPO_ROOT,
        )
    )
    return steps


# Backwards-compatible private alias for older tests/importers.
def _planned_steps(*, include_frontend: bool) -> list[tuple[str, tuple[str, ...], Path]]:
    return planned_steps(include_frontend=include_frontend)


def apply_research_paper_discovery_profile(args: argparse.Namespace) -> None:
    """Expand the current phase profile into explicit local-certify proof flags.

    The profile is intentionally an argument expander, not a shortcut around any
    gate.  It makes the Research-and-Paper-Discovery certification command
    reproducible while still leaving each proof visible in the final report.
    """
    if not getattr(args, "certify_research_paper_discovery", False):
        return
    args.clean_frontend_workspace = True
    args.include_collection_shards = True
    args.include_constitutional_shards = True
    args.include_pytest_shards = True
    args.include_researcher_fixture = True
    args.no_fail_fast = True


def _research_paper_discovery_profile_contract(*, frontend_included: bool) -> dict[str, object]:
    """Return the immutable current-phase certification contract.

    ``frontend_included`` is recorded for operator diagnostics, but it no
    longer changes the required proof set.  A Research-and-Paper-Discovery
    phase certificate must include frontend cleanup + frontend certify proof;
    otherwise a backend-only run could accidentally masquerade as full phase
    certification.
    """
    return {
        "schema_version": RESEARCH_PAPER_DISCOVERY_PROFILE_VERSION,
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "required_proofs": list(RESEARCH_PAPER_DISCOVERY_REQUIRED_PROOFS),
        "frontend_required": True,
        "frontend_included_at_runtime": frontend_included,
        "frontend_skip_allowed": False,
        "collection_shards_required": True,
        "constitutional_shards_required": True,
        "pytest_execution_shards_required": True,
        "researcher_fixture_required": True,
        "monolithic_pytest_required": False,
        "paper_pass_live_authority_firewall_required": True,
        "read_plane_only_required": True,
    }




def _profile_expected_artifact_paths() -> dict[str, str]:
    return {
        "frontend_preflight_report": str(FRONTEND_PREFLIGHT_REPORT_PATH),
        "frontend_clean_workspace_report": str(FRONTEND_CLEAN_WORKSPACE_REPORT_PATH),
        "frontend_certify_report": str(FRONTEND_CERTIFY_REPORT_PATH),
        "python_core_report": str(PYTHON_CORE_REPORT_PATH),
        "public_surface_dashboard": str(PUBLIC_SURFACE_DASHBOARD_REPORT_PATH),
        "package_repo_check": str(PACKAGE_REPO_CHECK_REPORT_PATH),
        "researcher_fixture_report": str(RESEARCHER_FIXTURE_REPORT_PATH),
        "collection_shards_summary": str(COLLECTION_SHARDS_SUMMARY_PATH),
        "collection_shards_summary_verification": str(COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH),
        "constitutional_shards_summary": str(CONSTITUTIONAL_SHARDS_SUMMARY_PATH),
        "constitutional_shards_summary_verification": str(CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH),
        "pytest_execution_shards_summary": str(PYTEST_EXECUTION_SHARDS_SUMMARY_PATH),
        "pytest_execution_shards_summary_verification": str(PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH),
        "local_certify_report": str(REPORT_PATH),
        "local_certify_report_verification": str(LOCAL_CERTIFY_REPORT_VERIFICATION_PATH),
        "phase_closure_report": str(RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH),
        "phase_evidence_bundle": str(RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH),
        "phase_evidence_bundle_seal": str(RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PATH),
        "phase_profile_plan": str(RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH),
        "phase_profile_plan_verification": str(RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH),
        "phase_run_report": str(RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH),
        "phase_run_report_verification": str(RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_PATH),
    }


def build_research_paper_discovery_steps(
    args: argparse.Namespace,
    *,
    frontend_included: bool,
    phase_preflight_failed: bool = False,
) -> list[tuple[str, tuple[str, ...], Path]]:
    if phase_preflight_failed:
        return []
    monolithic_pytest_included = (not args.include_pytest_shards) or args.run_monolithic_pytest_with_shards
    steps_to_run = planned_steps(
        include_frontend=frontend_included,
        include_pytest=monolithic_pytest_included,
        clean_frontend_workspace=args.clean_frontend_workspace,
    )
    if args.include_collection_shards:
        steps_to_run.extend(
            planned_collection_shard_steps(
                shard_count=args.collection_shard_count,
                timeout_seconds=args.collection_shard_timeout_seconds,
                heartbeat_seconds=args.collection_shard_heartbeat_seconds,
            )
        )
    if args.include_constitutional_shards:
        steps_to_run.extend(
            planned_constitutional_shard_steps(
                shard_count=args.constitutional_shard_count,
                timeout_seconds=args.constitutional_shard_timeout_seconds,
                heartbeat_seconds=args.constitutional_shard_heartbeat_seconds,
            )
        )
    if args.include_pytest_shards:
        steps_to_run.extend(
            planned_pytest_execution_shard_steps(
                shard_count=args.pytest_shard_count,
                timeout_seconds=args.pytest_shard_timeout_seconds,
                heartbeat_seconds=args.pytest_shard_heartbeat_seconds,
            )
        )
    if args.include_researcher_fixture:
        steps_to_run.extend(
            planned_researcher_fixture_steps(
                artifact_root=args.researcher_fixture_artifact_root,
                report_path=RESEARCHER_FIXTURE_REPORT_PATH,
                timeout_seconds=args.researcher_fixture_timeout_seconds,
                heartbeat_seconds=args.researcher_fixture_heartbeat_seconds,
            )
        )
    return steps_to_run


def _planned_step_entry(
    step: tuple[str, tuple[str, ...], Path],
    *,
    args: argparse.Namespace,
) -> dict[str, object]:
    name, command, cwd = step
    artifact_paths: list[str] = []
    if name == "frontend_clean_workspace":
        artifact_paths.append(str(FRONTEND_CLEAN_WORKSPACE_REPORT_PATH))
    elif name == "frontend_certify":
        artifact_paths.append(str(FRONTEND_CERTIFY_REPORT_PATH))
    elif name == "public_surface_dashboard":
        artifact_paths.append(str(PUBLIC_SURFACE_DASHBOARD_REPORT_PATH))
    elif name == "package_repo_check":
        artifact_paths.append(str(PACKAGE_REPO_CHECK_REPORT_PATH))
    elif name == "researcher_fixture":
        artifact_paths.append(str(RESEARCHER_FIXTURE_REPORT_PATH))
    elif name == "collection_shards_summary":
        artifact_paths.append(str(COLLECTION_SHARDS_SUMMARY_PATH))
    elif name == "collection_shards_summary_verification":
        artifact_paths.append(str(COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH))
    elif name == "constitutional_shards_summary":
        artifact_paths.append(str(CONSTITUTIONAL_SHARDS_SUMMARY_PATH))
    elif name == "constitutional_shards_summary_verification":
        artifact_paths.append(str(CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH))
    elif name == "pytest_execution_shards_summary":
        artifact_paths.append(str(PYTEST_EXECUTION_SHARDS_SUMMARY_PATH))
    elif name == "pytest_execution_shards_summary_verification":
        artifact_paths.append(str(PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH))
    return {
        "name": name,
        "command": list(command),
        "cwd": str(cwd),
        "timeout_seconds": _local_wrapper_timeout_for_step(name, args),
        "artifact_paths": artifact_paths,
    }


def write_research_paper_discovery_profile_plan(
    *,
    args: argparse.Namespace,
    frontend_included: bool,
    frontend_preflight_report: dict[str, object] | None,
    frontend_preflight_blockers: Sequence[str],
    phase_preflight_failed: bool,
    steps_to_run: Sequence[tuple[str, tuple[str, ...], Path]],
    output_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
) -> dict[str, object]:
    blockers = [
        f"RESEARCH_PAPER_DISCOVERY_PROFILE_FRONTEND_PREFLIGHT_BLOCKER:{blocker}"
        for blocker in frontend_preflight_blockers
    ]
    planned_step_entries = [_planned_step_entry(step, args=args) for step in steps_to_run]
    expensive_prefixes = (
        "collection_shard_",
        "constitutional_shard_",
        "pytest_execution_shard_",
    )
    expensive_names = {"frontend_npm_ci", "frontend_certify", "pytest", "researcher_fixture"}
    expensive_steps = [
        entry["name"]
        for entry in planned_step_entries
        if isinstance(entry.get("name"), str)
        and (entry["name"] in expensive_names or entry["name"].startswith(expensive_prefixes))
    ]
    payload: dict[str, object] = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile_contract": _research_paper_discovery_profile_contract(frontend_included=frontend_included),
        "frontend_required": True,
        "frontend_skip_allowed": False,
        "skip_frontend_requested": bool(args.skip_frontend),
        "frontend_included_at_runtime": frontend_included,
        "frontend_preflight_report": frontend_preflight_report,
        "frontend_preflight_status": (frontend_preflight_report or {}).get("status") if isinstance(frontend_preflight_report, dict) else None,
        "frontend_preflight_blockers": list(frontend_preflight_blockers),
        "phase_preflight_failed": phase_preflight_failed,
        "would_run_expensive_steps": bool(expensive_steps),
        "expensive_step_names": expensive_steps,
        "planned_step_count": len(planned_step_entries),
        "planned_steps": planned_step_entries,
        "required_proofs": list(RESEARCH_PAPER_DISCOVERY_REQUIRED_PROOFS),
        "expected_artifact_paths": _profile_expected_artifact_paths(),
        "collection_shard_count": args.collection_shard_count if args.include_collection_shards else None,
        "constitutional_shard_count": args.constitutional_shard_count if args.include_constitutional_shards else None,
        "pytest_shard_count": args.pytest_shard_count if args.include_pytest_shards else None,
        "monolithic_pytest_included": (not args.include_pytest_shards) or args.run_monolithic_pytest_with_shards,
        "pytest_execution_shards_replace_monolith": args.include_pytest_shards and not args.run_monolithic_pytest_with_shards,
        "source_tree_digest": _python_core_source_tree_digest(),
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "generated_at": _utc_now(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output_path),
    }
    payload["plan_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "plan_payload_sha256"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_research_paper_discovery_profile_plan(
    path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    payload, blockers = _load_json_object(path, blocker_prefix="RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN")
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_VERSION:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PHASE_UNEXPECTED:{payload.get('phase')}")
    embedded_blockers = payload.get("blockers")
    if not isinstance(embedded_blockers, list) or not all(isinstance(item, str) for item in embedded_blockers):
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_BLOCKERS_INVALID")
    elif embedded_blockers:
        blockers.extend(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_EMBEDDED_BLOCKER:{item}" for item in embedded_blockers)
    if payload.get("status") not in {"PASS", "FAIL"}:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_STATUS_UNEXPECTED:{payload.get('status')}")
    if payload.get("frontend_required") is not True:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_REQUIRED_FALSE")
    if payload.get("frontend_skip_allowed") is not False:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_SKIP_ALLOWED")
    preflight_report = payload.get("frontend_preflight_report")
    if not isinstance(preflight_report, dict):
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_PREFLIGHT_REPORT_MISSING")
    else:
        if payload.get("frontend_preflight_status") != preflight_report.get("status"):
            blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_PREFLIGHT_STATUS_MISMATCH")
        preflight_path_value = preflight_report.get("path")
        preflight_sha_value = preflight_report.get("sha256")
        if isinstance(preflight_path_value, str) and isinstance(preflight_sha_value, str):
            preflight_path = Path(preflight_path_value)
            if not preflight_path.exists():
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_PREFLIGHT_FILE_MISSING:{preflight_path}")
            else:
                observed_preflight_sha = _file_sha256(preflight_path)
                if preflight_sha_value != observed_preflight_sha:
                    blockers.append(
                        "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_PREFLIGHT_SHA256_MISMATCH:"
                        f"{preflight_sha_value}:expected={observed_preflight_sha}"
                    )
    output_path_value = payload.get("output_path")
    if not isinstance(output_path_value, str):
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_OUTPUT_PATH_MISSING")
    else:
        try:
            output_path_matches = Path(output_path_value).resolve() == path.resolve()
        except OSError:
            output_path_matches = False
        if not output_path_matches:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH_MISMATCH:{output_path_value}:expected={path}")
    if payload.get("source_tree_digest") != _python_core_source_tree_digest():
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SOURCE_TREE_MISMATCH:"
            f"{payload.get('source_tree_digest')}:expected={_python_core_source_tree_digest()}"
        )
    observed_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "plan_payload_sha256"})
    if payload.get("plan_payload_sha256") != observed_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PAYLOAD_DIGEST_MISMATCH:"
            f"{payload.get('plan_payload_sha256')}:expected={observed_digest}"
        )
    if payload.get("frontend_source_tree_digest") != _frontend_source_tree_digest():
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FRONTEND_SOURCE_TREE_MISMATCH:"
            f"{payload.get('frontend_source_tree_digest')}:expected={_frontend_source_tree_digest()}"
        )
    expected_artifacts = _profile_expected_artifact_paths()
    if payload.get("expected_artifact_paths") != expected_artifacts:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_EXPECTED_ARTIFACT_PATHS_MISMATCH")
    required_proofs = payload.get("required_proofs")
    if required_proofs != list(RESEARCH_PAPER_DISCOVERY_REQUIRED_PROOFS):
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_REQUIRED_PROOFS_MISMATCH:{required_proofs}")
    steps = payload.get("planned_steps")
    if not isinstance(steps, list):
        blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_STEPS_NOT_LIST")
        steps = []
    else:
        if payload.get("planned_step_count") != len(steps):
            blockers.append(
                "RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_STEP_COUNT_MISMATCH:"
                f"{payload.get('planned_step_count')}:expected={len(steps)}"
            )
        step_names = [step.get("name") for step in steps if isinstance(step, dict)]
        expensive_prefixes = ("collection_shard_", "constitutional_shard_", "pytest_execution_shard_")
        expensive_names = {"frontend_npm_ci", "frontend_certify", "pytest", "researcher_fixture"}
        observed_expensive = [
            name for name in step_names
            if isinstance(name, str) and (name in expensive_names or name.startswith(expensive_prefixes))
        ]
        if payload.get("expensive_step_names") != observed_expensive:
            blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_EXPENSIVE_STEPS_MISMATCH")
        if payload.get("would_run_expensive_steps") is not bool(observed_expensive):
            blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_EXPENSIVE_FLAG_MISMATCH")
        if payload.get("phase_preflight_failed") is True and step_names:
            blockers.append("RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PREFLIGHT_FAILED_WITH_PLANNED_STEPS")
        if payload.get("phase_preflight_failed") is not True:
            for required_step in ("compileall", "source_health", "repository_truth", "migration_truth", "public_surface_dashboard", "package_repo_check", "frontend_clean_workspace", "frontend_npm_ci", "frontend_certify", "collection_shards_summary", "constitutional_shards_summary", "pytest_execution_shards_summary", "researcher_fixture"):
                if required_step not in step_names:
                    blockers.append(f"RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_REQUIRED_STEP_MISSING:{required_step}")
    summary = {
        "proof_name": "research_paper_discovery_profile_plan",
        "path": str(path),
        "sha256": _file_sha256(path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers and payload.get("status") == "PASS" else "FAIL",
        "source_tree_digest": payload.get("source_tree_digest"),
        "created_at": payload.get("generated_at"),
        "verified_at": _utc_now(),
        "planned_step_count": payload.get("planned_step_count"),
        "phase_preflight_failed": payload.get("phase_preflight_failed"),
        "frontend_preflight_status": payload.get("frontend_preflight_status"),
        "would_run_expensive_steps": payload.get("would_run_expensive_steps"),
        "blocker_count": len(blockers),
    }
    return summary, blockers


def verify_research_paper_discovery_profile_plan(
    plan_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
    *,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Verify the Research-and-Paper-Discovery launch plan as a persisted proof artifact."""
    summary, blockers = validate_research_paper_discovery_profile_plan(plan_path)
    verification: dict[str, object] = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_SCHEMA_VERSION,
        "status": "PASS" if not blockers and summary is not None and summary.get("status") == "PASS" else "FAIL",
        "blockers": blockers,
        "plan_path": str(plan_path),
        "plan_sha256": _file_sha256(plan_path) if plan_path.exists() else None,
        "plan_summary": summary,
        "repo_root": str(REPO_ROOT),
        "source_tree_digest": _python_core_source_tree_digest(),
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "verified_at": _utc_now(),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification



def _json_artifact_status(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "path": None,
            "present": False,
            "sha256": None,
            "schema_version": None,
            "status": None,
        }
    row: dict[str, object] = {
        "path": str(path),
        "present": path.exists(),
        "sha256": _file_sha256(path) if path.exists() and path.is_file() else None,
        "schema_version": None,
        "status": None,
    }
    if path.exists() and path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            row["schema_version"] = payload.get("schema_version")
            row["status"] = payload.get("status")
    return row


def _final_certificate_artifact_paths() -> dict[str, Path]:
    return {
        "final_certificate_doc": FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_PATH,
        "phase_profile_plan": RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
        "phase_profile_plan_verification": RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
        "local_certify_report": REPORT_PATH,
        "local_certify_report_verification": LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
        "phase_run_report": RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH,
        "phase_run_report_verification": RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_PATH,
        "phase_closure_report": RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
        "phase_closure_report_verification": RESEARCH_PAPER_DISCOVERY_CLOSURE_VERIFICATION_PATH,
        "phase_evidence_bundle": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
        "phase_evidence_bundle_seal": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PATH,
        "phase_evidence_bundle_verification": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_VERIFICATION_PATH,
        "phase_evidence_bundle_export_verification": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_VERIFICATION_PATH,
        "frontend_preflight_report": FRONTEND_PREFLIGHT_REPORT_PATH,
        "frontend_clean_workspace_report": FRONTEND_CLEAN_WORKSPACE_REPORT_PATH,
        "frontend_certify_report": FRONTEND_CERTIFY_REPORT_PATH,
        "collection_shards_summary": COLLECTION_SHARDS_SUMMARY_PATH,
        "collection_shards_summary_verification": COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH,
        "constitutional_shards_summary": CONSTITUTIONAL_SHARDS_SUMMARY_PATH,
        "constitutional_shards_summary_verification": CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH,
        "pytest_execution_shards_summary": PYTEST_EXECUTION_SHARDS_SUMMARY_PATH,
        "pytest_execution_shards_summary_verification": PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH,
        "researcher_fixture_report": RESEARCHER_FIXTURE_REPORT_PATH,
        "public_surface_dashboard": PUBLIC_SURFACE_DASHBOARD_REPORT_PATH,
        "package_repo_check": PACKAGE_REPO_CHECK_REPORT_PATH,
    }


def _final_certificate_doc_contains_required_text(doc_text: str, needle: str) -> bool:
    compact_doc = " ".join(doc_text.split())
    compact_needle = " ".join(needle.split())
    return compact_needle in compact_doc


def build_final_research_paper_discovery_certification_index(
    *,
    final_certificate_doc_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_PATH,
    artifact_paths: dict[str, Path] | None = None,
    output_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PATH,
) -> dict[str, object]:
    """Build a machine-readable freshness index for the human final certificate.

    The markdown certificate is intentionally operator-readable. This index makes
    it machine-checkable by binding that prose to the canonical command chain,
    expected artifact paths, artifact hashes, and the no-live-authority / paper
    firewall assertions that the phase depends on.
    """
    blockers: list[str] = []
    artifacts_by_role = artifact_paths or _final_certificate_artifact_paths()
    doc_text = ""
    if not final_certificate_doc_path.exists() or not final_certificate_doc_path.is_file():
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_MISSING:{final_certificate_doc_path}")
    else:
        doc_text = final_certificate_doc_path.read_text(encoding="utf-8")

    missing_commands = [
        command
        for command in FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS
        if not _final_certificate_doc_contains_required_text(doc_text, command)
    ]
    for command in missing_commands:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_COMMAND_MISSING:{command}")

    missing_phrases = [
        phrase
        for phrase in FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_PHRASES
        if not _final_certificate_doc_contains_required_text(doc_text.lower(), phrase.lower())
    ]
    for phrase in missing_phrases:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_ASSERTION_TEXT_MISSING:{phrase}")

    artifact_rows: list[dict[str, object]] = []
    for role, path in sorted(artifacts_by_role.items()):
        row = _json_artifact_status(path)
        row["role"] = role
        row["expected_path"] = str(path)
        row["path_mentioned_in_certificate"] = _final_certificate_doc_contains_required_text(doc_text, str(path.relative_to(REPO_ROOT)) if path.is_absolute() and path.is_relative_to(REPO_ROOT) else str(path))
        if role != "final_certificate_doc":
            if row["present"] is not True:
                blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_ARTIFACT_MISSING:{role}:{path}")
            elif row.get("status") not in {"PASS", None}:
                blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_ARTIFACT_NOT_PASSING:{role}:{row.get('status')}")
            if role in {
                "phase_profile_plan",
                "local_certify_report",
                "phase_run_report",
                "phase_closure_report",
                "phase_evidence_bundle",
                "frontend_certify_report",
                "researcher_fixture_report",
                "public_surface_dashboard",
                "package_repo_check",
            } and row["path_mentioned_in_certificate"] is not True:
                blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_ARTIFACT_PATH_NOT_MENTIONED:{role}")
        artifact_rows.append(row)

    no_live_authority_assertion = _final_certificate_doc_contains_required_text(doc_text.lower(), "no-live-authority confirmation")
    paper_live_firewall_assertion = _final_certificate_doc_contains_required_text(doc_text.lower(), "paper/live firewall confirmation")
    not_autonomous_live_trading_assertion = _final_certificate_doc_contains_required_text(doc_text.lower(), "not autonomous live trading")
    payload: dict[str, object] = {
        "schema_version": FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "final_certificate_doc_path": str(final_certificate_doc_path),
        "final_certificate_doc_sha256": _file_sha256(final_certificate_doc_path) if final_certificate_doc_path.exists() else None,
        "canonical_command_count": len(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS),
        "canonical_commands": list(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_COMMANDS),
        "missing_commands": missing_commands,
        "required_assertion_phrases": list(FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_REQUIRED_PHRASES),
        "missing_assertion_phrases": missing_phrases,
        "no_live_authority_assertion": no_live_authority_assertion,
        "paper_live_firewall_assertion": paper_live_firewall_assertion,
        "not_autonomous_live_trading_assertion": not_autonomous_live_trading_assertion,
        "artifact_count": len(artifact_rows),
        "artifacts": artifact_rows,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "source_tree_digest": _python_core_source_tree_digest(),
        "output_path": str(output_path),
        "generated_at": _utc_now(),
    }
    payload["index_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "index_payload_sha256"})
    return payload


def write_final_research_paper_discovery_certification_index(
    *,
    final_certificate_doc_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_PATH,
    output_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PATH,
) -> dict[str, object]:
    index = build_final_research_paper_discovery_certification_index(
        final_certificate_doc_path=final_certificate_doc_path,
        output_path=output_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def validate_final_research_paper_discovery_certification_index(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    if not path.exists():
        return None, [f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_MISSING:{path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_NOT_OBJECT"]
    if payload.get("schema_version") != FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_SCHEMA_VERSION:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    declared_digest = payload.get("index_payload_sha256")
    observed_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "index_payload_sha256"})
    if declared_digest != observed_digest:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PAYLOAD_DIGEST_MISMATCH:{declared_digest}:expected={observed_digest}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PHASE_UNEXPECTED:{payload.get('phase')}")
    if payload.get("no_live_authority_assertion") is not True:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_NO_LIVE_AUTHORITY_ASSERTION_MISSING")
    if payload.get("paper_live_firewall_assertion") is not True:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PAPER_LIVE_FIREWALL_ASSERTION_MISSING")
    if payload.get("not_autonomous_live_trading_assertion") is not True:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_NOT_AUTONOMOUS_LIVE_TRADING_ASSERTION_MISSING")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_ARTIFACTS_NOT_LIST")
        artifacts = []
    for row in artifacts:
        if not isinstance(row, dict):
            blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_ARTIFACT_NOT_OBJECT")
            continue
        role = row.get("role")
        if not isinstance(role, str) or not role:
            blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_ARTIFACT_ROLE_MISSING")
            continue
        expected_path_value = row.get("expected_path")
        artifact_path = _repo_relative_or_absolute_path(expected_path_value)
        if artifact_path is None or not artifact_path.exists() or not artifact_path.is_file():
            blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_ARTIFACT_FILE_MISSING:{role}:{expected_path_value}")
            continue
        observed_sha = _file_sha256(artifact_path)
        if row.get("sha256") != observed_sha:
            blockers.append(
                f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_ARTIFACT_SHA256_MISMATCH:{role}:"
                f"{row.get('sha256')}:expected={observed_sha}"
            )
    payload_blockers = payload.get("blockers")
    if not isinstance(payload_blockers, list) or not all(isinstance(item, str) for item in payload_blockers):
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_BLOCKERS_INVALID")
        payload_blockers = []
    status = payload.get("status")
    if status not in {"PASS", "FAIL"}:
        blockers.append(f"FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_STATUS_UNEXPECTED:{status}")
    if status == "PASS" and payload_blockers:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PASS_HAS_BLOCKERS")
    if status == "PASS" and blockers:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PASS_HAS_VALIDATION_BLOCKERS")
    if status == "FAIL" and not payload_blockers:
        blockers.append("FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_FAIL_MISSING_BLOCKERS")
    return payload, blockers


def verify_final_research_paper_discovery_certification(
    final_certificate_doc_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_DOC_PATH,
    *,
    index_output_path: Path = FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PATH,
    verification_output_path: Path | None = None,
) -> dict[str, object]:
    index = write_final_research_paper_discovery_certification_index(
        final_certificate_doc_path=final_certificate_doc_path,
        output_path=index_output_path,
    )
    index_summary, index_blockers = validate_final_research_paper_discovery_certification_index(index_output_path)
    verification: dict[str, object] = {
        "schema_version": FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_VERIFICATION_SCHEMA_VERSION,
        "status": "PASS" if not index_blockers and index.get("status") == "PASS" else "FAIL",
        "blockers": index_blockers,
        "final_certificate_doc_path": str(final_certificate_doc_path),
        "final_certificate_doc_sha256": _file_sha256(final_certificate_doc_path) if final_certificate_doc_path.exists() else None,
        "certification_index_path": str(index_output_path),
        "certification_index_sha256": _file_sha256(index_output_path) if index_output_path.exists() else None,
        "certification_index": index_summary,
        "verified_at": _utc_now(),
    }
    if verification_output_path is not None:
        verification_output_path.parent.mkdir(parents=True, exist_ok=True)
        verification_output_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification


def build_research_paper_discovery_phase_run_report(
    *,
    local_certify_payload: dict[str, object],
    local_report_path: Path = REPORT_PATH,
    local_report_verification: dict[str, object] | None = None,
    local_report_verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
    phase_profile_plan_report: dict[str, object] | None = None,
    phase_profile_plan_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
    phase_profile_plan_verification: dict[str, object] | None = None,
    phase_profile_plan_verification_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
    phase_closure_report: dict[str, object] | None = None,
    phase_closure_path: Path = RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
    phase_evidence_bundle: dict[str, object] | None = None,
    phase_evidence_bundle_path: Path = RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
    phase_profile_blockers: Sequence[str] = (),
    output_path: Path = RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH,
) -> dict[str, object]:
    """Build the terminal operator-facing result for a full phase-profile run.

    This report intentionally sits above the plan, local certify report,
    closure report, and evidence bundle.  It is written for both PASS and FAIL
    outcomes so an early phase blocker leaves one terminal artifact with the
    exact failed step and next diagnostic.
    """
    blockers: list[str] = [str(blocker) for blocker in phase_profile_blockers]
    local_status = local_certify_payload.get("status")
    failed_step = local_certify_payload.get("failed_step")
    if local_status != "PASS":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_CERTIFY_NOT_PASSING:{local_status}")
    if isinstance(failed_step, str) and failed_step:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_FAILED_STEP:{failed_step}")
    if local_report_verification is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_REPORT_VERIFICATION_MISSING")
    elif local_report_verification.get("status") != "PASS":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_REPORT_VERIFICATION_NOT_PASSING:"
            f"{local_report_verification.get('status')}"
        )
        verification_blockers = local_report_verification.get("blockers")
        if isinstance(verification_blockers, list):
            blockers.extend(
                f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_LOCAL_REPORT_VERIFICATION_BLOCKER:{item}"
                for item in verification_blockers
                if isinstance(item, str)
            )
    if phase_profile_plan_report is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PROFILE_PLAN_MISSING")
    elif phase_profile_plan_report.get("status") != "PASS":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PROFILE_PLAN_NOT_PASSING:"
            f"{phase_profile_plan_report.get('status')}"
        )
    if phase_profile_plan_verification is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PROFILE_PLAN_VERIFICATION_MISSING")
    elif phase_profile_plan_verification.get("status") != "PASS":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PROFILE_PLAN_VERIFICATION_NOT_PASSING:"
            f"{phase_profile_plan_verification.get('status')}"
        )
        plan_verification_blockers = phase_profile_plan_verification.get("blockers")
        if isinstance(plan_verification_blockers, list):
            blockers.extend(
                f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PROFILE_PLAN_VERIFICATION_BLOCKER:{item}"
                for item in plan_verification_blockers
                if isinstance(item, str)
            )
    if phase_closure_report is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_CLOSURE_REPORT_MISSING")
    elif phase_closure_report.get("status") != "PASS":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_CLOSURE_NOT_PASSING:"
            f"{phase_closure_report.get('status')}"
        )
    if phase_evidence_bundle is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_EVIDENCE_BUNDLE_MISSING")
    elif phase_evidence_bundle.get("status") != "PASS":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_EVIDENCE_BUNDLE_NOT_PASSING:"
            f"{phase_evidence_bundle.get('status')}"
        )

    ordered_blockers = list(dict.fromkeys(blockers))
    next_diagnostic = local_certify_payload.get("next_diagnostic")
    if not isinstance(next_diagnostic, str) or not next_diagnostic:
        if failed_step == "frontend_preflight":
            next_diagnostic = "inspect frontend_preflight_report.json and research_paper_discovery_profile_plan.json"
        elif ordered_blockers:
            next_diagnostic = "inspect research_paper_discovery_phase_run_report.json blockers, then replay plan/report/closure/bundle verification commands"
        else:
            next_diagnostic = None
    payload: dict[str, object] = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_SCHEMA_VERSION,
        "status": "PASS" if not ordered_blockers else "FAIL",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile": local_certify_payload.get("certification_profile"),
        "local_certify_status": local_status,
        "local_certify_failed_step": failed_step,
        "timeout_seconds": local_certify_payload.get("timeout_seconds"),
        "next_diagnostic": next_diagnostic,
        "blocker_count": len(ordered_blockers),
        "blockers": ordered_blockers,
        "phase_profile_blockers": list(phase_profile_blockers),
        "local_certify_report": _json_artifact_status(local_report_path),
        "local_certify_report_verification": _json_artifact_status(local_report_verification_path),
        "phase_profile_plan": _json_artifact_status(phase_profile_plan_path),
        "phase_profile_plan_verification": _json_artifact_status(phase_profile_plan_verification_path),
        "phase_closure_report": _json_artifact_status(phase_closure_path),
        "phase_evidence_bundle": _json_artifact_status(phase_evidence_bundle_path),
        "frontend_preflight_report": local_certify_payload.get("frontend_preflight_report"),
        "frontend_clean_workspace_report": local_certify_payload.get("frontend_clean_workspace_report"),
        "frontend_certify_report": local_certify_payload.get("frontend_certify_report"),
        "python_core_report": local_certify_payload.get("python_core_report"),
        "researcher_fixture_report": local_certify_payload.get("researcher_fixture_report"),
        "collection_shards_proof": local_certify_payload.get("collection_shards_proof"),
        "constitutional_shards_proof": local_certify_payload.get("constitutional_shards_proof"),
        "pytest_execution_shards_proof": local_certify_payload.get("pytest_execution_shards_proof"),
        "no_live_authority_assertion": (
            phase_closure_report.get("no_live_authority_assertion") if isinstance(phase_closure_report, dict) else None
        ),
        "paper_live_firewall_assertion": (
            phase_closure_report.get("paper_live_firewall_assertion") if isinstance(phase_closure_report, dict) else None
        ),
        "source_tree_digest": _python_core_source_tree_digest(),
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "generated_at": _utc_now(),
        "repo_root": str(REPO_ROOT),
        "output_path": str(output_path),
    }
    payload["run_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "run_payload_sha256"})
    return payload


def write_research_paper_discovery_phase_run_report(
    *,
    local_certify_payload: dict[str, object],
    local_report_path: Path = REPORT_PATH,
    local_report_verification: dict[str, object] | None = None,
    local_report_verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
    phase_profile_plan_report: dict[str, object] | None = None,
    phase_profile_plan_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
    phase_profile_plan_verification: dict[str, object] | None = None,
    phase_profile_plan_verification_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
    phase_closure_report: dict[str, object] | None = None,
    phase_closure_path: Path = RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
    phase_evidence_bundle: dict[str, object] | None = None,
    phase_evidence_bundle_path: Path = RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
    phase_profile_blockers: Sequence[str] = (),
    output_path: Path = RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH,
) -> dict[str, object]:
    payload = build_research_paper_discovery_phase_run_report(
        local_certify_payload=local_certify_payload,
        local_report_path=local_report_path,
        local_report_verification=local_report_verification,
        local_report_verification_path=local_report_verification_path,
        phase_profile_plan_report=phase_profile_plan_report,
        phase_profile_plan_path=phase_profile_plan_path,
        phase_profile_plan_verification=phase_profile_plan_verification,
        phase_profile_plan_verification_path=phase_profile_plan_verification_path,
        phase_closure_report=phase_closure_report,
        phase_closure_path=phase_closure_path,
        phase_evidence_bundle=phase_evidence_bundle,
        phase_evidence_bundle_path=phase_evidence_bundle_path,
        phase_profile_blockers=phase_profile_blockers,
        output_path=output_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_research_paper_discovery_phase_run_report(
    path: Path = RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH,
) -> tuple[dict[str, object] | None, list[str]]:
    payload, blockers = _load_json_object(path, blocker_prefix="RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT")
    if payload is None:
        return None, blockers
    if payload.get("schema_version") != RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_SCHEMA_VERSION:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PHASE_UNEXPECTED:{payload.get('phase')}")
    if payload.get("certification_profile") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_CERTIFICATION_PROFILE_UNEXPECTED:"
            f"{payload.get('certification_profile')}"
        )
    embedded_blockers = payload.get("blockers")
    if not isinstance(embedded_blockers, list) or not all(isinstance(item, str) for item in embedded_blockers):
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_BLOCKERS_INVALID")
        embedded_blockers = []
    if payload.get("blocker_count") != len(embedded_blockers):
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_BLOCKER_COUNT_MISMATCH:"
            f"{payload.get('blocker_count')}:expected={len(embedded_blockers)}"
        )
    if payload.get("status") == "PASS" and embedded_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PASS_WITH_BLOCKERS")
    if payload.get("status") == "FAIL" and not embedded_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_PHASE_RUN_FAIL_WITHOUT_BLOCKERS")
    observed_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "run_payload_sha256"})
    if payload.get("run_payload_sha256") != observed_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_PAYLOAD_DIGEST_MISMATCH:"
            f"{payload.get('run_payload_sha256')}:expected={observed_digest}"
        )
    if payload.get("source_tree_digest") != _python_core_source_tree_digest():
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_SOURCE_TREE_MISMATCH:"
            f"{payload.get('source_tree_digest')}:expected={_python_core_source_tree_digest()}"
        )
    if payload.get("frontend_source_tree_digest") != _frontend_source_tree_digest():
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_PHASE_RUN_FRONTEND_SOURCE_TREE_MISMATCH:"
            f"{payload.get('frontend_source_tree_digest')}:expected={_frontend_source_tree_digest()}"
        )
    for key in (
        "local_certify_report",
        "local_certify_report_verification",
        "phase_profile_plan",
        "phase_profile_plan_verification",
        "phase_closure_report",
        "phase_evidence_bundle",
    ):
        row = payload.get(key)
        if not isinstance(row, dict):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_ARTIFACT_ROW_MISSING:{key}")
            continue
        row_path = row.get("path")
        row_sha = row.get("sha256")
        if not isinstance(row_path, str):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_ARTIFACT_PATH_MISSING:{key}")
            continue
        artifact_path = Path(row_path)
        if row.get("present") is True:
            if not artifact_path.exists():
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_ARTIFACT_FILE_MISSING:{key}:{row_path}")
                continue
            observed_sha = _file_sha256(artifact_path)
            if row_sha != observed_sha:
                blockers.append(
                    f"RESEARCH_PAPER_DISCOVERY_PHASE_RUN_ARTIFACT_SHA256_MISMATCH:{key}:{row_sha}:expected={observed_sha}"
                )
    summary = {
        "proof_name": "research_paper_discovery_phase_run_report",
        "path": str(path),
        "sha256": _file_sha256(path),
        "schema_version": payload.get("schema_version"),
        "status": "PASS" if not blockers and payload.get("status") == "PASS" else "FAIL",
        "source_tree_digest": payload.get("source_tree_digest"),
        "created_at": payload.get("generated_at"),
        "verified_at": _utc_now(),
        "blocker_count": len(blockers),
    }
    return summary, blockers

def _verify_research_paper_discovery_profile_contract(payload: dict[str, object], blockers: list[str]) -> None:
    if payload.get("certification_profile") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        return
    contract = payload.get("certification_profile_contract")
    if not isinstance(contract, dict):
        blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_CONTRACT_MISSING")
        return
    if contract.get("schema_version") != RESEARCH_PAPER_DISCOVERY_PROFILE_VERSION:
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_SCHEMA_UNEXPECTED:"
            f"{contract.get('schema_version')}"
        )
    if contract.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PHASE_UNEXPECTED:"
            f"{contract.get('phase')}"
        )
    expected_flags = {
        "frontend_included": True,
        "frontend_clean_workspace_included": True,
        "collection_shards_included": True,
        "constitutional_shards_included": True,
        "pytest_execution_shards_included": True,
        "researcher_fixture_included": True,
        "pytest_execution_shards_replace_monolith": True,
    }
    if contract.get("frontend_required") is not True:
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FRONTEND_REQUIRED_FALSE"
        )
    if contract.get("frontend_skip_allowed") is not False:
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FRONTEND_SKIP_ALLOWED"
        )
    frontend_preflight = payload.get("frontend_preflight_report")
    if not isinstance(frontend_preflight, dict):
        blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FRONTEND_PREFLIGHT_REPORT_MISSING")
    elif frontend_preflight.get("status") != "PASS":
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FRONTEND_PREFLIGHT_NOT_PASSING:"
            f"{frontend_preflight.get('status')}"
        )
    phase_profile_plan = payload.get("phase_profile_plan_report")
    if not isinstance(phase_profile_plan, dict):
        blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_REPORT_MISSING")
    elif phase_profile_plan.get("status") != "PASS":
        blockers.append(
            "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_NOT_PASSING:"
            f"{phase_profile_plan.get('status')}"
        )
    else:
        plan_path_value = phase_profile_plan.get("path")
        if not isinstance(plan_path_value, str):
            blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH_MISSING")
        else:
            plan_path = Path(plan_path_value)
            if not plan_path.exists():
                blockers.append(f"LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_FILE_MISSING:{plan_path}")
            else:
                observed_plan_sha = _file_sha256(plan_path)
                if phase_profile_plan.get("sha256") != observed_plan_sha:
                    blockers.append(
                        "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_SHA256_MISMATCH:"
                        f"{phase_profile_plan.get('sha256')}:expected={observed_plan_sha}"
                    )
                _plan_summary, plan_blockers = validate_research_paper_discovery_profile_plan(plan_path)
                if plan_blockers:
                    blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_CURRENT_VALIDATION_FAILED:" + ";".join(plan_blockers))
    for field, expected in expected_flags.items():
        if payload.get(field) is not expected:
            blockers.append(
                "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_FLAG_MISMATCH:"
                f"{field}={payload.get(field)}:expected={expected}"
            )
    required_proofs = contract.get("required_proofs")
    if not isinstance(required_proofs, list) or not all(isinstance(item, str) for item in required_proofs):
        blockers.append("LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_REQUIRED_PROOFS_INVALID")
        return
    for proof_name in required_proofs:
        proof = payload.get(proof_name)
        if not isinstance(proof, dict):
            blockers.append(f"LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_MISSING:{proof_name}")
            continue
        if proof.get("status") != "PASS":
            blockers.append(
                "LOCAL_CERTIFY_RESEARCH_PAPER_DISCOVERY_PROFILE_PROOF_NOT_PASSING:"
                f"{proof_name}:{proof.get('status')}"
            )


def _node_version() -> str | None:
    if shutil.which("node") is None:
        return None
    try:
        result = subprocess.run(["node", "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return None
    return result.stdout.strip() or None


def _build_payload(
    *,
    results: list[LocalCertifyStep],
    failed: LocalCertifyStep | None,
    frontend_included: bool,
    frontend_clean_workspace_included: bool = False,
    researcher_fixture_included: bool = False,
    collection_shards_included: bool = False,
    collection_shard_count: int | None = None,
    constitutional_shards_included: bool = False,
    constitutional_shard_count: int | None = None,
    pytest_execution_shards_included: bool = False,
    pytest_shard_count: int | None = None,
    monolithic_pytest_included: bool = True,
    pytest_execution_shards_replace_monolith: bool = False,
    frontend_certify_report: dict[str, object] | None = None,
    frontend_clean_workspace_report: dict[str, object] | None = None,
    frontend_preflight_report: dict[str, object] | None = None,
    phase_profile_plan_report: dict[str, object] | None = None,
    python_core_report: dict[str, object] | None = None,
    public_surface_dashboard: dict[str, object] | None = None,
    package_repo_check: dict[str, object] | None = None,
    researcher_fixture_report: dict[str, object] | None = None,
    collection_shards_proof: dict[str, object] | None = None,
    constitutional_shards_proof: dict[str, object] | None = None,
    pytest_execution_shards_proof: dict[str, object] | None = None,
    certification_profile: str | None = None,
    certification_profile_contract: dict[str, object] | None = None,
) -> dict[str, object]:
    steps = [step.to_payload() for step in results]
    status = "PASS" if failed is None else "TIMEOUT" if failed.timed_out else "FAIL"
    payload: dict[str, object] = {
        "schema_version": LOCAL_CERTIFY_SCHEMA_VERSION,
        "status": status,
        "failed_step": None if failed is None else failed.name,
        "frontend_included": frontend_included,
        "frontend_clean_workspace_included": frontend_clean_workspace_included,
        "researcher_fixture_included": researcher_fixture_included,
        "collection_shards_included": collection_shards_included,
        "collection_shard_count": collection_shard_count,
        "constitutional_shards_included": constitutional_shards_included,
        "constitutional_shard_count": constitutional_shard_count,
        "pytest_execution_shards_included": pytest_execution_shards_included,
        "pytest_shard_count": pytest_shard_count,
        "monolithic_pytest_included": monolithic_pytest_included,
        "pytest_execution_shards_replace_monolith": pytest_execution_shards_replace_monolith,
        "timeout_seconds": None if failed is None else failed.timeout_seconds,
        "next_diagnostic": _next_diagnostic_for_failed_step(failed) if failed is not None else None,
        "frontend_certify_report": frontend_certify_report,
        "frontend_clean_workspace_report": frontend_clean_workspace_report,
        "frontend_preflight_report": frontend_preflight_report,
        "phase_profile_plan_report": phase_profile_plan_report,
        "python_core_report": python_core_report,
        "public_surface_dashboard": public_surface_dashboard,
        "package_repo_check": package_repo_check,
        "researcher_fixture_report": researcher_fixture_report,
        "collection_shards_proof": collection_shards_proof,
        "constitutional_shards_proof": constitutional_shards_proof,
        "pytest_execution_shards_proof": pytest_execution_shards_proof,
        "certification_profile": certification_profile,
        "certification_profile_contract": certification_profile_contract,
        "python_version": platform.python_version(),
        "node_version": _node_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "report_path": str(REPORT_PATH),
        "steps": steps,
    }
    payload["step_manifest_sha256"] = _step_manifest_digest(steps)
    payload["report_payload_sha256"] = local_certify_payload_digest(payload)
    return payload


def _next_diagnostic_for_failed_step(step: LocalCertifyStep) -> str | None:
    if not step.timed_out:
        return None
    if step.name == "pytest":
        return "run --include-collection-shards, --include-constitutional-shards, or --include-pytest-shards"
    if step.name.startswith("constitutional_shard_"):
        return "inspect the matching constitutional shard report under artifacts/certification_stability/latest"
    if step.name.startswith("collection_shard_"):
        return "inspect the matching collection shard report under artifacts/certification_stability/latest"
    if step.name.startswith("pytest_execution_shard_"):
        return "inspect the matching pytest execution shard report under artifacts/certification_stability/latest"
    return "inspect stdout_tail and stderr_tail for the timed-out step"


def _is_resumable_proof_step(name: str) -> bool:
    """Return true for optional shard proof commands whose failure is aggregated later.

    A shard step may fail because pytest found failures or because its inner
    watchdog timed out.  Local certification should still run the remaining
    shards plus the summary/verification commands so the final report contains
    a complete blocker set instead of stopping at the first nonzero shard.
    """
    return (
        name.startswith("collection_shard_")
        or name.startswith("constitutional_shard_")
        or name.startswith("pytest_execution_shard_")
        or name
        in {
            "collection_shards_summary",
            "collection_shards_summary_verification",
            "constitutional_shards_summary",
            "constitutional_shards_summary_verification",
            "pytest_execution_shards_summary",
            "pytest_execution_shards_summary_verification",
        }
    )


def _local_wrapper_timeout_for_step(name: str, args: argparse.Namespace) -> int | None:
    """Choose the outer local-certify watchdog for a step.

    Shard commands already pass their own per-shard timeout into
    certification_stability.py.  The outer watchdog gets a small grace window
    so a broken driver process cannot hang local certification after the inner
    watchdog should have completed.
    """
    if name.startswith("collection_shard_"):
        return int(args.collection_shard_timeout_seconds) + 60
    if name.startswith("constitutional_shard_"):
        return int(args.constitutional_shard_timeout_seconds) + 60
    if name.startswith("pytest_execution_shard_"):
        return int(args.pytest_shard_timeout_seconds) + 60
    if name.endswith("_shards_summary") or name.endswith("_shards_summary_verification"):
        if args.step_timeout_seconds is None:
            return 300
        return min(int(args.step_timeout_seconds), 300)
    if name == "researcher_fixture":
        return int(args.researcher_fixture_timeout_seconds) * 2 + 60
    if name in LOCAL_CERTIFY_BASE_REQUIRED_STEPS or name.startswith("frontend_"):
        return None if args.step_timeout_seconds is None else int(args.step_timeout_seconds)
    return None


def _verify_embedded_shard_proof(
    payload: dict[str, object],
    *,
    field_name: str,
    included_flag: str,
    blocker_prefix: str,
    blockers: list[str],
) -> dict[str, object] | None:
    """Verify an embedded resumable proof summary still points to current artifacts."""
    if payload.get(included_flag) is not True:
        return None
    proof = payload.get(field_name)
    if not isinstance(proof, dict):
        blockers.append(f"{blocker_prefix}_SUMMARY_MISSING")
        return None
    summary_path_value = proof.get("summary_path")
    verification_path_value = proof.get("verification_path")
    if not isinstance(summary_path_value, str):
        blockers.append(f"{blocker_prefix}_SUMMARY_PATH_MISSING")
    if not isinstance(verification_path_value, str):
        blockers.append(f"{blocker_prefix}_VERIFICATION_PATH_MISSING")
    required_fields = (
        "path",
        "sha256",
        "schema_version",
        "status",
        "source_tree_digest",
        "created_at",
        "verified_at",
        "summary_path",
        "summary_sha256",
        "summary_schema_version",
        "verification_path",
        "verification_sha256",
        "verification_schema_version",
    )
    for field in required_fields:
        if proof.get(field) in {None, ""}:
            blockers.append(f"{blocker_prefix}_FIELD_MISSING:{field}")
    if proof.get("status") != "PASS":
        blockers.append(f"{blocker_prefix}_NOT_PASSING:{proof.get('status')}")
    if proof.get("summary_status") != "PASS":
        blockers.append(f"{blocker_prefix}_SUMMARY_NOT_PASSING:{proof.get('summary_status')}")
    if proof.get("verification_status") != "PASS":
        blockers.append(f"{blocker_prefix}_VERIFICATION_NOT_PASSING:{proof.get('verification_status')}")
    if proof.get("path") != summary_path_value:
        blockers.append(f"{blocker_prefix}_PATH_ALIAS_MISMATCH:{proof.get('path')}:expected={summary_path_value}")
    if proof.get("sha256") != proof.get("summary_sha256"):
        blockers.append(f"{blocker_prefix}_SHA256_ALIAS_MISMATCH:{proof.get('sha256')}:expected={proof.get('summary_sha256')}")
    if proof.get("schema_version") != proof.get("summary_schema_version"):
        blockers.append(f"{blocker_prefix}_SCHEMA_ALIAS_MISMATCH:{proof.get('schema_version')}:expected={proof.get('summary_schema_version')}")
    current_source_digest = _expected_current_digest_for_embedded_proof(field_name)
    if current_source_digest is not None and proof.get("source_tree_digest") != current_source_digest:
        blockers.append(f"{blocker_prefix}_SOURCE_TREE_MISMATCH:{proof.get('source_tree_digest')}:expected={current_source_digest}")

    if isinstance(summary_path_value, str):
        summary_path = Path(summary_path_value)
        if not summary_path.exists():
            blockers.append(f"{blocker_prefix}_SUMMARY_FILE_MISSING:{summary_path}")
        else:
            observed = _file_sha256(summary_path)
            if proof.get("summary_sha256") != observed:
                blockers.append(f"{blocker_prefix}_SUMMARY_SHA256_MISMATCH:{proof.get('summary_sha256')}:expected={observed}")
    if isinstance(verification_path_value, str):
        verification_path = Path(verification_path_value)
        if not verification_path.exists():
            blockers.append(f"{blocker_prefix}_VERIFICATION_FILE_MISSING:{verification_path}")
        else:
            observed = _file_sha256(verification_path)
            if proof.get("verification_sha256") != observed:
                blockers.append(f"{blocker_prefix}_VERIFICATION_SHA256_MISMATCH:{proof.get('verification_sha256')}:expected={observed}")
    return proof


def verify_local_certify_report(
    report_path: Path = REPORT_PATH,
    *,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Verify a persisted local-certify report as a tamper-evident proof artifact."""
    blockers: list[str] = []
    payload: dict[str, object] | None = None
    if not report_path.exists():
        blockers.append(f"LOCAL_CERTIFY_REPORT_MISSING:{report_path}")
    else:
        try:
            loaded = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                blockers.append("LOCAL_CERTIFY_REPORT_NOT_OBJECT")
            else:
                payload = loaded
        except json.JSONDecodeError as exc:
            blockers.append(f"LOCAL_CERTIFY_REPORT_INVALID_JSON:{exc}")

    declared_digest: object | None = None
    observed_digest: str | None = None
    step_names: list[str] = []
    expected_step_names: list[str] = []
    missing_step_names: list[str] = []
    unexpected_step_names: list[str] = []
    duplicate_step_names: list[str] = []
    nonzero_steps: list[str] = []
    frontend_report_summary: dict[str, object] | None = None
    frontend_clean_workspace_report_summary: dict[str, object] | None = None
    python_core_report_summary: dict[str, object] | None = None
    public_surface_dashboard_summary: dict[str, object] | None = None
    package_repo_check_summary: dict[str, object] | None = None
    researcher_fixture_report_summary: dict[str, object] | None = None
    collection_shards_proof_summary: dict[str, object] | None = None
    constitutional_shards_proof_summary: dict[str, object] | None = None
    pytest_execution_shards_proof_summary: dict[str, object] | None = None
    phase_profile_plan_report_summary: dict[str, object] | None = None

    if payload is not None:
        schema_version = payload.get("schema_version")
        if schema_version != LOCAL_CERTIFY_SCHEMA_VERSION:
            blockers.append(f"LOCAL_CERTIFY_REPORT_SCHEMA_UNEXPECTED:{schema_version}")
        if payload.get("repo_root") != str(REPO_ROOT):
            blockers.append(f"LOCAL_CERTIFY_REPORT_REPO_ROOT_MISMATCH:{payload.get('repo_root')}:expected={REPO_ROOT}")
        declared_digest = payload.get("report_payload_sha256")
        observed_digest = local_certify_payload_digest(payload)
        if declared_digest != observed_digest:
            blockers.append(f"LOCAL_CERTIFY_REPORT_PAYLOAD_DIGEST_MISMATCH:{declared_digest}:expected={observed_digest}")
        _verify_research_paper_discovery_profile_contract(payload, blockers)

        steps = payload.get("steps")
        if not isinstance(steps, list):
            blockers.append("LOCAL_CERTIFY_REPORT_STEPS_NOT_LIST")
            steps = []
        for step in steps:
            if not isinstance(step, dict):
                blockers.append("LOCAL_CERTIFY_REPORT_STEP_NOT_OBJECT")
                continue
            name = step.get("name")
            if isinstance(name, str):
                step_names.append(name)
            exit_code = step.get("exit_code")
            timed_out = step.get("timed_out")
            if (exit_code != 0 or timed_out is True) and isinstance(name, str):
                suffix = ":TIMEOUT" if timed_out is True else f":{exit_code}"
                nonzero_steps.append(f"{name}{suffix}")
        expected_step_names = _expected_local_certify_step_names(payload)
        missing_step_names = [name for name in expected_step_names if name not in step_names]
        unexpected_step_names = [name for name in step_names if name not in expected_step_names]
        duplicate_step_names = sorted({name for name in step_names if step_names.count(name) > 1})
        if missing_step_names:
            blockers.append("LOCAL_CERTIFY_REPORT_REQUIRED_STEPS_MISSING:" + ",".join(missing_step_names))
        if unexpected_step_names:
            blockers.append("LOCAL_CERTIFY_REPORT_UNEXPECTED_STEPS:" + ",".join(unexpected_step_names))
        if duplicate_step_names:
            blockers.append("LOCAL_CERTIFY_REPORT_DUPLICATE_STEPS:" + ",".join(duplicate_step_names))
        declared_step_manifest = payload.get("step_manifest_sha256")
        observed_step_manifest = _step_manifest_digest(steps)
        if declared_step_manifest != observed_step_manifest:
            blockers.append(f"LOCAL_CERTIFY_REPORT_STEP_MANIFEST_MISMATCH:{declared_step_manifest}:expected={observed_step_manifest}")

        status = payload.get("status")
        failed_step = payload.get("failed_step")
        if status not in {"PASS", "FAIL", "TIMEOUT"}:
            blockers.append(f"LOCAL_CERTIFY_REPORT_STATUS_UNEXPECTED:{status}")
        if status == "PASS" and failed_step is not None:
            blockers.append(f"LOCAL_CERTIFY_REPORT_PASS_HAS_FAILED_STEP:{failed_step}")
        if status == "PASS" and nonzero_steps:
            blockers.append("LOCAL_CERTIFY_REPORT_PASS_HAS_NONZERO_STEPS:" + ",".join(nonzero_steps))
        if status in {"FAIL", "TIMEOUT"} and not failed_step:
            blockers.append(f"LOCAL_CERTIFY_REPORT_{status}_MISSING_FAILED_STEP")
        if status == "TIMEOUT":
            timeout_seconds = payload.get("timeout_seconds")
            if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
                blockers.append(f"LOCAL_CERTIFY_REPORT_TIMEOUT_SECONDS_INVALID:{timeout_seconds}")
            if not payload.get("next_diagnostic"):
                blockers.append("LOCAL_CERTIFY_REPORT_TIMEOUT_MISSING_NEXT_DIAGNOSTIC")

        if payload.get("frontend_included") is True:
            frontend_report = payload.get("frontend_certify_report")
            if not isinstance(frontend_report, dict):
                blockers.append("LOCAL_CERTIFY_FRONTEND_REPORT_SUMMARY_MISSING")
            else:
                frontend_report_summary = frontend_report
                frontend_path_value = frontend_report.get("path")
                frontend_declared_sha = frontend_report.get("sha256")
                if not isinstance(frontend_path_value, str):
                    blockers.append("LOCAL_CERTIFY_FRONTEND_REPORT_PATH_MISSING")
                else:
                    frontend_path = Path(frontend_path_value)
                    if not frontend_path.exists():
                        blockers.append(f"LOCAL_CERTIFY_FRONTEND_REPORT_FILE_MISSING:{frontend_path}")
                    else:
                        observed_frontend_sha = _file_sha256(frontend_path)
                        if frontend_declared_sha != observed_frontend_sha:
                            blockers.append(
                                f"LOCAL_CERTIFY_FRONTEND_REPORT_SHA256_MISMATCH:{frontend_declared_sha}:expected={observed_frontend_sha}"
                            )
                for field in ("path", "sha256", "schema_version", "status", "source_tree_digest", "created_at", "verified_at"):
                    if frontend_report.get(field) in {None, ""}:
                        blockers.append(f"LOCAL_CERTIFY_FRONTEND_REPORT_FIELD_MISSING:{field}")
                if frontend_report.get("proof_name") not in {None, "frontend_certify_report"}:
                    blockers.append(f"LOCAL_CERTIFY_FRONTEND_REPORT_PROOF_NAME_UNEXPECTED:{frontend_report.get('proof_name')}")
                if frontend_report.get("status") != "PASS":
                    blockers.append(f"LOCAL_CERTIFY_FRONTEND_REPORT_NOT_PASSING:{frontend_report.get('status')}")
                current_frontend_digest = _expected_current_digest_for_embedded_proof("frontend_certify_report")
                if current_frontend_digest is not None and frontend_report.get("source_tree_digest") != current_frontend_digest:
                    blockers.append(
                        "LOCAL_CERTIFY_FRONTEND_REPORT_SOURCE_TREE_MISMATCH:"
                        f"{frontend_report.get('source_tree_digest')}:expected={current_frontend_digest}"
                    )

        for field_name, blocker_prefix, target in (
            ("frontend_clean_workspace_report", "LOCAL_CERTIFY_FRONTEND_CLEAN_WORKSPACE_REPORT", "frontend_clean_workspace_report"),
            ("python_core_report", "LOCAL_CERTIFY_PYTHON_CORE_REPORT", "python_core_report"),
            ("public_surface_dashboard", "LOCAL_CERTIFY_PUBLIC_SURFACE_DASHBOARD", "public_surface_dashboard"),
            ("package_repo_check", "LOCAL_CERTIFY_PACKAGE_REPO_CHECK", "package_repo_check"),
            ("researcher_fixture_report", "LOCAL_CERTIFY_RESEARCHER_FIXTURE_REPORT", "researcher_fixture_report"),
        ):
            if field_name == "frontend_clean_workspace_report" and payload.get("frontend_clean_workspace_included") is not True:
                continue
            if field_name == "researcher_fixture_report" and payload.get("researcher_fixture_included") is not True:
                continue
            proof = payload.get(field_name)
            if not isinstance(proof, dict):
                blockers.append(f"{blocker_prefix}_SUMMARY_MISSING")
                continue
            if field_name == "frontend_clean_workspace_report":
                frontend_clean_workspace_report_summary = proof
            elif field_name == "python_core_report":
                python_core_report_summary = proof
            elif field_name == "public_surface_dashboard":
                public_surface_dashboard_summary = proof
            elif field_name == "package_repo_check":
                package_repo_check_summary = proof
            else:
                researcher_fixture_report_summary = proof
            for required_field in ("path", "sha256", "schema_version", "status", "source_tree_digest", "created_at", "verified_at"):
                if proof.get(required_field) in {None, ""}:
                    blockers.append(f"{blocker_prefix}_FIELD_MISSING:{required_field}")
            if proof.get("proof_name") != target:
                blockers.append(f"{blocker_prefix}_PROOF_NAME_UNEXPECTED:{proof.get('proof_name')}")
            if proof.get("status") != "PASS":
                blockers.append(f"{blocker_prefix}_NOT_PASSING:{proof.get('status')}")
            proof_path_value = proof.get("path")
            if not isinstance(proof_path_value, str):
                blockers.append(f"{blocker_prefix}_PATH_MISSING")
            else:
                proof_path = Path(proof_path_value)
                if not proof_path.exists():
                    blockers.append(f"{blocker_prefix}_FILE_MISSING:{proof_path}")
                else:
                    observed = _file_sha256(proof_path)
                    if proof.get("sha256") != observed:
                        blockers.append(f"{blocker_prefix}_SHA256_MISMATCH:{proof.get('sha256')}:expected={observed}")
                    validator_summary: dict[str, object] | None = None
                    validator_blockers: list[str] = []
                    if field_name == "frontend_clean_workspace_report":
                        validator_summary, validator_blockers = validate_frontend_clean_workspace_report(proof_path)
                    elif field_name == "python_core_report":
                        validator_summary, validator_blockers = validate_python_core_report(proof_path)
                    elif field_name == "public_surface_dashboard":
                        validator_summary, validator_blockers = validate_public_surface_dashboard_report(proof_path)
                    elif field_name == "package_repo_check":
                        validator_summary, validator_blockers = validate_package_repo_check_report(proof_path)
                    elif field_name == "researcher_fixture_report":
                        validator_summary, validator_blockers = validate_researcher_fixture_report(proof_path)
                    if validator_blockers:
                        blockers.append(f"{blocker_prefix}_CURRENT_VALIDATION_FAILED:" + ";".join(validator_blockers))
                    if validator_summary is not None:
                        current_digest = validator_summary.get("source_tree_digest")
                        if proof.get("source_tree_digest") != current_digest:
                            blockers.append(
                                f"{blocker_prefix}_SOURCE_TREE_MISMATCH:{proof.get('source_tree_digest')}:expected={current_digest}"
                            )

        collection_shards_proof_summary = _verify_embedded_shard_proof(
            payload,
            field_name="collection_shards_proof",
            included_flag="collection_shards_included",
            blocker_prefix="LOCAL_CERTIFY_COLLECTION_SHARDS_PROOF",
            blockers=blockers,
        )
        constitutional_shards_proof_summary = _verify_embedded_shard_proof(
            payload,
            field_name="constitutional_shards_proof",
            included_flag="constitutional_shards_included",
            blocker_prefix="LOCAL_CERTIFY_CONSTITUTIONAL_SHARDS_PROOF",
            blockers=blockers,
        )
        pytest_execution_shards_proof_summary = _verify_embedded_shard_proof(
            payload,
            field_name="pytest_execution_shards_proof",
            included_flag="pytest_execution_shards_included",
            blocker_prefix="LOCAL_CERTIFY_PYTEST_EXECUTION_SHARDS_PROOF",
            blockers=blockers,
        )
        phase_plan = payload.get("phase_profile_plan_report")
        if isinstance(phase_plan, dict):
            phase_profile_plan_report_summary = phase_plan

    verification: dict[str, object] = {
        "schema_version": LOCAL_CERTIFY_VERIFICATION_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "report_path": str(report_path),
        "report_sha256": _file_sha256(report_path) if report_path.exists() else None,
        "declared_report_payload_sha256": declared_digest,
        "observed_report_payload_sha256": observed_digest,
        "repo_root": str(REPO_ROOT),
        "step_count": len(step_names),
        "step_names": step_names,
        "expected_step_names": expected_step_names,
        "missing_step_names": missing_step_names,
        "unexpected_step_names": unexpected_step_names,
        "duplicate_step_names": duplicate_step_names,
        "nonzero_steps": nonzero_steps,
        "frontend_certify_report": frontend_report_summary,
        "frontend_clean_workspace_report": frontend_clean_workspace_report_summary,
        "python_core_report": python_core_report_summary,
        "public_surface_dashboard": public_surface_dashboard_summary,
        "package_repo_check": package_repo_check_summary,
        "researcher_fixture_report": researcher_fixture_report_summary,
        "collection_shards_proof": collection_shards_proof_summary,
        "constitutional_shards_proof": constitutional_shards_proof_summary,
        "pytest_execution_shards_proof": pytest_execution_shards_proof_summary,
        "phase_profile_plan_report": phase_profile_plan_report_summary,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification


def _proof_summary_rows_for_profile(payload: dict[str, object]) -> list[dict[str, object]]:
    contract = payload.get("certification_profile_contract")
    required_proofs: list[str] = []
    if isinstance(contract, dict) and isinstance(contract.get("required_proofs"), list):
        required_proofs = [item for item in contract["required_proofs"] if isinstance(item, str)]
    rows: list[dict[str, object]] = []
    for proof_name in required_proofs:
        proof = payload.get(proof_name)
        row: dict[str, object] = {
            "proof_name": proof_name,
            "present": isinstance(proof, dict),
            "status": None,
            "schema_version": None,
            "path": None,
            "sha256": None,
            "source_tree_digest": None,
            "summary_status": None,
            "verification_status": None,
        }
        if isinstance(proof, dict):
            row.update(
                {
                    "status": proof.get("status"),
                    "schema_version": proof.get("schema_version"),
                    "path": proof.get("path"),
                    "sha256": proof.get("sha256"),
                    "source_tree_digest": proof.get("source_tree_digest"),
                    "summary_status": proof.get("summary_status"),
                    "verification_status": proof.get("verification_status"),
                }
            )
        rows.append(row)
    return rows


def build_research_paper_discovery_closure_report(
    payload: dict[str, object],
    verification: dict[str, object],
    *,
    report_path: Path = REPORT_PATH,
    verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
) -> dict[str, object]:
    """Build the terminal phase-closure artifact for the current certification profile."""
    blockers: list[str] = []
    if payload.get("certification_profile") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_PROFILE_MISSING:"
            f"{payload.get('certification_profile')}"
        )
    _verify_research_paper_discovery_profile_contract(payload, blockers)
    if payload.get("status") != "PASS":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_NOT_PASSING:{payload.get('status')}")
    verification_blockers = verification.get("blockers") if isinstance(verification.get("blockers"), list) else []
    if verification.get("status") != "PASS":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_VERIFICATION_NOT_PASSING:{verification.get('status')}")
    for blocker in verification_blockers:
        if isinstance(blocker, str):
            blockers.append(f"LOCAL_CERTIFY_VERIFICATION:{blocker}")
    proof_rows = _proof_summary_rows_for_profile(payload)
    for row in proof_rows:
        proof_name = row["proof_name"]
        if row["present"] is not True:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_MISSING:{proof_name}")
            continue
        if row.get("status") != "PASS":
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_NOT_PASSING:{proof_name}:{row.get('status')}")
    failed_proofs = [str(row["proof_name"]) for row in proof_rows if row.get("status") != "PASS"]
    first_blocker = blockers[0] if blockers else None
    next_diagnostic = None
    if first_blocker is not None:
        if failed_proofs:
            next_diagnostic = f"inspect required proof(s): {', '.join(failed_proofs)}"
        elif payload.get("failed_step"):
            next_diagnostic = f"inspect failed local-certify step: {payload.get('failed_step')}"
        else:
            next_diagnostic = "run local_certify.py --verify-report against the referenced report and inspect blockers"
    report_sha256 = _file_sha256(report_path) if report_path.exists() else None
    verification_sha256 = _file_sha256(verification_path) if verification_path.exists() else None
    return {
        "schema_version": RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "certification_profile": payload.get("certification_profile"),
        "local_certify_status": payload.get("status"),
        "local_certify_failed_step": payload.get("failed_step"),
        "local_certify_report_path": str(report_path),
        "local_certify_report_sha256": report_sha256,
        "local_certify_verification_status": verification.get("status"),
        "local_certify_verification_path": str(verification_path),
        "local_certify_verification_sha256": verification_sha256,
        "required_proofs": proof_rows,
        "required_proof_count": len(proof_rows),
        "failed_proofs": failed_proofs,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "next_diagnostic": next_diagnostic,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_tree_digest": _python_core_source_tree_digest(),
        "no_live_authority_assertion": True,
        "paper_live_firewall_assertion": True,
        "repo_root": str(REPO_ROOT),
    }


def write_research_paper_discovery_closure_report(
    payload: dict[str, object],
    verification: dict[str, object],
    *,
    output_path: Path = RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
    report_path: Path = REPORT_PATH,
    verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
) -> dict[str, object]:
    closure = build_research_paper_discovery_closure_report(
        payload,
        verification,
        report_path=report_path,
        verification_path=verification_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(closure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return closure


def validate_research_paper_discovery_closure_report(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    if not path.exists():
        return None, [f"RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_MISSING:{path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_NOT_OBJECT"]
    if payload.get("schema_version") != RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_VERSION:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PHASE_UNEXPECTED:{payload.get('phase')}")
    for required_field in ("generated_at", "source_tree_digest"):
        if not isinstance(payload.get(required_field), str) or not payload.get(required_field):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_FIELD_MISSING:{required_field}")
    if payload.get("no_live_authority_assertion") is not True:
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_NO_LIVE_AUTHORITY_ASSERTION_MISSING")
    if payload.get("paper_live_firewall_assertion") is not True:
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_PAPER_LIVE_FIREWALL_ASSERTION_MISSING")
    portable_context = path.parent.name == "proof_artifacts"
    required_proofs = payload.get("required_proofs")
    proof_names: list[str] = []
    failed_proof_names: list[str] = []
    if not isinstance(required_proofs, list):
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_REQUIRED_PROOFS_NOT_LIST")
    else:
        for index, row in enumerate(required_proofs):
            if not isinstance(row, dict):
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_REQUIRED_PROOF_NOT_OBJECT:{index}")
                continue
            for field in ("proof_name", "present", "status"):
                if field not in row:
                    blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_REQUIRED_PROOF_FIELD_MISSING:{index}:{field}")
            proof_name_value = row.get("proof_name")
            proof_name = proof_name_value if isinstance(proof_name_value, str) and proof_name_value else f"index_{index}"
            proof_names.append(proof_name)
            if row.get("present") is not True:
                failed_proof_names.append(proof_name)
                continue
            if row.get("status") != "PASS":
                failed_proof_names.append(proof_name)
            proof_path_value = row.get("path")
            proof_sha_value = row.get("sha256")
            if not isinstance(proof_path_value, str) or not proof_path_value:
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_PATH_MISSING:{proof_name}")
                continue
            if portable_context and not _is_safe_relative_artifact_reference(proof_path_value):
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PORTABLE_PROOF_PATH_UNSAFE:{proof_name}:{proof_path_value}")
                continue
            proof_path = _referenced_artifact_path(proof_path_value, base_dir=path.parent, portable=portable_context)
            if proof_path is None:
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_PATH_INVALID:{proof_name}:{proof_path_value}")
                continue
            if not proof_path.exists():
                blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_FILE_MISSING:{proof_name}:{proof_path}")
                continue
            observed_proof_sha = _file_sha256(proof_path)
            if proof_sha_value != observed_proof_sha:
                blockers.append(
                    f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_SHA256_MISMATCH:{proof_name}:"
                    f"{proof_sha_value}:expected={observed_proof_sha}"
                )
            proof_schema, proof_status = _json_artifact_metadata(proof_path)
            if row.get("schema_version") != proof_schema:
                blockers.append(
                    f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_SCHEMA_MISMATCH:{proof_name}:"
                    f"{row.get('schema_version')}:expected={proof_schema}"
                )
            if row.get("status") != proof_status:
                blockers.append(
                    f"RESEARCH_PAPER_DISCOVERY_CLOSURE_PROOF_STATUS_MISMATCH:{proof_name}:"
                    f"{row.get('status')}:expected={proof_status}"
                )
    if len(proof_names) != len(set(proof_names)):
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_DUPLICATE_REQUIRED_PROOFS")
    declared_required_proof_count = payload.get("required_proof_count")
    if isinstance(required_proofs, list) and declared_required_proof_count != len(required_proofs):
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_REQUIRED_PROOF_COUNT_MISMATCH:"
            f"{declared_required_proof_count}:expected={len(required_proofs)}"
        )
    declared_failed_proofs = payload.get("failed_proofs")
    if not isinstance(declared_failed_proofs, list) or not all(isinstance(item, str) for item in declared_failed_proofs):
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_FAILED_PROOFS_INVALID")
    elif sorted(declared_failed_proofs) != sorted(failed_proof_names):
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_FAILED_PROOFS_MISMATCH:"
            f"{sorted(declared_failed_proofs)}:expected={sorted(failed_proof_names)}"
        )
    blockers_value = payload.get("blockers")
    if not isinstance(blockers_value, list) or not all(isinstance(item, str) for item in blockers_value):
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_BLOCKERS_INVALID")
        blockers_value = []
    status = payload.get("status")
    if status not in {"PASS", "FAIL"}:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_CLOSURE_STATUS_UNEXPECTED:{status}")
    if status == "PASS" and blockers_value:
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_PASS_HAS_BLOCKERS")
    if status == "PASS" and failed_proof_names:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_PASS_HAS_FAILED_PROOFS:"
            f"{','.join(sorted(failed_proof_names))}"
        )
    if status == "FAIL" and not blockers_value:
        blockers.append("RESEARCH_PAPER_DISCOVERY_CLOSURE_FAIL_MISSING_BLOCKERS")
    for field, sha_field, prefix in (
        (
            "local_certify_report_path",
            "local_certify_report_sha256",
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_REPORT",
        ),
        (
            "local_certify_verification_path",
            "local_certify_verification_sha256",
            "RESEARCH_PAPER_DISCOVERY_CLOSURE_LOCAL_CERTIFY_VERIFICATION",
        ),
    ):
        value = payload.get(field)
        declared_sha = payload.get(sha_field)
        if not isinstance(value, str) or not value:
            blockers.append(f"{prefix}_PATH_MISSING")
            continue
        if portable_context and not _is_safe_relative_artifact_reference(value):
            blockers.append(f"{prefix}_PORTABLE_PATH_UNSAFE:{value}")
            continue
        target = _referenced_artifact_path(value, base_dir=path.parent, portable=portable_context)
        if target is None or not target.exists():
            blockers.append(f"{prefix}_FILE_MISSING:{target}")
            continue
        observed_sha = _file_sha256(target)
        if declared_sha != observed_sha:
            blockers.append(f"{prefix}_SHA256_MISMATCH:{declared_sha}:expected={observed_sha}")
    return payload, blockers



def _json_artifact_metadata(path: Path) -> tuple[str | None, str | None]:
    """Return schema/status metadata for JSON artifacts without making it mandatory."""
    if not path.exists() or not path.is_file():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    schema = payload.get("schema_version")
    status = payload.get("status")
    return (schema if isinstance(schema, str) else None, status if isinstance(status, str) else None)


def _evidence_bundle_artifact_row(
    *,
    role: str,
    proof_name: str,
    path: Path | None,
    declared_sha256: object | None = None,
) -> dict[str, object]:
    exists = bool(path is not None and path.exists() and path.is_file())
    schema_version = None
    artifact_status = None
    if path is not None:
        schema_version, artifact_status = _json_artifact_metadata(path)
    observed_sha256 = _file_sha256(path) if exists and path is not None else None
    return {
        "role": role,
        "proof_name": proof_name,
        "path": None if path is None else str(path),
        "present": exists,
        "sha256": observed_sha256,
        "declared_sha256": declared_sha256,
        "size_bytes": path.stat().st_size if exists and path is not None else None,
        "schema_version": schema_version,
        "status": artifact_status,
    }


def build_research_paper_discovery_evidence_bundle(
    *,
    local_report_path: Path = REPORT_PATH,
    verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
    closure_path: Path = RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
    phase_profile_plan_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
    phase_profile_plan_verification_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
    output_path: Path = RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
) -> dict[str, object]:
    """Build a portable manifest over every proof artifact used by phase closure."""
    blockers: list[str] = []
    closure_payload, closure_blockers = validate_research_paper_discovery_closure_report(closure_path)
    for blocker in closure_blockers:
        blockers.append(f"EVIDENCE_BUNDLE_CLOSURE:{blocker}")
    artifacts: list[dict[str, object]] = [
        _evidence_bundle_artifact_row(
            role="local_certify_report",
            proof_name="local_certify_report",
            path=local_report_path,
            declared_sha256=_file_sha256(local_report_path) if local_report_path.exists() else None,
        ),
        _evidence_bundle_artifact_row(
            role="local_certify_report_verification",
            proof_name="local_certify_report_verification",
            path=verification_path,
            declared_sha256=_file_sha256(verification_path) if verification_path.exists() else None,
        ),
        _evidence_bundle_artifact_row(
            role="phase_closure_report",
            proof_name="research_paper_discovery_closure_report",
            path=closure_path,
            declared_sha256=_file_sha256(closure_path) if closure_path.exists() else None,
        ),
    ]
    optional_phase_artifacts = (
        ("phase_profile_plan", "research_paper_discovery_profile_plan", phase_profile_plan_path),
        ("phase_profile_plan_verification", "research_paper_discovery_profile_plan_verification", phase_profile_plan_verification_path),
    )
    for role, proof_name, optional_path in optional_phase_artifacts:
        if (
            optional_path.exists()
            and optional_path.is_file()
            and optional_path.parent.resolve() == output_path.parent.resolve()
        ):
            artifacts.append(
                _evidence_bundle_artifact_row(
                    role=role,
                    proof_name=proof_name,
                    path=optional_path,
                    declared_sha256=_file_sha256(optional_path),
                )
            )
    if isinstance(closure_payload, dict):
        for row in closure_payload.get("required_proofs", []):
            if not isinstance(row, dict):
                continue
            proof_name = row.get("proof_name")
            proof_path = _repo_relative_or_absolute_path(row.get("path"))
            artifacts.append(
                _evidence_bundle_artifact_row(
                    role="required_proof",
                    proof_name=proof_name if isinstance(proof_name, str) and proof_name else "unknown_required_proof",
                    path=proof_path,
                    declared_sha256=row.get("sha256"),
                )
            )
    seen_names: set[str] = set()
    duplicate_names: list[str] = []
    for artifact in artifacts:
        proof_name = str(artifact.get("proof_name"))
        if proof_name in seen_names:
            duplicate_names.append(proof_name)
        seen_names.add(proof_name)
        if artifact.get("present") is not True:
            blockers.append(f"EVIDENCE_BUNDLE_ARTIFACT_MISSING:{proof_name}:{artifact.get('path')}")
        declared_sha = artifact.get("declared_sha256")
        observed_sha = artifact.get("sha256")
        if declared_sha is not None and observed_sha is not None and declared_sha != observed_sha:
            blockers.append(f"EVIDENCE_BUNDLE_ARTIFACT_SHA256_MISMATCH:{proof_name}:{declared_sha}:expected={observed_sha}")
    if duplicate_names:
        blockers.append("EVIDENCE_BUNDLE_DUPLICATE_PROOF_NAMES:" + ",".join(sorted(set(duplicate_names))))
    closure_status = closure_payload.get("status") if isinstance(closure_payload, dict) else None
    if closure_status != "PASS":
        blockers.append(f"EVIDENCE_BUNDLE_PHASE_CLOSURE_NOT_PASSING:{closure_status}")
    required_artifact_proof_names = [
        "local_certify_report",
        "local_certify_report_verification",
        "research_paper_discovery_closure_report",
    ]
    if isinstance(closure_payload, dict) and isinstance(closure_payload.get("required_proofs"), list):
        for row in closure_payload["required_proofs"]:
            if isinstance(row, dict) and isinstance(row.get("proof_name"), str) and row.get("proof_name"):
                required_artifact_proof_names.append(row["proof_name"])
    provenance = _evidence_bundle_provenance(artifacts=artifacts, output_path=output_path)
    artifact_manifest_sha256 = _evidence_bundle_artifact_manifest_digest(artifacts)
    payload: dict[str, object] = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "closure_status": closure_status,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_artifact_proof_names": required_artifact_proof_names,
        "bundle_manifest_sha256": artifact_manifest_sha256,
        "provenance": provenance,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "local_certify_report_path": str(local_report_path),
        "local_certify_report_verification_path": str(verification_path),
        "phase_closure_report_path": str(closure_path),
        "output_path": str(output_path),
        "generated_at": _utc_now(),
        "repo_root": str(REPO_ROOT),
    }
    payload["bundle_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "bundle_payload_sha256"})
    return payload


def write_research_paper_discovery_evidence_bundle(
    *,
    local_report_path: Path = REPORT_PATH,
    verification_path: Path = LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
    closure_path: Path = RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
    phase_profile_plan_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
    phase_profile_plan_verification_path: Path = RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
    output_path: Path = RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
    seal_path: Path | None = None,
) -> dict[str, object]:
    bundle = build_research_paper_discovery_evidence_bundle(
        local_report_path=local_report_path,
        verification_path=verification_path,
        closure_path=closure_path,
        phase_profile_plan_path=phase_profile_plan_path,
        phase_profile_plan_verification_path=phase_profile_plan_verification_path,
        output_path=output_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_research_paper_discovery_evidence_bundle_seal(
        bundle_path=output_path,
        seal_path=seal_path or _evidence_bundle_seal_path_for(output_path),
    )
    return bundle


def _evidence_bundle_seal_path_for(bundle_path: Path) -> Path:
    return bundle_path.with_name("research_paper_discovery_evidence_bundle_seal.json")


def _evidence_bundle_seal_subject(
    bundle_path: Path,
    bundle_payload: dict[str, object],
    *,
    subject_bundle_path: str | None = None,
) -> dict[str, object]:
    provenance = bundle_payload.get("provenance") if isinstance(bundle_payload.get("provenance"), dict) else {}
    required_names = bundle_payload.get("required_artifact_proof_names")
    subject = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_SCHEMA_VERSION,
        "phase": bundle_payload.get("phase"),
        "bundle_schema_version": bundle_payload.get("schema_version"),
        "bundle_status": bundle_payload.get("status"),
        "bundle_path": subject_bundle_path or str(bundle_path),
        "bundle_sha256": _file_sha256(bundle_path),
        "bundle_payload_sha256": bundle_payload.get("bundle_payload_sha256"),
        "bundle_manifest_sha256": bundle_payload.get("bundle_manifest_sha256"),
        "provenance_sha256": _canonical_json_digest(provenance),
        "artifact_count": bundle_payload.get("artifact_count"),
        "required_artifact_proof_names_sha256": _canonical_json_digest(required_names if isinstance(required_names, list) else []),
        "source_tree_digest": provenance.get("source_tree_digest") if isinstance(provenance, dict) else None,
        "exported": bundle_payload.get("exported") is True,
    }
    return subject


def build_research_paper_discovery_evidence_bundle_seal(
    *,
    bundle_path: Path,
    subject_bundle_path: str | None = None,
) -> dict[str, object]:
    blockers: list[str] = []
    bundle_payload: dict[str, object] | None = None
    if not bundle_path.exists():
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_MISSING:{bundle_path}")
    else:
        try:
            loaded = json.loads(bundle_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                bundle_payload = loaded
            else:
                blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_NOT_OBJECT")
        except json.JSONDecodeError as exc:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_INVALID_JSON:{exc}")
    subject = _evidence_bundle_seal_subject(
        bundle_path, bundle_payload or {}, subject_bundle_path=subject_bundle_path
    ) if bundle_payload is not None else {
        "bundle_path": subject_bundle_path or str(bundle_path),
        "bundle_sha256": None,
    }
    if bundle_payload is not None and subject.get("bundle_status") != "PASS":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_BUNDLE_NOT_PASSING:{subject.get('bundle_status')}")
    payload: dict[str, object] = {
        "schema_version": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_VERSION,
        "status": "PASS" if not blockers else "FAIL",
        "seal_kind": "UNSIGNED_DETERMINISTIC_ATTESTATION",
        "digest_algorithm": "sha256",
        "generated_by": "scripts/local_certify.py",
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "subject": subject,
        "subject_sha256": _canonical_json_digest(subject),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "generated_at": _utc_now(),
    }
    payload["seal_payload_sha256"] = _canonical_json_digest({k: v for k, v in payload.items() if k != "seal_payload_sha256"})
    return payload


def write_research_paper_discovery_evidence_bundle_seal(
    *,
    bundle_path: Path,
    seal_path: Path,
    subject_bundle_path: str | None = None,
) -> dict[str, object]:
    seal = build_research_paper_discovery_evidence_bundle_seal(
        bundle_path=bundle_path, subject_bundle_path=subject_bundle_path
    )
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return seal



RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_REQUIRED_SUBJECT_FIELDS = (
    "schema_version",
    "phase",
    "bundle_schema_version",
    "bundle_status",
    "bundle_path",
    "bundle_sha256",
    "bundle_payload_sha256",
    "bundle_manifest_sha256",
    "provenance_sha256",
    "artifact_count",
    "required_artifact_proof_names_sha256",
    "source_tree_digest",
    "exported",
)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def validate_research_paper_discovery_evidence_bundle_seal(
    seal_path: Path,
    *,
    bundle_path: Path | None = None,
    portable: bool | None = None,
) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    if not seal_path.exists():
        return None, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_MISSING:{seal_path}"]
    try:
        payload = json.loads(seal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_NOT_OBJECT"]
    if payload.get("schema_version") != RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_VERSION:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    declared_payload_digest = payload.get("seal_payload_sha256")
    observed_payload_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "seal_payload_sha256"})
    if declared_payload_digest != observed_payload_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PAYLOAD_DIGEST_MISMATCH:"
            f"{declared_payload_digest}:expected={observed_payload_digest}"
        )
    if payload.get("seal_kind") != "UNSIGNED_DETERMINISTIC_ATTESTATION":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_KIND_UNEXPECTED:{payload.get('seal_kind')}")
    if payload.get("digest_algorithm") != "sha256":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_DIGEST_ALGORITHM_UNEXPECTED:{payload.get('digest_algorithm')}")
    if payload.get("generated_by") != "scripts/local_certify.py":
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_GENERATOR_UNEXPECTED:{payload.get('generated_by')}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PHASE_UNEXPECTED:{payload.get('phase')}")
    subject = payload.get("subject")
    if not isinstance(subject, dict):
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_NOT_OBJECT")
        subject = {}
    declared_subject_digest = payload.get("subject_sha256")
    observed_subject_digest = _canonical_json_digest(subject)
    if declared_subject_digest != observed_subject_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_DIGEST_MISMATCH:"
            f"{declared_subject_digest}:expected={observed_subject_digest}"
        )
    for field in RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_REQUIRED_SUBJECT_FIELDS:
        if field not in subject:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_FIELD_MISSING:{field}")
    if subject.get("schema_version") != RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_SCHEMA_VERSION:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_SCHEMA_UNEXPECTED:"
            f"{subject.get('schema_version')}"
        )
    if subject.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_PHASE_UNEXPECTED:{subject.get('phase')}")
    if subject.get("bundle_schema_version") != RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SCHEMA_VERSION:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_BUNDLE_SCHEMA_UNEXPECTED:"
            f"{subject.get('bundle_schema_version')}"
        )
    for digest_field in (
        "bundle_sha256",
        "bundle_payload_sha256",
        "bundle_manifest_sha256",
        "provenance_sha256",
        "required_artifact_proof_names_sha256",
        "source_tree_digest",
    ):
        digest_value = subject.get(digest_field)
        if digest_value is not None and not _is_sha256_hex(digest_value):
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_DIGEST_FIELD_INVALID:{digest_field}:{digest_value}"
            )
    path_value = subject.get("bundle_path")
    seal_is_portable = portable if portable is not None else subject.get("exported") is True
    if portable is not None and subject.get("exported") is not portable:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_EXPORTED_FLAG_MISMATCH:"
            f"{subject.get('exported')}:expected={portable}"
        )
    if not isinstance(path_value, str) or not path_value:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_PATH_MISSING")
    elif seal_is_portable and not _is_safe_relative_artifact_reference(path_value):
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PORTABLE_BUNDLE_PATH_UNSAFE:{path_value}")
    resolved_bundle_path = bundle_path
    if resolved_bundle_path is None:
        if not isinstance(path_value, str) or not path_value:
            resolved_bundle_path = None
        elif seal_is_portable and not _is_safe_relative_artifact_reference(path_value):
            resolved_bundle_path = None
        else:
            resolved_bundle_path = _referenced_artifact_path(path_value, base_dir=seal_path.parent, portable=seal_is_portable)
    if resolved_bundle_path is None or not resolved_bundle_path.exists():
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_FILE_MISSING:{path_value}")
    else:
        observed_bundle_sha = _file_sha256(resolved_bundle_path)
        if subject.get("bundle_sha256") != observed_bundle_sha:
            blockers.append(
                "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_SHA256_MISMATCH:"
                f"{subject.get('bundle_sha256')}:expected={observed_bundle_sha}"
            )
        try:
            bundle_payload = json.loads(resolved_bundle_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BUNDLE_INVALID_JSON:{exc}")
            bundle_payload = None
        if isinstance(bundle_payload, dict):
            expected_subject = _evidence_bundle_seal_subject(resolved_bundle_path, bundle_payload)
            # For exported portable bundles the seal subject stores the portable relative bundle path.
            expected_subject["bundle_path"] = subject.get("bundle_path")
            if subject != expected_subject:
                blockers.append(
                    "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_SUBJECT_MISMATCH:"
                    f"{_canonical_json_digest(subject)}:expected={_canonical_json_digest(expected_subject)}"
                )
    status = payload.get("status")
    if status not in {"PASS", "FAIL"}:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_STATUS_UNEXPECTED:{status}")
    seal_blockers = payload.get("blockers")
    if not isinstance(seal_blockers, list) or not all(isinstance(item, str) for item in seal_blockers):
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_BLOCKERS_INVALID")
        seal_blockers = []
    if status == "PASS" and seal_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PASS_HAS_BLOCKERS")
    if status == "PASS" and blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_PASS_HAS_VALIDATION_BLOCKERS")
    if status == "FAIL" and not seal_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL_FAIL_MISSING_BLOCKERS")
    return payload, blockers


def validate_research_paper_discovery_evidence_bundle(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    blockers: list[str] = []
    if not path.exists():
        return None, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_MISSING:{path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_INVALID_JSON:{exc}"]
    if not isinstance(payload, dict):
        return None, ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_NOT_OBJECT"]
    if payload.get("schema_version") != RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SCHEMA_VERSION:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SCHEMA_UNEXPECTED:{payload.get('schema_version')}")
    declared_digest = payload.get("bundle_payload_sha256")
    observed_digest = _canonical_json_digest({k: v for k, v in payload.items() if k != "bundle_payload_sha256"})
    if declared_digest != observed_digest:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PAYLOAD_DIGEST_MISMATCH:{declared_digest}:expected={observed_digest}")
    if payload.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PHASE_UNEXPECTED:{payload.get('phase')}")
    portable_bundle = payload.get("exported") is True
    required_artifact_names_value = payload.get("required_artifact_proof_names")
    required_artifact_names: list[str] = []
    if isinstance(required_artifact_names_value, list) and all(isinstance(item, str) and item for item in required_artifact_names_value):
        required_artifact_names = list(required_artifact_names_value)
    elif required_artifact_names_value is not None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_REQUIRED_ARTIFACT_NAMES_INVALID")
    artifacts = payload.get("artifacts")
    artifact_names: list[str] = []
    closure_artifact_seen = False
    if not isinstance(artifacts, list):
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACTS_NOT_LIST")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_NOT_OBJECT:{index}")
            continue
        proof_name = artifact.get("proof_name")
        proof_name = proof_name if isinstance(proof_name, str) and proof_name else f"index_{index}"
        artifact_names.append(proof_name)
        if proof_name == "research_paper_discovery_closure_report":
            closure_artifact_seen = True
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_PATH_MISSING:{proof_name}")
            continue
        if portable_bundle and not _is_safe_relative_artifact_reference(path_value):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PORTABLE_ARTIFACT_PATH_UNSAFE:{proof_name}:{path_value}")
            continue
        artifact_path = _referenced_artifact_path(path_value, base_dir=path.parent, portable=portable_bundle)
        if artifact_path is None or not artifact_path.exists():
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_FILE_MISSING:{proof_name}:{path_value}")
            continue
        observed_sha = _file_sha256(artifact_path)
        if artifact.get("sha256") != observed_sha:
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_SHA256_MISMATCH:{proof_name}:"
                f"{artifact.get('sha256')}:expected={observed_sha}"
            )
        if artifact.get("declared_sha256") is not None and artifact.get("declared_sha256") != observed_sha:
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_DECLARED_SHA256_MISMATCH:{proof_name}:"
                f"{artifact.get('declared_sha256')}:expected={observed_sha}"
            )
        if artifact.get("size_bytes") != artifact_path.stat().st_size:
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_SIZE_MISMATCH:{proof_name}:"
                f"{artifact.get('size_bytes')}:expected={artifact_path.stat().st_size}"
            )
        schema_version, status = _json_artifact_metadata(artifact_path)
        if artifact.get("schema_version") != schema_version:
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_SCHEMA_MISMATCH:{proof_name}:"
                f"{artifact.get('schema_version')}:expected={schema_version}"
            )
        if artifact.get("status") != status:
            blockers.append(
                f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_STATUS_MISMATCH:{proof_name}:"
                f"{artifact.get('status')}:expected={status}"
            )
    if len(artifact_names) != len(set(artifact_names)):
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_DUPLICATE_PROOF_NAMES")
    if required_artifact_names:
        missing_required = sorted(set(required_artifact_names) - set(artifact_names))
        unknown_artifacts = sorted(set(artifact_names) - set(required_artifact_names))
        for name in missing_required:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_REQUIRED_ARTIFACT_MISSING:{name}")
        for name in unknown_artifacts:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_UNKNOWN_ARTIFACT:{name}")
    declared_manifest_sha256 = payload.get("bundle_manifest_sha256")
    observed_manifest_sha256 = _evidence_bundle_artifact_manifest_digest(artifacts)
    if declared_manifest_sha256 != observed_manifest_sha256:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_MANIFEST_SHA256_MISMATCH:"
            f"{declared_manifest_sha256}:expected={observed_manifest_sha256}"
        )
    declared_count = payload.get("artifact_count")
    if declared_count != len(artifacts):
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_ARTIFACT_COUNT_MISMATCH:{declared_count}:expected={len(artifacts)}")
    blockers.extend(_validate_evidence_bundle_provenance(payload, base_dir=path.parent))
    if not closure_artifact_seen:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_CLOSURE_ARTIFACT_MISSING")
    closure_path_value = payload.get("phase_closure_report_path")
    if portable_bundle and not _is_safe_relative_artifact_reference(closure_path_value):
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PORTABLE_CLOSURE_PATH_UNSAFE:{closure_path_value}")
        closure_path = None
    else:
        closure_path = _referenced_artifact_path(closure_path_value, base_dir=path.parent, portable=portable_bundle)
    if closure_path is None:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_CLOSURE_PATH_MISSING")
    else:
        _closure_payload, closure_blockers = validate_research_paper_discovery_closure_report(closure_path)
        for blocker in closure_blockers:
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_CLOSURE:{blocker}")
    seal_path = _evidence_bundle_seal_path_for(path)
    _seal_payload, seal_blockers = validate_research_paper_discovery_evidence_bundle_seal(
        seal_path, bundle_path=path, portable=portable_bundle
    )
    for blocker in seal_blockers:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_SEAL:{blocker}")
    payload_blockers = payload.get("blockers")
    if not isinstance(payload_blockers, list) or not all(isinstance(item, str) for item in payload_blockers):
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_BLOCKERS_INVALID")
        payload_blockers = []
    status = payload.get("status")
    if status not in {"PASS", "FAIL"}:
        blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_STATUS_UNEXPECTED:{status}")
    if status == "PASS" and payload_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PASS_HAS_BLOCKERS")
    if status == "PASS" and blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PASS_HAS_VALIDATION_BLOCKERS")
    if status == "FAIL" and not payload_blockers:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_FAIL_MISSING_BLOCKERS")
    return payload, blockers


def _artifact_row_by_proof_name(artifacts: Sequence[object], proof_name: str) -> dict[str, object] | None:
    for artifact in artifacts:
        if isinstance(artifact, dict) and artifact.get("proof_name") == proof_name:
            return artifact
    return None


def _evidence_bundle_artifact_manifest_digest(artifacts: Sequence[object]) -> str:
    return _canonical_json_digest(list(artifacts))


def _evidence_bundle_provenance(
    *,
    artifacts: Sequence[dict[str, object]],
    output_path: Path,
    exported: bool = False,
    exported_from_bundle_path: Path | None = None,
    export_root: Path | None = None,
) -> dict[str, object]:
    local_report = _artifact_row_by_proof_name(artifacts, "local_certify_report")
    verification = _artifact_row_by_proof_name(artifacts, "local_certify_report_verification")
    closure = _artifact_row_by_proof_name(artifacts, "research_paper_discovery_closure_report")
    return {
        "schema_version": RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_VERSION,
        "phase": RESEARCH_PAPER_DISCOVERY_PROFILE,
        "generated_by": "scripts/local_certify.py",
        "generator_schema_version": LOCAL_CERTIFY_SCHEMA_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "repo_root": str(REPO_ROOT),
        "source_tree_digest": _python_core_source_tree_digest(),
        "artifact_manifest_sha256": _evidence_bundle_artifact_manifest_digest(artifacts),
        "artifact_count": len(artifacts),
        "local_certify_report_sha256": None if local_report is None else local_report.get("sha256"),
        "local_certify_report_verification_sha256": None if verification is None else verification.get("sha256"),
        "phase_closure_report_sha256": None if closure is None else closure.get("sha256"),
        "output_path": str(output_path),
        "exported": exported,
        "exported_from_bundle_path": None if exported_from_bundle_path is None else str(exported_from_bundle_path),
        "export_root": None if export_root is None else str(export_root),
        "generated_at": _utc_now(),
    }


def _validate_evidence_bundle_provenance(payload: dict[str, object], *, base_dir: Path) -> list[str]:
    blockers: list[str] = []
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_MISSING"]
    if provenance.get("schema_version") != RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_VERSION:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SCHEMA_UNEXPECTED:"
            f"{provenance.get('schema_version')}"
        )
    if provenance.get("phase") != RESEARCH_PAPER_DISCOVERY_PROFILE:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_PHASE_UNEXPECTED:"
            f"{provenance.get('phase')}"
        )
    if provenance.get("generated_by") != "scripts/local_certify.py":
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_GENERATOR_UNEXPECTED:"
            f"{provenance.get('generated_by')}"
        )
    if provenance.get("generator_schema_version") != LOCAL_CERTIFY_SCHEMA_VERSION:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_GENERATOR_SCHEMA_UNEXPECTED:"
            f"{provenance.get('generator_schema_version')}"
        )
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []
    declared_artifact_count = provenance.get("artifact_count")
    if declared_artifact_count != len(artifacts):
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_ARTIFACT_COUNT_MISMATCH:"
            f"{declared_artifact_count}:expected={len(artifacts)}"
        )
    declared_manifest_digest = provenance.get("artifact_manifest_sha256")
    observed_manifest_digest = _evidence_bundle_artifact_manifest_digest(artifacts)
    if declared_manifest_digest != observed_manifest_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_ARTIFACT_MANIFEST_SHA256_MISMATCH:"
            f"{declared_manifest_digest}:expected={observed_manifest_digest}"
        )
    if payload.get("bundle_manifest_sha256") != observed_manifest_digest:
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_BUNDLE_MANIFEST_SHA256_MISMATCH:"
            f"{payload.get('bundle_manifest_sha256')}:expected={observed_manifest_digest}"
        )
    if payload.get("exported") is not True and provenance.get("source_tree_digest") != _python_core_source_tree_digest():
        blockers.append(
            "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SOURCE_TREE_DIGEST_STALE:"
            f"{provenance.get('source_tree_digest')}:expected={_python_core_source_tree_digest()}"
        )
    for proof_name, field_name in (
        ("local_certify_report", "local_certify_report_sha256"),
        ("local_certify_report_verification", "local_certify_report_verification_sha256"),
        ("research_paper_discovery_closure_report", "phase_closure_report_sha256"),
    ):
        artifact = _artifact_row_by_proof_name(artifacts, proof_name)
        expected_sha = None if artifact is None else artifact.get("sha256")
        if provenance.get(field_name) != expected_sha:
            blockers.append(
                "RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_SHA256_MISMATCH:"
                f"{field_name}:{provenance.get(field_name)}:expected={expected_sha}"
            )
    for string_field in ("python_version", "platform", "repo_root", "source_tree_digest", "output_path", "generated_at"):
        if not isinstance(provenance.get(string_field), str) or not provenance.get(string_field):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_FIELD_MISSING:{string_field}")
    if payload.get("exported") is True and provenance.get("exported") is not True:
        blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_EXPORT_FLAG_MISMATCH")
    if payload.get("exported") is True:
        if not isinstance(provenance.get("export_root"), str) or not provenance.get("export_root"):
            blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_EXPORT_ROOT_MISSING")
        if not isinstance(provenance.get("exported_from_bundle_path"), str) or not provenance.get("exported_from_bundle_path"):
            blockers.append("RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PROVENANCE_EXPORTED_FROM_PATH_MISSING")
    return blockers


def _portable_proof_filename(proof_name: str, index: int) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in proof_name.strip())
    safe = safe.strip("._") or f"artifact_{index}"
    return f"{index:02d}_{safe}.json"


def _copy_optional_phase_export_artifact(
    *,
    proof_name: str,
    role: str,
    source_path: Path,
    export_dir: Path,
    index: int,
    copied_rows: list[dict[str, object]],
    copied_by_name: dict[str, str],
) -> None:
    if proof_name in copied_by_name:
        return
    if not source_path.exists() or not source_path.is_file():
        return
    relative_path = f"proof_artifacts/{_portable_proof_filename(proof_name, index)}"
    dest_path = export_dir / relative_path
    shutil.copy2(source_path, dest_path)
    schema_version, status = _json_artifact_metadata(dest_path)
    copied_rows.append(
        {
            "role": role,
            "proof_name": proof_name,
            "path": relative_path,
            "present": True,
            "sha256": _file_sha256(dest_path),
            "declared_sha256": _file_sha256(dest_path),
            "size_bytes": dest_path.stat().st_size,
            "schema_version": schema_version,
            "status": status,
            "exported_from_path": str(source_path),
        }
    )
    copied_by_name[proof_name] = relative_path


def export_research_paper_discovery_evidence_bundle(
    *,
    bundle_path: Path,
    export_dir: Path,
) -> tuple[dict[str, object] | None, list[str]]:
    """Copy a phase evidence bundle into a portable, self-contained directory."""
    source_payload, validation_blockers = validate_research_paper_discovery_evidence_bundle(bundle_path)
    hard_blockers = [blocker for blocker in validation_blockers if "_PASS_HAS_" in blocker or "_PAYLOAD_DIGEST_MISMATCH" in blocker]
    if source_payload is None:
        return None, validation_blockers
    if hard_blockers:
        return None, validation_blockers
    artifacts = source_payload.get("artifacts")
    if not isinstance(artifacts, list):
        return None, ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_ARTIFACTS_NOT_LIST"]

    export_dir.mkdir(parents=True, exist_ok=True)
    proof_dir = export_dir / "proof_artifacts"
    proof_dir.mkdir(parents=True, exist_ok=True)

    copied_by_name: dict[str, str] = {}
    copied_rows: list[dict[str, object]] = []
    blockers: list[str] = []
    closure_source_path: Path | None = None
    closure_dest_relative: str | None = None
    closure_row_index: int | None = None

    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_ARTIFACT_NOT_OBJECT:{index}")
            continue
        proof_name_value = artifact.get("proof_name")
        proof_name = proof_name_value if isinstance(proof_name_value, str) and proof_name_value else f"artifact_{index}"
        path_value = artifact.get("path")
        source_path = _referenced_artifact_path(path_value, base_dir=bundle_path.parent)
        if source_path is None or not source_path.exists() or not source_path.is_file():
            blockers.append(f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_ARTIFACT_MISSING:{proof_name}:{path_value}")
            continue
        relative_path = f"proof_artifacts/{_portable_proof_filename(proof_name, index)}"
        dest_path = export_dir / relative_path
        if proof_name == "research_paper_discovery_closure_report":
            closure_source_path = source_path
            closure_dest_relative = relative_path
            closure_row_index = len(copied_rows)
            copied_rows.append(dict(artifact, path=relative_path, exported_from_path=str(source_path)))
            copied_by_name[proof_name] = relative_path
            continue
        shutil.copy2(source_path, dest_path)
        schema_version, status = _json_artifact_metadata(dest_path)
        copied_row = dict(artifact)
        copied_row.update(
            {
                "path": relative_path,
                "present": True,
                "sha256": _file_sha256(dest_path),
                "declared_sha256": artifact.get("declared_sha256"),
                "size_bytes": dest_path.stat().st_size,
                "schema_version": schema_version,
                "status": status,
                "exported_from_path": str(source_path),
            }
        )
        copied_rows.append(copied_row)
        copied_by_name[proof_name] = relative_path

    if blockers:
        return None, blockers
    if closure_source_path is None or closure_dest_relative is None or closure_row_index is None:
        return None, ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_CLOSURE_ARTIFACT_MISSING"]

    try:
        closure_payload = json.loads(closure_source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_CLOSURE_INVALID_JSON:{exc}"]
    if not isinstance(closure_payload, dict):
        return None, ["RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_CLOSURE_NOT_OBJECT"]

    if copied_by_name.get("local_certify_report"):
        closure_payload["local_certify_report_path"] = Path(copied_by_name["local_certify_report"]).name
        local_report_path = export_dir / copied_by_name["local_certify_report"]
        closure_payload["local_certify_report_sha256"] = _file_sha256(local_report_path)
    if copied_by_name.get("local_certify_report_verification"):
        closure_payload["local_certify_verification_path"] = Path(copied_by_name["local_certify_report_verification"]).name
        verification_path = export_dir / copied_by_name["local_certify_report_verification"]
        closure_payload["local_certify_verification_sha256"] = _file_sha256(verification_path)

    required_proofs = closure_payload.get("required_proofs")
    if isinstance(required_proofs, list):
        for row in required_proofs:
            if not isinstance(row, dict):
                continue
            proof_name_value = row.get("proof_name")
            if not isinstance(proof_name_value, str):
                continue
            copied_relative = copied_by_name.get(proof_name_value)
            if not copied_relative:
                continue
            copied_path = export_dir / copied_relative
            row["path"] = Path(copied_relative).name
            row["sha256"] = _file_sha256(copied_path)
    closure_dest_path = export_dir / closure_dest_relative
    closure_dest_path.write_text(json.dumps(closure_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    closure_schema, closure_status = _json_artifact_metadata(closure_dest_path)
    closure_row = dict(copied_rows[closure_row_index])
    closure_row.update(
        {
            "path": closure_dest_relative,
            "present": True,
            "sha256": _file_sha256(closure_dest_path),
            "declared_sha256": _file_sha256(closure_dest_path),
            "size_bytes": closure_dest_path.stat().st_size,
            "schema_version": closure_schema,
            "status": closure_status,
            "exported_from_path": str(closure_source_path),
        }
    )
    copied_rows[closure_row_index] = closure_row

    next_index = len(copied_rows) + 1
    optional_export_artifacts = (
        ("research_paper_discovery_profile_plan", "phase_profile_plan", bundle_path.parent / "research_paper_discovery_profile_plan.json"),
        ("research_paper_discovery_profile_plan_verification", "phase_profile_plan_verification", bundle_path.parent / "research_paper_discovery_profile_plan_verification.json"),
        ("research_paper_discovery_phase_run_report", "phase_run_report", bundle_path.parent / "research_paper_discovery_phase_run_report.json"),
        ("research_paper_discovery_phase_run_report_verification", "phase_run_report_verification", bundle_path.parent / "research_paper_discovery_phase_run_report_verification.json"),
        ("final_research_paper_discovery_certification_index", "final_phase_certificate_index", bundle_path.parent / "final_research_paper_discovery_certification_index.json"),
        ("final_research_paper_discovery_certification_verification", "final_phase_certificate_verification", bundle_path.parent / "final_research_paper_discovery_certification_verification.json"),
    )
    for proof_name, role, optional_path in optional_export_artifacts:
        before = len(copied_rows)
        _copy_optional_phase_export_artifact(
            proof_name=proof_name,
            role=role,
            source_path=optional_path,
            export_dir=export_dir,
            index=next_index,
            copied_rows=copied_rows,
            copied_by_name=copied_by_name,
        )
        if len(copied_rows) > before:
            next_index += 1

    required_artifact_proof_names = list(source_payload.get("required_artifact_proof_names") or [])
    for proof_name in copied_by_name:
        if proof_name not in required_artifact_proof_names:
            required_artifact_proof_names.append(proof_name)

    exported_payload = dict(source_payload)
    exported_payload.update(
        {
            "artifacts": copied_rows,
            "artifact_count": len(copied_rows),
            "required_artifact_proof_names": required_artifact_proof_names,
            "bundle_manifest_sha256": _evidence_bundle_artifact_manifest_digest(copied_rows),
            "phase_closure_report_path": closure_dest_relative,
            "local_certify_report_path": copied_by_name.get("local_certify_report"),
            "local_certify_report_verification_path": copied_by_name.get("local_certify_report_verification"),
            "output_path": "research_paper_discovery_evidence_bundle.json",
            "exported": True,
            "exported_at": _utc_now(),
            "exported_from_bundle_path": str(bundle_path),
            "export_root": str(export_dir),
        }
    )
    exported_payload["provenance"] = _evidence_bundle_provenance(
        artifacts=copied_rows,
        output_path=Path("research_paper_discovery_evidence_bundle.json"),
        exported=True,
        exported_from_bundle_path=bundle_path,
        export_root=export_dir,
    )
    exported_payload["bundle_payload_sha256"] = _canonical_json_digest(
        {k: v for k, v in exported_payload.items() if k != "bundle_payload_sha256"}
    )
    exported_manifest = export_dir / "research_paper_discovery_evidence_bundle.json"
    exported_manifest.write_text(json.dumps(exported_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_research_paper_discovery_evidence_bundle_seal(
        bundle_path=exported_manifest,
        seal_path=_evidence_bundle_seal_path_for(exported_manifest),
        subject_bundle_path="research_paper_discovery_evidence_bundle.json",
    )

    _verified_payload, exported_blockers = validate_research_paper_discovery_evidence_bundle(exported_manifest)
    if exported_blockers:
        return exported_payload, [f"RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_REPLAY:{blocker}" for blocker in exported_blockers]
    return exported_payload, []


@contextlib.contextmanager
def _temporary_certify_artifact_paths(args: argparse.Namespace):
    """Temporarily rebind canonical artifact paths for this process (tests, isolated dirs).

    Restores module-level paths on exit so in-process test callers do not leak overrides.
    """
    global REPORT_PATH, FRONTEND_PREFLIGHT_REPORT_PATH, PYTHON_CORE_REPORT_PATH
    saved_report = REPORT_PATH
    saved_preflight = FRONTEND_PREFLIGHT_REPORT_PATH
    saved_python_core = PYTHON_CORE_REPORT_PATH
    try:
        if args.local_certify_report_output is not None:
            REPORT_PATH = args.local_certify_report_output.expanduser().resolve()
        if args.frontend_preflight_report_output is not None:
            FRONTEND_PREFLIGHT_REPORT_PATH = args.frontend_preflight_report_output.expanduser().resolve()
        if args.python_core_report_output is not None:
            PYTHON_CORE_REPORT_PATH = args.python_core_report_output.expanduser().resolve()
        yield
    finally:
        REPORT_PATH = saved_report
        FRONTEND_PREFLIGHT_REPORT_PATH = saved_preflight
        PYTHON_CORE_REPORT_PATH = saved_python_core


def _write_report(payload: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_for_unicode()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary after the transcript.")
    parser.add_argument("--no-fail-fast", action="store_true", help="Run all phases even if one fails.")
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Run only Python gates. CI/local parity documentation treats this as a diagnostic mode, not certification.",
    )
    parser.add_argument(
        "--clean-frontend-workspace",
        action="store_true",
        help="Remove frontend generated state before npm ci/npm run certify and seal the cleanup proof.",
    )
    parser.add_argument(
        "--include-collection-shards",
        action="store_true",
        help="Append resumable full pytest collection shard proof steps and aggregate their JSON reports.",
    )
    parser.add_argument("--collection-shard-count", type=int, default=16, help="Shard count for --include-collection-shards.")
    parser.add_argument("--collection-shard-timeout-seconds", type=int, default=120, help="Per-shard watchdog timeout for --include-collection-shards.")
    parser.add_argument("--collection-shard-heartbeat-seconds", type=int, default=5, help="Per-shard heartbeat interval for --include-collection-shards.")
    parser.add_argument(
        "--include-constitutional-shards",
        action="store_true",
        help="Append resumable constitutional shard proof steps and aggregate their JSON reports.",
    )
    parser.add_argument("--constitutional-shard-count", type=int, default=16, help="Shard count for --include-constitutional-shards.")
    parser.add_argument("--constitutional-shard-timeout-seconds", type=int, default=120, help="Per-shard watchdog timeout for --include-constitutional-shards.")
    parser.add_argument("--constitutional-shard-heartbeat-seconds", type=int, default=5, help="Per-shard heartbeat interval for --include-constitutional-shards.")
    parser.add_argument(
        "--include-pytest-shards",
        action="store_true",
        help="Append resumable backend pytest execution shard proof steps and aggregate their JSON reports.",
    )
    parser.add_argument("--pytest-shard-count", type=int, default=16, help="Shard count for --include-pytest-shards.")
    parser.add_argument("--pytest-shard-timeout-seconds", type=int, default=180, help="Per-shard watchdog timeout for --include-pytest-shards.")
    parser.add_argument("--pytest-shard-heartbeat-seconds", type=int, default=5, help="Per-shard heartbeat interval for --include-pytest-shards.")
    parser.add_argument(
        "--run-monolithic-pytest-with-shards",
        action="store_true",
        help=(
            "When --include-pytest-shards is used, also run the monolithic python -m pytest -q gate. "
            "By default shard proof replaces the monolithic pytest gate to avoid reintroducing an opaque long-running blocker."
        ),
    )
    parser.add_argument(
        "--include-researcher-fixture",
        action="store_true",
        help="Append bounded Researcher cycle + certification fixture proof and embed its sealed report.",
    )
    parser.add_argument(
        "--certify-research-paper-discovery",
        action="store_true",
        help=(
            "Expand to the current Research-and-Paper-Discovery certification profile: clean frontend proof, "
            "collection shards, constitutional shards, pytest execution shards, and Researcher fixture proof."
        ),
    )
    parser.add_argument(
        "--phase-profile-plan-only",
        action="store_true",
        help=(
            "With --certify-research-paper-discovery, run only the frontend preflight and write the "
            "Research-and-Paper-Discovery execution plan without launching npm, pytest, shards, or fixture work."
        ),
    )
    parser.add_argument(
        "--phase-profile-plan-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_PATH,
        help="Output path for the Research-and-Paper-Discovery phase profile plan JSON.",
    )
    parser.add_argument(
        "--verify-phase-profile-plan",
        type=Path,
        help="Verify an existing Research-and-Paper-Discovery phase profile plan instead of running certification gates.",
    )
    parser.add_argument(
        "--phase-profile-plan-verification-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_PROFILE_PLAN_VERIFICATION_PATH,
        help="Output path for --verify-phase-profile-plan verification JSON.",
    )
    parser.add_argument(
        "--phase-run-report-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_PHASE_RUN_REPORT_PATH,
        help="Output path for the terminal Research-and-Paper-Discovery phase run report.",
    )

    parser.add_argument(
        "--verify-phase-run-report",
        type=Path,
        help="Verify an existing terminal Research-and-Paper-Discovery phase run report instead of running certification gates.",
    )
    parser.add_argument(
        "--phase-run-report-verification-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_PATH,
        help="Output path for --verify-phase-run-report verification JSON.",
    )
    parser.add_argument(
        "--researcher-fixture-artifact-root",
        type=Path,
        default=RESEARCHER_FIXTURE_ARTIFACT_ROOT,
        help="Artifact root used by --include-researcher-fixture.",
    )
    parser.add_argument(
        "--researcher-fixture-timeout-seconds",
        type=int,
        default=900,
        help="Per-step watchdog timeout for --include-researcher-fixture.",
    )
    parser.add_argument(
        "--researcher-fixture-heartbeat-seconds",
        type=int,
        default=10,
        help="Heartbeat interval for --include-researcher-fixture.",
    )
    parser.add_argument("--step-timeout-seconds", type=int, default=None, help="Override timeout for canonical local-certify steps.")
    parser.add_argument("--step-heartbeat-seconds", type=int, default=10, help="Heartbeat interval for canonical local-certify steps.")
    parser.add_argument(
        "--verify-report",
        type=Path,
        help="Verify an existing local_certify_report.json instead of running certification gates.",
    )
    parser.add_argument(
        "--verification-output",
        type=Path,
        default=LOCAL_CERTIFY_REPORT_VERIFICATION_PATH,
        help="Output path for --verify-report verification JSON.",
    )
    parser.add_argument(
        "--verify-phase-closure-report",
        type=Path,
        help="Verify an existing Research-and-Paper-Discovery phase closure report instead of running certification gates.",
    )
    parser.add_argument(
        "--phase-closure-verification-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_CLOSURE_VERIFICATION_PATH,
        help="Output path for --verify-phase-closure-report verification JSON.",
    )
    parser.add_argument(
        "--phase-closure-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_CLOSURE_REPORT_PATH,
        help="Output path for the Research-and-Paper-Discovery closure report produced by the phase profile.",
    )
    parser.add_argument(
        "--verify-phase-evidence-bundle",
        type=Path,
        help="Verify an existing Research-and-Paper-Discovery evidence bundle manifest instead of running certification gates.",
    )
    parser.add_argument(
        "--phase-evidence-bundle-verification-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_VERIFICATION_PATH,
        help="Output path for --verify-phase-evidence-bundle verification JSON.",
    )
    parser.add_argument(
        "--export-phase-evidence-bundle",
        type=Path,
        help="Copy an existing Research-and-Paper-Discovery evidence bundle into a portable self-contained directory.",
    )
    parser.add_argument(
        "--phase-evidence-bundle-export-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "local_certify" / "latest" / "research_paper_discovery_evidence_bundle_export",
        help="Output directory for --export-phase-evidence-bundle.",
    )
    parser.add_argument(
        "--phase-evidence-bundle-export-verification-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_EXPORT_VERIFICATION_PATH,
        help="Output path for --export-phase-evidence-bundle replay/export verification JSON.",
    )
    parser.add_argument(
        "--phase-evidence-bundle-output",
        type=Path,
        default=RESEARCH_PAPER_DISCOVERY_EVIDENCE_BUNDLE_PATH,
        help="Output path for the Research-and-Paper-Discovery evidence bundle manifest produced by the phase profile.",
    )
    parser.add_argument(
        "--verify-final-phase-certificate",
        type=Path,
        help="Verify the human-readable final Research-and-Paper-Discovery certificate and write its machine-readable index.",
    )
    parser.add_argument(
        "--final-phase-certificate-index-output",
        type=Path,
        default=FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_INDEX_PATH,
        help="Output path for --verify-final-phase-certificate machine-readable index JSON.",
    )
    parser.add_argument(
        "--final-phase-certificate-verification-output",
        type=Path,
        default=FINAL_RESEARCH_PAPER_DISCOVERY_CERTIFICATE_VERIFICATION_PATH,
        help="Output path for --verify-final-phase-certificate verification JSON.",
    )
    parser.add_argument(
        "--local-certify-report-output",
        type=Path,
        default=None,
        help=(
            "Override where local_certify_report.json is written and consumed for this process "
            "(default: artifacts/local_certify/latest). Intended for isolated subprocess tests."
        ),
    )
    parser.add_argument(
        "--frontend-preflight-report-output",
        type=Path,
        default=None,
        help="Override output path for frontend_preflight_report.json for this process.",
    )
    parser.add_argument(
        "--python-core-report-output",
        type=Path,
        default=None,
        help="Override output path for python_core_report.json for this process.",
    )
    args = parser.parse_args(argv)

    if args.verify_final_phase_certificate is not None:
        verification = verify_final_research_paper_discovery_certification(
            args.verify_final_phase_certificate,
            index_output_path=args.final_phase_certificate_index_output,
            verification_output_path=args.final_phase_certificate_verification_output,
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification.get("status") != "PASS":
            print(
                f"Final Research-and-Paper-Discovery certificate verification: FAIL ({args.verify_final_phase_certificate})",
                file=sys.stderr,
            )
            print(
                "Final Research-and-Paper-Discovery certificate verification: "
                f"written to {args.final_phase_certificate_verification_output}",
                file=sys.stderr,
            )
            return 1
        print("Final Research-and-Paper-Discovery certificate verification: PASS")
        print(
            "Final Research-and-Paper-Discovery certificate verification: "
            f"written to {args.final_phase_certificate_verification_output}"
        )
        return 0

    if args.verify_phase_profile_plan is not None:
        verification = verify_research_paper_discovery_profile_plan(
            args.verify_phase_profile_plan,
            output_path=args.phase_profile_plan_verification_output,
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        return 0 if verification.get("status") == "PASS" else 1

    if args.verify_phase_run_report is not None:
        phase_run_summary, phase_run_blockers = validate_research_paper_discovery_phase_run_report(
            args.verify_phase_run_report
        )
        verification = {
            "schema_version": RESEARCH_PAPER_DISCOVERY_PHASE_RUN_VERIFICATION_SCHEMA_VERSION,
            "status": "PASS" if not phase_run_blockers else "FAIL",
            "blockers": phase_run_blockers,
            "phase_run_report_path": str(args.verify_phase_run_report),
            "phase_run_report_sha256": (
                _file_sha256(args.verify_phase_run_report) if args.verify_phase_run_report.exists() else None
            ),
            "phase_run_report": phase_run_summary,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        args.phase_run_report_verification_output.parent.mkdir(parents=True, exist_ok=True)
        args.phase_run_report_verification_output.write_text(
            json.dumps(verification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification["status"] != "PASS":
            print(
                f"Research-and-Paper-Discovery phase run report verification: FAIL ({args.verify_phase_run_report})",
                file=sys.stderr,
            )
            print(
                "Research-and-Paper-Discovery phase run report verification: "
                f"written to {args.phase_run_report_verification_output}",
                file=sys.stderr,
            )
            return 1
        print("Research-and-Paper-Discovery phase run report verification: PASS")
        print(
            "Research-and-Paper-Discovery phase run report verification: "
            f"written to {args.phase_run_report_verification_output}"
        )
        return 0

    if args.export_phase_evidence_bundle is not None:
        export_payload, export_blockers = export_research_paper_discovery_evidence_bundle(
            bundle_path=args.export_phase_evidence_bundle,
            export_dir=args.phase_evidence_bundle_export_dir,
        )
        exported_bundle_path = args.phase_evidence_bundle_export_dir / "research_paper_discovery_evidence_bundle.json"
        verification = {
            "schema_version": "research_paper_discovery_evidence_bundle_export/v1",
            "status": "PASS" if not export_blockers else "FAIL",
            "blockers": export_blockers,
            "source_bundle_path": str(args.export_phase_evidence_bundle),
            "source_bundle_sha256": _file_sha256(args.export_phase_evidence_bundle) if args.export_phase_evidence_bundle.exists() else None,
            "export_dir": str(args.phase_evidence_bundle_export_dir),
            "exported_bundle_path": str(exported_bundle_path),
            "exported_bundle_sha256": _file_sha256(exported_bundle_path) if exported_bundle_path.exists() else None,
            "exported_bundle_seal_path": str(_evidence_bundle_seal_path_for(exported_bundle_path)),
            "exported_bundle_seal_sha256": (
                _file_sha256(_evidence_bundle_seal_path_for(exported_bundle_path))
                if _evidence_bundle_seal_path_for(exported_bundle_path).exists()
                else None
            ),
            "exported_phase_run_report_path": (
                str(exported_bundle_path.parent / _artifact_row_by_proof_name(export_payload.get("artifacts", []) if isinstance(export_payload, dict) else [], "research_paper_discovery_phase_run_report").get("path"))
                if isinstance(export_payload, dict) and _artifact_row_by_proof_name(export_payload.get("artifacts", []), "research_paper_discovery_phase_run_report") is not None
                else None
            ),
            "exported_phase_run_report_verification_path": (
                str(exported_bundle_path.parent / _artifact_row_by_proof_name(export_payload.get("artifacts", []) if isinstance(export_payload, dict) else [], "research_paper_discovery_phase_run_report_verification").get("path"))
                if isinstance(export_payload, dict) and _artifact_row_by_proof_name(export_payload.get("artifacts", []), "research_paper_discovery_phase_run_report_verification") is not None
                else None
            ),
            "exported_final_phase_certificate_index_path": (
                str(exported_bundle_path.parent / _artifact_row_by_proof_name(export_payload.get("artifacts", []) if isinstance(export_payload, dict) else [], "final_research_paper_discovery_certification_index").get("path"))
                if isinstance(export_payload, dict) and _artifact_row_by_proof_name(export_payload.get("artifacts", []), "final_research_paper_discovery_certification_index") is not None
                else None
            ),
            "exported_final_phase_certificate_verification_path": (
                str(exported_bundle_path.parent / _artifact_row_by_proof_name(export_payload.get("artifacts", []) if isinstance(export_payload, dict) else [], "final_research_paper_discovery_certification_verification").get("path"))
                if isinstance(export_payload, dict) and _artifact_row_by_proof_name(export_payload.get("artifacts", []), "final_research_paper_discovery_certification_verification") is not None
                else None
            ),
            "bundle": export_payload,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
        args.phase_evidence_bundle_export_verification_output.parent.mkdir(parents=True, exist_ok=True)
        args.phase_evidence_bundle_export_verification_output.write_text(
            json.dumps(verification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification["status"] != "PASS":
            print(f"Research-and-Paper-Discovery evidence bundle export: FAIL ({args.export_phase_evidence_bundle})", file=sys.stderr)
            print(f"Research-and-Paper-Discovery evidence bundle export verification: written to {args.phase_evidence_bundle_export_verification_output}", file=sys.stderr)
            return 1
        print("Research-and-Paper-Discovery evidence bundle export: PASS")
        print(f"Research-and-Paper-Discovery evidence bundle export verification: written to {args.phase_evidence_bundle_export_verification_output}")
        return 0

    if args.verify_phase_evidence_bundle is not None:
        bundle_payload, bundle_blockers = validate_research_paper_discovery_evidence_bundle(args.verify_phase_evidence_bundle)
        verification = {
            "schema_version": "research_paper_discovery_evidence_bundle_verification/v1",
            "status": "PASS" if not bundle_blockers else "FAIL",
            "blockers": bundle_blockers,
            "bundle_path": str(args.verify_phase_evidence_bundle),
            "bundle_sha256": _file_sha256(args.verify_phase_evidence_bundle) if args.verify_phase_evidence_bundle.exists() else None,
            "bundle_seal_path": str(_evidence_bundle_seal_path_for(args.verify_phase_evidence_bundle)),
            "bundle_seal_sha256": (
                _file_sha256(_evidence_bundle_seal_path_for(args.verify_phase_evidence_bundle))
                if _evidence_bundle_seal_path_for(args.verify_phase_evidence_bundle).exists()
                else None
            ),
            "bundle": bundle_payload,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        args.phase_evidence_bundle_verification_output.parent.mkdir(parents=True, exist_ok=True)
        args.phase_evidence_bundle_verification_output.write_text(
            json.dumps(verification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification["status"] != "PASS":
            print(f"Research-and-Paper-Discovery evidence bundle verification: FAIL ({args.verify_phase_evidence_bundle})", file=sys.stderr)
            print(f"Research-and-Paper-Discovery evidence bundle verification: written to {args.phase_evidence_bundle_verification_output}", file=sys.stderr)
            return 1
        print("Research-and-Paper-Discovery evidence bundle verification: PASS")
        print(f"Research-and-Paper-Discovery evidence bundle verification: written to {args.phase_evidence_bundle_verification_output}")
        return 0

    if args.verify_phase_closure_report is not None:
        closure_payload, closure_blockers = validate_research_paper_discovery_closure_report(args.verify_phase_closure_report)
        verification = {
            "schema_version": "research_paper_discovery_closure_verification/v1",
            "status": "PASS" if not closure_blockers else "FAIL",
            "blockers": closure_blockers,
            "closure_report_path": str(args.verify_phase_closure_report),
            "closure_report_sha256": _file_sha256(args.verify_phase_closure_report) if args.verify_phase_closure_report.exists() else None,
            "closure_report": closure_payload,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        args.phase_closure_verification_output.parent.mkdir(parents=True, exist_ok=True)
        args.phase_closure_verification_output.write_text(
            json.dumps(verification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification["status"] != "PASS":
            print(f"Research-and-Paper-Discovery closure verification: FAIL ({args.verify_phase_closure_report})", file=sys.stderr)
            print(f"Research-and-Paper-Discovery closure verification: written to {args.phase_closure_verification_output}", file=sys.stderr)
            return 1
        print("Research-and-Paper-Discovery closure verification: PASS")
        print(f"Research-and-Paper-Discovery closure verification: written to {args.phase_closure_verification_output}")
        return 0

    if args.verify_report is not None:
        verification = verify_local_certify_report(args.verify_report, output_path=args.verification_output)
        if args.json:
            print(json.dumps(verification, indent=2, sort_keys=True))
        if verification["status"] != "PASS":
            print(f"local_certify report verification: FAIL ({args.verify_report})", file=sys.stderr)
            print(f"local_certify report verification: written to {args.verification_output}", file=sys.stderr)
            return 1
        print("local_certify report verification: PASS")
        print(f"local_certify report verification: written to {args.verification_output}")
        return 0

    with _temporary_certify_artifact_paths(args):
        apply_research_paper_discovery_profile(args)
        frontend_included = not args.skip_frontend and (FRONTEND_ROOT / "package-lock.json").exists()
        results: list[LocalCertifyStep] = []
        failed: LocalCertifyStep | None = None
        frontend_preflight_report_summary: dict[str, object] | None = None
        preflight_blockers: list[str] = []
        if args.certify_research_paper_discovery:
            preflight_started = time.perf_counter()
            write_frontend_preflight_report(
                skip_frontend_requested=args.skip_frontend,
                output_path=FRONTEND_PREFLIGHT_REPORT_PATH,
            )
            frontend_preflight_report_summary, preflight_blockers = validate_frontend_preflight_report(
                FRONTEND_PREFLIGHT_REPORT_PATH
            )
            preflight_step = _proof_report_step(
                step_name="frontend_preflight",
                validator_name="validate_frontend_preflight_report",
                summary=frontend_preflight_report_summary,
                blockers=preflight_blockers,
                report_path=FRONTEND_PREFLIGHT_REPORT_PATH,
                started=preflight_started,
            )
            results.append(preflight_step)
            if preflight_step.exit_code != 0:
                failed = preflight_step
        monolithic_pytest_included = (not args.include_pytest_shards) or args.run_monolithic_pytest_with_shards
        phase_preflight_failed = failed is not None and args.certify_research_paper_discovery
        steps_to_run = build_research_paper_discovery_steps(
            args,
            frontend_included=frontend_included,
            phase_preflight_failed=phase_preflight_failed,
        )
        phase_profile_plan_report_summary: dict[str, object] | None = None
        phase_profile_plan_verification: dict[str, object] | None = None
        if args.certify_research_paper_discovery:
            plan_payload = write_research_paper_discovery_profile_plan(
                args=args,
                frontend_included=frontend_included,
                frontend_preflight_report=frontend_preflight_report_summary,
                frontend_preflight_blockers=preflight_blockers,
                phase_preflight_failed=phase_preflight_failed,
                steps_to_run=steps_to_run,
                output_path=args.phase_profile_plan_output,
            )
            phase_profile_plan_report_summary, plan_blockers = validate_research_paper_discovery_profile_plan(
                args.phase_profile_plan_output
            )
            phase_profile_plan_verification = verify_research_paper_discovery_profile_plan(
                args.phase_profile_plan_output,
                output_path=args.phase_profile_plan_verification_output,
            )
            if args.phase_profile_plan_only:
                if args.json:
                    print(json.dumps(plan_payload, indent=2, sort_keys=True))
                if plan_blockers:
                    print("Research-and-Paper-Discovery phase profile plan: FAIL", file=sys.stderr)
                    for blocker in plan_blockers:
                        print(f"local_certify: {blocker}", file=sys.stderr)
                    print(f"Research-and-Paper-Discovery phase profile plan: written to {args.phase_profile_plan_output}", file=sys.stderr)
                    return 1
                print("Research-and-Paper-Discovery phase profile plan: PASS")
                print(f"Research-and-Paper-Discovery phase profile plan: written to {args.phase_profile_plan_output}")
                return 0
    
        frontend_certify_report_summary: dict[str, object] | None = None
        frontend_clean_workspace_report_summary: dict[str, object] | None = None
        python_core_report_summary: dict[str, object] | None = None
        public_surface_dashboard_summary: dict[str, object] | None = None
        package_repo_check_summary: dict[str, object] | None = None
        researcher_fixture_report_summary: dict[str, object] | None = None
        collection_shards_proof_summary: dict[str, object] | None = None
        constitutional_shards_proof_summary: dict[str, object] | None = None
        pytest_execution_shards_proof_summary: dict[str, object] | None = None
        deferred_resumable_failure: LocalCertifyStep | None = None
        for name, command, cwd in steps_to_run:
            if name == "frontend_clean_workspace":
                FRONTEND_CLEAN_WORKSPACE_REPORT_PATH.unlink(missing_ok=True)
            if name == "frontend_certify":
                FRONTEND_CERTIFY_REPORT_PATH.unlink(missing_ok=True)
            if name == "public_surface_dashboard":
                PUBLIC_SURFACE_DASHBOARD_REPORT_PATH.unlink(missing_ok=True)
            if name == "package_repo_check":
                PACKAGE_REPO_CHECK_REPORT_PATH.unlink(missing_ok=True)
            if name == "researcher_fixture":
                RESEARCHER_FIXTURE_REPORT_PATH.unlink(missing_ok=True)
            step_env: dict[str, str] | None = None
            if name == "frontend_certify":
                step_env = {"FRONTEND_CERTIFY_REPORT": str(FRONTEND_CERTIFY_REPORT_PATH)}
            if name in ("frontend_npm_ci", "frontend_certify"):
                step_env = {**(step_env or {}), **_npm_public_registry_env()}
            result = _run(
                name,
                command,
                cwd=cwd,
                extra_env=step_env,
                timeout_seconds=_local_wrapper_timeout_for_step(name, args),
                heartbeat_seconds=args.step_heartbeat_seconds,
            )
            results.append(result)
            if result.exit_code != 0 and _is_resumable_proof_step(name) and deferred_resumable_failure is None:
                deferred_resumable_failure = result
            if result.exit_code != 0 and failed is None and not _is_resumable_proof_step(name):
                failed = result
                if not args.no_fail_fast:
                    break
            if name == "frontend_clean_workspace":
                validation_started = time.perf_counter()
                frontend_clean_workspace_report_summary, blockers = validate_frontend_clean_workspace_report(
                    FRONTEND_CLEAN_WORKSPACE_REPORT_PATH
                )
                validation_step = _proof_report_step(
                    step_name="frontend_clean_workspace_report_validation",
                    validator_name="validate_frontend_clean_workspace_report",
                    summary=frontend_clean_workspace_report_summary,
                    blockers=blockers,
                    report_path=FRONTEND_CLEAN_WORKSPACE_REPORT_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = validation_step
                    if not args.no_fail_fast:
                        break
            if name == "frontend_certify":
                validation_started = time.perf_counter()
                frontend_certify_report_summary, blockers = validate_frontend_certify_report(FRONTEND_CERTIFY_REPORT_PATH)
                validation_step = _frontend_certify_report_step(
                    summary=frontend_certify_report_summary,
                    blockers=blockers,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = validation_step
                    if not args.no_fail_fast:
                        break
            if name == "public_surface_dashboard":
                validation_started = time.perf_counter()
                public_surface_dashboard_summary, blockers = validate_public_surface_dashboard_report(
                    PUBLIC_SURFACE_DASHBOARD_REPORT_PATH
                )
                validation_step = _proof_report_step(
                    step_name="public_surface_dashboard_report_validation",
                    validator_name="validate_public_surface_dashboard_report",
                    summary=public_surface_dashboard_summary,
                    blockers=blockers,
                    report_path=PUBLIC_SURFACE_DASHBOARD_REPORT_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = validation_step
                    if not args.no_fail_fast:
                        break
            if name == "package_repo_check":
                validation_started = time.perf_counter()
                package_repo_check_summary, blockers = validate_package_repo_check_report(PACKAGE_REPO_CHECK_REPORT_PATH)
                validation_step = _proof_report_step(
                    step_name="package_repo_check_report_validation",
                    validator_name="validate_package_repo_check_report",
                    summary=package_repo_check_summary,
                    blockers=blockers,
                    report_path=PACKAGE_REPO_CHECK_REPORT_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = validation_step
                    if not args.no_fail_fast:
                        break
            if name == "researcher_fixture":
                validation_started = time.perf_counter()
                researcher_fixture_report_summary, blockers = validate_researcher_fixture_report(RESEARCHER_FIXTURE_REPORT_PATH)
                validation_step = _proof_report_step(
                    step_name="researcher_fixture_report_validation",
                    validator_name="validate_researcher_fixture_report",
                    summary=researcher_fixture_report_summary,
                    blockers=blockers,
                    report_path=RESEARCHER_FIXTURE_REPORT_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = validation_step
                    if not args.no_fail_fast:
                        break
            if name == "collection_shards_summary_verification":
                validation_started = time.perf_counter()
                collection_shards_proof_summary, blockers = validate_collection_shards_proof(
                    COLLECTION_SHARDS_SUMMARY_PATH,
                    COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH,
                )
                validation_step = _shard_proof_report_step(
                    step_name="collection_shards_report_validation",
                    validator_name="validate_collection_shards_proof",
                    summary=collection_shards_proof_summary,
                    blockers=blockers,
                    summary_path=COLLECTION_SHARDS_SUMMARY_PATH,
                    verification_path=COLLECTION_SHARDS_SUMMARY_VERIFICATION_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = deferred_resumable_failure or validation_step
                    if not args.no_fail_fast:
                        break
            if name == "constitutional_shards_summary_verification":
                validation_started = time.perf_counter()
                constitutional_shards_proof_summary, blockers = validate_constitutional_shards_proof(
                    CONSTITUTIONAL_SHARDS_SUMMARY_PATH,
                    CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH,
                )
                validation_step = _shard_proof_report_step(
                    step_name="constitutional_shards_report_validation",
                    validator_name="validate_constitutional_shards_proof",
                    summary=constitutional_shards_proof_summary,
                    blockers=blockers,
                    summary_path=CONSTITUTIONAL_SHARDS_SUMMARY_PATH,
                    verification_path=CONSTITUTIONAL_SHARDS_SUMMARY_VERIFICATION_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = deferred_resumable_failure or validation_step
                    if not args.no_fail_fast:
                        break
            if name == "pytest_execution_shards_summary_verification":
                validation_started = time.perf_counter()
                pytest_execution_shards_proof_summary, blockers = validate_pytest_execution_shards_proof(
                    PYTEST_EXECUTION_SHARDS_SUMMARY_PATH,
                    PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH,
                )
                validation_step = _shard_proof_report_step(
                    step_name="pytest_execution_shards_report_validation",
                    validator_name="validate_pytest_execution_shards_proof",
                    summary=pytest_execution_shards_proof_summary,
                    blockers=blockers,
                    summary_path=PYTEST_EXECUTION_SHARDS_SUMMARY_PATH,
                    verification_path=PYTEST_EXECUTION_SHARDS_SUMMARY_VERIFICATION_PATH,
                    started=validation_started,
                )
                results.append(validation_step)
                if args.include_pytest_shards and not monolithic_pytest_included:
                    replacement_started = time.perf_counter()
                    pytest_replacement_step = _pytest_execution_shards_replacement_step(
                        summary=pytest_execution_shards_proof_summary,
                        blockers=blockers,
                        started=replacement_started,
                    )
                    results.append(pytest_replacement_step)
                if validation_step.exit_code != 0 and failed is None:
                    failed = deferred_resumable_failure or validation_step
                    if not args.no_fail_fast:
                        break
    
        if failed is None and deferred_resumable_failure is not None:
            failed = deferred_resumable_failure
    
        python_core_report_payload = _write_python_core_report(results=results, failed=failed, report_path=PYTHON_CORE_REPORT_PATH)
        validation_started = time.perf_counter()
        python_core_report_summary, blockers = validate_python_core_report(PYTHON_CORE_REPORT_PATH)
        python_core_validation_step = _proof_report_step(
            step_name="python_core_report_validation",
            validator_name="validate_python_core_report",
            summary=python_core_report_summary,
            blockers=blockers,
            report_path=PYTHON_CORE_REPORT_PATH,
            started=validation_started,
        )
        results.append(python_core_validation_step)
        if python_core_validation_step.exit_code != 0 and failed is None:
            failed = python_core_validation_step
    
        payload = _build_payload(
            results=results,
            failed=failed,
            frontend_included=frontend_included,
            frontend_clean_workspace_included=bool(frontend_included and args.clean_frontend_workspace),
            researcher_fixture_included=args.include_researcher_fixture,
            collection_shards_included=args.include_collection_shards,
            collection_shard_count=args.collection_shard_count if args.include_collection_shards else None,
            constitutional_shards_included=args.include_constitutional_shards,
            constitutional_shard_count=args.constitutional_shard_count if args.include_constitutional_shards else None,
            pytest_execution_shards_included=args.include_pytest_shards,
            pytest_shard_count=args.pytest_shard_count if args.include_pytest_shards else None,
            monolithic_pytest_included=monolithic_pytest_included,
            pytest_execution_shards_replace_monolith=args.include_pytest_shards and not monolithic_pytest_included,
            frontend_certify_report=frontend_certify_report_summary,
            frontend_clean_workspace_report=frontend_clean_workspace_report_summary,
            frontend_preflight_report=frontend_preflight_report_summary,
            phase_profile_plan_report=phase_profile_plan_report_summary,
            python_core_report=python_core_report_summary,
            public_surface_dashboard=public_surface_dashboard_summary,
            package_repo_check=package_repo_check_summary,
            researcher_fixture_report=researcher_fixture_report_summary,
            collection_shards_proof=collection_shards_proof_summary,
            constitutional_shards_proof=constitutional_shards_proof_summary,
            pytest_execution_shards_proof=pytest_execution_shards_proof_summary,
            certification_profile=RESEARCH_PAPER_DISCOVERY_PROFILE if args.certify_research_paper_discovery else None,
            certification_profile_contract=(
                _research_paper_discovery_profile_contract(frontend_included=frontend_included)
                if args.certify_research_paper_discovery
                else None
            ),
        )
        _write_report(payload)
        phase_closure_report: dict[str, object] | None = None
        phase_evidence_bundle: dict[str, object] | None = None
        phase_run_report: dict[str, object] | None = None
        final_certificate_index: dict[str, object] | None = None
        report_verification: dict[str, object] | None = None
        phase_profile_blockers: list[str] = []
        if args.certify_research_paper_discovery:
            report_verification = verify_local_certify_report(REPORT_PATH, output_path=args.verification_output)
            if report_verification.get("status") != "PASS":
                phase_profile_blockers.append(
                    "RESEARCH_PAPER_DISCOVERY_PROFILE_LOCAL_CERTIFY_REPORT_VERIFICATION_NOT_PASSING:"
                    f"{report_verification.get('status')}"
                )
            phase_closure_report = write_research_paper_discovery_closure_report(
                payload,
                report_verification,
                output_path=args.phase_closure_output,
                report_path=REPORT_PATH,
                verification_path=args.verification_output,
            )
            if phase_closure_report.get("status") != "PASS":
                phase_profile_blockers.append(
                    "RESEARCH_PAPER_DISCOVERY_PROFILE_CLOSURE_NOT_PASSING:"
                    f"{phase_closure_report.get('status')}"
                )
            phase_evidence_bundle = write_research_paper_discovery_evidence_bundle(
                local_report_path=REPORT_PATH,
                verification_path=args.verification_output,
                closure_path=args.phase_closure_output,
                phase_profile_plan_path=args.phase_profile_plan_output,
                phase_profile_plan_verification_path=args.phase_profile_plan_verification_output,
                output_path=args.phase_evidence_bundle_output,
            )
            if phase_evidence_bundle.get("status") != "PASS":
                phase_profile_blockers.append(
                    "RESEARCH_PAPER_DISCOVERY_PROFILE_EVIDENCE_BUNDLE_NOT_PASSING:"
                    f"{phase_evidence_bundle.get('status')}"
                )
            phase_run_report = write_research_paper_discovery_phase_run_report(
                local_certify_payload=payload,
                local_report_path=REPORT_PATH,
                local_report_verification=report_verification,
                local_report_verification_path=args.verification_output,
                phase_profile_plan_report=phase_profile_plan_report_summary,
                phase_profile_plan_path=args.phase_profile_plan_output,
                phase_profile_plan_verification=phase_profile_plan_verification,
                phase_profile_plan_verification_path=args.phase_profile_plan_verification_output,
                phase_closure_report=phase_closure_report,
                phase_closure_path=args.phase_closure_output,
                phase_evidence_bundle=phase_evidence_bundle,
                phase_evidence_bundle_path=args.phase_evidence_bundle_output,
                phase_profile_blockers=phase_profile_blockers,
                output_path=args.phase_run_report_output,
            )
            final_certificate_index = write_final_research_paper_discovery_certification_index(
                output_path=args.final_phase_certificate_index_output,
            )
        if args.json:
            if phase_closure_report is not None:
                payload = dict(payload)
                payload["phase_closure_report"] = phase_closure_report
                payload["phase_closure_report_path"] = str(args.phase_closure_output)
            if phase_evidence_bundle is not None:
                payload = dict(payload)
                payload["phase_evidence_bundle"] = phase_evidence_bundle
                payload["phase_evidence_bundle_path"] = str(args.phase_evidence_bundle_output)
            if phase_run_report is not None:
                payload = dict(payload)
                payload["phase_run_report"] = phase_run_report
                payload["phase_run_report_path"] = str(args.phase_run_report_output)
            if final_certificate_index is not None:
                payload = dict(payload)
                payload["final_phase_certificate_index"] = final_certificate_index
                payload["final_phase_certificate_index_path"] = str(args.final_phase_certificate_index_output)
            print(json.dumps(payload, indent=2, sort_keys=True))
        if failed is not None:
            print(f"\nlocal_certify: FAIL at {failed.name} (exit {failed.exit_code})", file=sys.stderr)
            print(f"local_certify: report written to {REPORT_PATH}", file=sys.stderr)
            return failed.exit_code or 1
        if phase_profile_blockers:
            print("\nlocal_certify: FAIL at research_paper_discovery_profile_validation", file=sys.stderr)
            for blocker in phase_profile_blockers:
                print(f"local_certify: {blocker}", file=sys.stderr)
            print(f"local_certify: report written to {REPORT_PATH}", file=sys.stderr)
            return 1
        print("\nlocal_certify: PASS")
        print(f"local_certify: report written to {REPORT_PATH}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
