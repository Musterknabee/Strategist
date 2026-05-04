from __future__ import annotations

import argparse
import ast
import json
import signal
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import (  # noqa: E402
    PathIntegrityError,
    safe_input_dir,
    symlink_components_preserving_path,
)

# Whole-repo ownership roots are available for local package-sliced diagnostics,
# but the default gate stays on the high-gravity set so CI/release assessment
# remains deterministic in constrained runners.
REPO_OWNED_ROOTS = ("strategy_validator", "scripts", "tests")

HIGH_GRAVITY_ROOTS = (
    "strategy_validator/application/ui_command_actions.py",
    "strategy_validator/application/ui_command_policy.py",
    "strategy_validator/application/ui_public_facade.py",
    "strategy_validator/application/public_surface.py",
    "strategy_validator/application/operator_action_projection.py",
    "strategy_validator/application/ui_workboard_intelligence_policy.py",
    "strategy_validator/application/release_publication_paths.py",
    "strategy_validator/application/strategic_horizon_readiness.py",
    "strategy_validator/application/strategy_validation_vertical.py",
    "strategy_validator/api/app.py",
    "strategy_validator/api/auth.py",
    "strategy_validator/api/security.py",
    "strategy_validator/api/routes/readiness.py",
    "strategy_validator/contracts/ui_public_facade.py",
    "strategy_validator/cli/hygiene_check.py",
    "strategy_validator/cli/release_candidate.py",
    "strategy_validator/cli/single_tenant_preflight.py",
    "strategy_validator/cli/deployment_env_check.py",
    "strategy_validator/cli/single_tenant_deployment_bundle.py",
    "strategy_validator/cli/single_tenant_deployment_acceptance.py",
    "strategy_validator/cli/single_tenant_deployment_evidence.py",
    "strategy_validator/core/config.py",
    "strategy_validator/core/path_guards.py",
    "strategy_validator/core/provider_url_policy.py",
    "strategy_validator/ledger/_append_only.py",
    "strategy_validator/ledger/operator_actions.py",
    "strategy_validator/ledger/writer/__init__.py",
    "strategy_validator/validator/orchestrator/__init__.py",
    "strategy_validator/validator/oracle_campaign_execution.py",
    "strategy_validator/validator/oracle_doctrine_adaptation.py",
    "strategy_validator/validator/oracle_opportunity_queue.py",
    "strategy_validator/validator/oracle_research_execution_memory.py",
    "strategy_validator/validator/oracle_research_planner.py",
    "strategy_validator/validator/oracle_scenario_lab.py",
    "strategy_validator/validator/oracle_signal_fusion_rendering.py",
    "strategy_validator/validator/oracle_strategic_briefing_rendering.py",
    "strategy_validator/validator/oracle_strategy_cohort.py",
    "strategy_validator/validator/oracle_thesis_memory.py",
    "strategy_validator/validator/strategy_health_posterior.py",
    "scripts/architecture_health_report.py",
    "scripts/environment_check.py",
    "scripts/package_repo.py",
    "scripts/migration_truth_check.py",
    "scripts/repository_truth_check.py",
    "scripts/verify_repo_archive.py",
    "scripts/openapi_contract_snapshot.py",
    "scripts/ui_facade_contract_snapshot.py",
    "scripts/single_tenant_api_smoke.py",
    "scripts/ci_local_verify.py",
    "scripts/verify_frontend.py",
    "tests/api/test_ui_public_facade_snapshot_contract.py",
    "tests/constitutional/test_ui_public_facade_snapshot_assets.py",
    "tests/constitutional/test_single_tenant_deployment_preflight.py",
    "tests/constitutional/test_single_tenant_deployment_env_check.py",
    "tests/constitutional/test_single_tenant_api_smoke_script.py",
    "tests/constitutional/test_source_health_scan_root_path_integrity.py",
    "tests/constitutional/test_single_tenant_deployment_bundle.py",
    "tests/constitutional/test_single_tenant_deployment_acceptance.py",
    "tests/constitutional/test_single_tenant_deployment_evidence.py",
    "tests/constitutional/test_verify_frontend_script.py",
    "tests/constitutional/test_repo_archive_path_integrity.py",
    "tests/constitutional/test_repository_truth_docs_path_integrity.py",
    "tests/constitutional/test_repository_truth_sqlite_migration_path_integrity.py",
    "tests/constitutional/test_sqlite_migration_path_integrity.py",
    "scripts/source_health.py",
)
DEFAULT_ROOTS = HIGH_GRAVITY_ROOTS
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}


@dataclass(frozen=True)
class SourceHealthFailure:
    path: str
    error_type: str
    message: str
    lineno: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class SourceHealthReport:
    schema_version: str
    status: str
    checked_file_count: int
    failure_count: int
    roots: tuple[str, ...]
    failures: tuple[SourceHealthFailure, ...]
    missing_roots: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "checked_file_count": self.checked_file_count,
            "failure_count": self.failure_count,
            "missing_root_count": len(self.missing_roots),
            "roots": list(self.roots),
            "missing_roots": list(self.missing_roots),
            "failures": [asdict(failure) for failure in self.failures],
        }


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def _scan_root_path(repo_root: Path, raw_root: str) -> Path:
    root_arg = Path(raw_root)
    if root_arg.is_absolute():
        raise PathIntegrityError(
            code="SOURCE_HEALTH_SCAN_ROOT_ABSOLUTE",
            path=str(root_arg),
            detail="source-health scan roots must be repository-relative",
        )
    if ".." in root_arg.parts:
        raise PathIntegrityError(
            code="SOURCE_HEALTH_SCAN_ROOT_PARENT_TRAVERSAL",
            path=raw_root,
            detail="source-health scan roots must not contain parent traversal",
        )
    target = repo_root / root_arg
    symlinks = symlink_components_preserving_path(target)
    if symlinks:
        final_component = target in symlinks
        code = (
            "SOURCE_HEALTH_SCAN_ROOT_IS_SYMLINK"
            if final_component
            else "SOURCE_HEALTH_SCAN_ROOT_PARENT_IS_SYMLINK"
        )
        detail_prefix = "symlinked scan root" if final_component else "symlinked scan-root parent directories"
        raise PathIntegrityError(
            code=code,
            path=str(target),
            detail=f"{detail_prefix}: {', '.join(str(item) for item in symlinks)}",
        )
    return target


def _validate_scan_roots(
    repo_root: Path, roots: Sequence[str]
) -> tuple[tuple[Path, ...], tuple[str, ...], tuple[SourceHealthFailure, ...]]:
    paths: list[Path] = []
    missing: list[str] = []
    failures: list[SourceHealthFailure] = []
    for raw_root in roots:
        try:
            root = _scan_root_path(repo_root, raw_root)
        except PathIntegrityError as exc:
            failures.append(SourceHealthFailure(path=exc.path, error_type=exc.code, message=exc.detail))
            continue
        if not root.exists():
            missing.append(raw_root)
            continue
        paths.append(root)
    return tuple(paths), tuple(missing), tuple(failures)


def _iter_python_files(repo_root: Path, root_paths: Sequence[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in root_paths:
        if root.is_file():
            try:
                rel = root.relative_to(repo_root)
            except ValueError:
                continue
            if root.suffix == ".py" and not _is_skipped(rel) and root not in seen:
                seen.add(root)
                yield root
            continue
        for path in sorted(root.rglob("*.py"), key=lambda p: p.as_posix()):
            try:
                rel = path.relative_to(repo_root)
            except ValueError:
                continue
            if _is_skipped(rel):
                continue
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def _source_file_path_integrity_failure(repo_root: Path, path: Path) -> SourceHealthFailure | None:
    symlinks = symlink_components_preserving_path(path)
    if not symlinks:
        return None
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel = str(path)
    final_component = path in symlinks
    code = "SOURCE_HEALTH_FILE_IS_SYMLINK" if final_component else "SOURCE_HEALTH_FILE_PARENT_IS_SYMLINK"
    detail_prefix = "symlinked source file" if final_component else "symlinked source-file parent directories"
    return SourceHealthFailure(
        path=rel,
        error_type=code,
        message=f"{detail_prefix}: {', '.join(str(item) for item in symlinks)}",
    )


class _ParseTimeoutError(TimeoutError):
    pass


def _parse_source_with_timeout(source: str, *, filename: str, timeout_s: float) -> None:
    # A bounded parse timer keeps the syntax gate fail-fast on pathological
    # source while remaining side-effect-free. Set timeout_s=0 to disable it.
    if timeout_s <= 0 or not hasattr(signal, "SIGALRM"):
        ast.parse(source, filename=filename)
        return

    previous_handler = signal.getsignal(signal.SIGALRM)

    def _handle_timeout(signum, frame):  # type: ignore[no-untyped-def]
        raise _ParseTimeoutError(f"syntax parse timed out after {timeout_s:g}s")

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_s)
    try:
        ast.parse(source, filename=filename)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def run_source_health(
    *,
    repo_root: str | Path | None = None,
    roots: Sequence[str] = DEFAULT_ROOTS,
    per_file_timeout_s: float = 1.0,
) -> SourceHealthReport:
    failures: list[SourceHealthFailure] = []
    if repo_root is None:
        root = _REPO_ROOT
    else:
        try:
            checked_root = safe_input_dir(repo_root, label="SOURCE_HEALTH_REPO_ROOT", required=True)
        except PathIntegrityError as exc:
            failures.append(SourceHealthFailure(path=exc.path, error_type=exc.code, message=exc.detail))
            return SourceHealthReport(
                schema_version="source_health/v2",
                status="FAIL",
                checked_file_count=0,
                failure_count=len(failures),
                roots=tuple(roots),
                failures=tuple(failures),
                missing_roots=(),
            )
        assert checked_root is not None
        root = checked_root
    root_paths, missing_roots, root_failures = _validate_scan_roots(root, roots)
    failures.extend(root_failures)
    checked = 0
    for path in _iter_python_files(root, root_paths):
        rel = path.relative_to(root).as_posix()
        integrity_failure = _source_file_path_integrity_failure(root, path)
        if integrity_failure is not None:
            failures.append(integrity_failure)
            continue
        checked += 1
        try:
            source = path.read_text(encoding="utf-8")
            _parse_source_with_timeout(source, filename=rel, timeout_s=per_file_timeout_s)
        except _ParseTimeoutError as exc:
            failures.append(SourceHealthFailure(path=rel, error_type="ParseTimeout", message=str(exc)))
        except SyntaxError as exc:
            failures.append(
                SourceHealthFailure(
                    path=rel,
                    error_type="SyntaxError",
                    message=exc.msg,
                    lineno=exc.lineno,
                    offset=exc.offset,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive IO/encoding reporting.
            failures.append(SourceHealthFailure(path=rel, error_type=type(exc).__name__, message=str(exc)))
    return SourceHealthReport(
        schema_version="source_health/v2",
        status="PASS" if not failures and not missing_roots else "FAIL",
        checked_file_count=checked,
        failure_count=len(failures),
        roots=tuple(roots),
        failures=tuple(failures),
        missing_roots=missing_roots,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Side-effect-free Python AST syntax health gate. Defaults to high-gravity source files."
    )
    parser.add_argument("roots", nargs="*", help="Repo-relative roots/files to scan; defaults to the high-gravity source-health scope")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this script's parent repository")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--repo-owned", action="store_true", help="Scan the broader repository-owned Python roots: strategy_validator scripts tests")
    parser.add_argument("--high-gravity", action="store_true", help="Scan only the high-gravity historically fragile source-health scope")
    parser.add_argument(
        "--per-file-timeout",
        type=float,
        default=1.0,
        help="Optional seconds to spend parsing one file; 0 disables signal timers",
    )
    args = parser.parse_args(argv)

    if args.roots:
        roots = tuple(args.roots)
    elif args.repo_owned:
        roots = REPO_OWNED_ROOTS
    else:
        roots = HIGH_GRAVITY_ROOTS
    report = run_source_health(repo_root=args.repo_root, roots=roots, per_file_timeout_s=args.per_file_timeout)
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"source_health: {report.status} checked={report.checked_file_count} "
            f"failures={report.failure_count} missing_roots={len(report.missing_roots)}"
        )
        for missing in report.missing_roots:
            print(f"{missing}: MissingRoot: root/file does not exist")
        for failure in report.failures:
            location = f":{failure.lineno}:{failure.offset}" if failure.lineno is not None else ""
            print(f"{failure.path}{location}: {failure.error_type}: {failure.message}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
