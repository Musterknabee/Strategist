from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import tomllib
from dataclasses import asdict, dataclass
from collections.abc import Mapping
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, safe_input_dir, symlink_components_preserving_path  # noqa: E402
from scripts.sample_secret_hygiene import collect_sample_secret_hygiene_violations  # noqa: E402


@dataclass(frozen=True)
class TruthCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class RepositoryTruthReport:
    schema_version: str
    status: str
    checks: tuple[TruthCheck, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "checks": [asdict(check) for check in self.checks],
        }


def _check(status: bool, name: str, pass_detail: str, fail_detail: str) -> TruthCheck:
    return TruthCheck(name=name, status="PASS" if status else "FAIL", detail=pass_detail if status else fail_detail)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_pyproject(repo_root: Path) -> dict[str, object]:
    with (repo_root / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


_LOCAL_OPS_REGISTRY_SCHEMA = "local_ops_command_registry/v1"
_LOCAL_OPS_REGISTRY_REL = Path("ui/strategist-web/lib/operator/local-ops-command-registry.json")
_LOCAL_OPS_SAFETY = frozenset({"READ_ONLY", "LOCAL_OPERATOR_ACTION", "PRODUCTION_SENSITIVE", "AUTH_REQUIRED"})


def _local_ops_registry_errors(repo_root: Path, scripts: Mapping[str, object], registry: dict[str, object]) -> list[str]:
    """Validate cockpit local-ops JSON registry against packaged console scripts and repo paths."""
    errors: list[str] = []
    if registry.get("schema_version") != _LOCAL_OPS_REGISTRY_SCHEMA:
        errors.append(f"unexpected schema_version {registry.get('schema_version')!r} (expected {_LOCAL_OPS_REGISTRY_SCHEMA!r})")
    commands = registry.get("commands")
    if not isinstance(commands, list):
        errors.append("commands must be a non-empty list")
        return errors
    for item in commands:
        if not isinstance(item, dict):
            errors.append("each command must be an object")
            continue
        cid = str(item.get("id") or "?")
        pcs = str(item.get("primaryConsoleScript") or "").strip()
        py_paths_raw = item.get("pythonScriptPaths")
        py_paths: tuple[str, ...] = ()
        if isinstance(py_paths_raw, list):
            py_paths = tuple(str(p).strip().replace("\\", "/") for p in py_paths_raw if isinstance(p, str) and str(p).strip())
        elif py_paths_raw is not None:
            errors.append(f"{cid}: pythonScriptPaths must be a list")

        if pcs and pcs not in scripts:
            errors.append(f"{cid}: primaryConsoleScript {pcs!r} not in pyproject [project.scripts]")
        for rel in py_paths:
            candidate = repo_root / rel
            if not candidate.is_file():
                errors.append(f"{cid}: missing pythonScriptPaths file {rel}")

        if not pcs and not py_paths:
            errors.append(f"{cid}: set primaryConsoleScript and/or pythonScriptPaths")

        doc_path = item.get("docPath")
        if isinstance(doc_path, str) and doc_path.strip():
            doc_candidate = repo_root / doc_path.strip().replace("\\", "/")
            if not doc_candidate.is_file():
                errors.append(f"{cid}: missing docPath {doc_path.strip()}")

        command_text = str(item.get("commandText") or "")
        lowered = command_text.lower()
        for banned in (
            "x-strategy-validator-token",
            "bearer ",
            "password=",
            "secret=",
            "api_key=",
            "private_key",
            "-----begin",
        ):
            if banned in lowered:
                errors.append(f"{cid}: commandText contains disallowed pattern {banned!r}")

        safety = item.get("safetyClass")
        if safety not in _LOCAL_OPS_SAFETY:
            errors.append(f"{cid}: invalid safetyClass {safety!r}")
            continue
        warning = item.get("productionWarning")
        warning_ok = isinstance(warning, str) and bool(warning.strip())
        if safety == "PRODUCTION_SENSITIVE" and not warning_ok:
            errors.append(f"{cid}: PRODUCTION_SENSITIVE requires non-empty productionWarning")

    return errors


def _function_defined(path: Path, function_name: str) -> bool:
    try:
        tree = ast.parse(_read_text(path), filename=path.as_posix())
    except SyntaxError:
        return False
    return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name for node in tree.body)


def _literal_tuple_assignment(path: Path, assignment_name: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(_read_text(path), filename=path.as_posix())
    except SyntaxError:
        return ()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == assignment_name for target in node.targets):
            continue
        if isinstance(node.value, (ast.Tuple, ast.List)):
            values: list[str] = []
            for item in node.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    values.append(item.value)
            return tuple(values)
    return ()


def _module_exists(repo_root: Path, module_name: str) -> bool:
    module_path = repo_root.joinpath(*module_name.split('.')).with_suffix('.py')
    package_init = repo_root.joinpath(*module_name.split('.')) / '__init__.py'
    return module_path.exists() or package_init.exists()


def _importlinter_contracts(pyproject: dict[str, object]) -> list[dict[str, object]]:
    tool = pyproject.get('tool', {}) if isinstance(pyproject, dict) else {}
    importlinter = tool.get('importlinter', {}) if isinstance(tool, dict) else {}
    contracts = importlinter.get('contracts', []) if isinstance(importlinter, dict) else []
    return [contract for contract in contracts if isinstance(contract, dict)] if isinstance(contracts, list) else []




def _safe_docs_markdown_root(repo_root: Path) -> Path | None:
    """Return the docs scan root without following symlinked components.

    The repository truth gate treats ``docs/`` as an implicit evidence input.
    ``Path.rglob`` follows a symlinked starting directory on supported Python
    versions, so a linked ``docs`` tree can launder outside markdown into the
    console-command/test-path drift checks.  Missing docs remain valid for tiny
    fixture repositories; present docs must be a real directory inside the
    reviewed repo envelope.
    """
    docs_root = repo_root / "docs"
    symlinks = symlink_components_preserving_path(docs_root)
    if symlinks:
        final_component = docs_root in symlinks
        code = (
            "REPOSITORY_TRUTH_DOCS_ROOT_IS_SYMLINK"
            if final_component
            else "REPOSITORY_TRUTH_DOCS_ROOT_PARENT_IS_SYMLINK"
        )
        detail_prefix = "symlinked docs scan root" if final_component else "symlinked docs scan-root parent directories"
        raise PathIntegrityError(
            code=code,
            path=str(docs_root),
            detail=f"{detail_prefix}: {', '.join(str(item) for item in symlinks)}",
        )
    if not docs_root.exists():
        return None
    if not docs_root.is_dir():
        raise PathIntegrityError(
            code="REPOSITORY_TRUTH_DOCS_ROOT_NOT_DIRECTORY",
            path=str(docs_root),
            detail="docs markdown scan root exists but is not a directory",
        )
    return docs_root


def _iter_markdown_files(repo_root: Path, docs_root: Path | None) -> Iterable[Path]:
    if docs_root is None:
        return ()
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(docs_root):
        current_path = Path(current)
        try:
            rel = current_path.relative_to(repo_root).parts
        except ValueError:
            dirnames[:] = []
            continue
        if len(rel) >= 2 and rel[0] == "docs" and rel[1] == "artifacts":
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if not (current_path / dirname).is_symlink()
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if path.suffix == ".md" and not path.is_symlink():
                paths.append(path)
    return tuple(paths)


def _iter_documented_console_commands(repo_root: Path, docs_root: Path | None) -> Iterable[str]:
    pattern = re.compile(r"\b(strategy-validator-[A-Za-z0-9_-]+)\b")
    for path in _iter_markdown_files(repo_root, docs_root):
        text = _read_text(path)
        for match in pattern.finditer(text):
            next_char = text[match.end():match.end() + 1]
            if next_char in {".", ":", "/"}:
                continue
            yield match.group(1)


def _iter_documented_test_paths(repo_root: Path, docs_root: Path | None) -> Iterable[str]:
    pattern = re.compile(r"\btests/[A-Za-z0-9_./-]+\.py\b")
    for path in _iter_markdown_files(repo_root, docs_root):
        for match in pattern.finditer(_read_text(path)):
            yield match.group(0)

def _iter_test_paths_referenced_by_ci(ci_text: str) -> Iterable[str]:
    # This intentionally avoids requiring a YAML dependency.  It catches the
    # literal pytest/test-path references that have historically drifted in CI.
    for match in re.finditer(r"\btests/[A-Za-z0-9_./-]+", ci_text):
        yield match.group(0).rstrip("'\"),]")


def _safe_sqlite_migration_files(repo_root: Path) -> tuple[Path, ...]:
    """Return SQLite migration SQL files without following symlinked inputs.

    Repository-truth checks derive schema version evidence from migration file
    names and tracking inserts.  That evidence must come from the reviewed repo
    tree, not from a symlinked migration root or linked ``*.sql`` file outside
    the source envelope.  Missing migration roots remain valid for tiny fixture
    repositories; present roots and files must be real filesystem entries.
    """
    sqlite_root = repo_root / "strategy_validator" / "migrations" / "sqlite"
    symlinks = symlink_components_preserving_path(sqlite_root)
    if symlinks:
        final_component = sqlite_root in symlinks
        code = (
            "REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_IS_SYMLINK"
            if final_component
            else "REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_PARENT_IS_SYMLINK"
        )
        detail_prefix = "symlinked SQLite migration root" if final_component else "symlinked SQLite migration-root parent directories"
        raise PathIntegrityError(
            code=code,
            path=str(sqlite_root),
            detail=f"{detail_prefix}: {', '.join(str(item) for item in symlinks)}",
        )
    if not sqlite_root.exists():
        return ()
    if not sqlite_root.is_dir():
        raise PathIntegrityError(
            code="REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_NOT_DIRECTORY",
            path=str(sqlite_root),
            detail="SQLite migration scan root exists but is not a directory",
        )

    migrations: list[Path] = []
    for path in sorted(sqlite_root.glob("*.sql"), key=lambda item: item.as_posix()):
        symlinks = symlink_components_preserving_path(path)
        if symlinks:
            final_component = path in symlinks
            code = (
                "REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_IS_SYMLINK"
                if final_component
                else "REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_PARENT_IS_SYMLINK"
            )
            detail_prefix = "symlinked SQLite migration file" if final_component else "symlinked SQLite migration-file parent directories"
            raise PathIntegrityError(
                code=code,
                path=str(path),
                detail=f"{detail_prefix}: {', '.join(str(item) for item in symlinks)}",
            )
        if not path.is_file():
            raise PathIntegrityError(
                code="REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_NOT_REGULAR",
                path=str(path),
                detail="SQLite migration path exists but is not a regular file",
            )
        migrations.append(path)
    return tuple(migrations)


def _max_sqlite_migration_version(migration_files: Iterable[Path]) -> int:
    versions: list[int] = []
    for path in migration_files:
        match = re.match(r"^(\d{4})_", path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0)


def _schema_versions_recorded_by_migrations(migration_files: Iterable[Path]) -> set[int]:
    versions: set[int] = set()
    for path in migration_files:
        text = _read_text(path)
        for match in re.finditer(r"version_id\)\s*\nVALUES\s*\((\d+),", text):
            versions.add(int(match.group(1)))
        for match in re.finditer(r"VALUES\s*\((\d+),\s*datetime\('now'\)", text):
            versions.add(int(match.group(1)))
    return versions


REQUIRED_IGNORE_PATTERNS = (
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.db-wal",
    "*.db-shm",
    "*.log",
    "*.jsonl",
    "artifacts",
    "node_modules",
)


def _normalise_ignore_line(line: str) -> str:
    return line.strip().rstrip("/")


def _ignore_file_missing_patterns(path: Path, required_patterns: tuple[str, ...] = REQUIRED_IGNORE_PATTERNS) -> list[str]:
    if not path.exists():
        return list(required_patterns)
    lines = {
        _normalise_ignore_line(line)
        for line in _read_text(path).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing: list[str] = []
    for pattern in required_patterns:
        normalized = _normalise_ignore_line(pattern)
        alternatives = {normalized}
        if normalized == "*.pyc":
            alternatives.add("*.py[cod]")
        if normalized == "artifacts":
            alternatives.add("artifacts/**")
            # Root-scoped only (so `docs/artifacts/` can stay tracked for classification MANIFEST.json).
            alternatives.add("/artifacts")
        if not alternatives.intersection(lines):
            missing.append(pattern)
    return missing


def run_repository_truth_check(repo_root: str | Path | None = None) -> RepositoryTruthReport:
    checks: list[TruthCheck] = []
    if repo_root is None:
        root = _REPO_ROOT
    else:
        try:
            checked_root = safe_input_dir(repo_root, label="REPOSITORY_TRUTH_REPO_ROOT", required=True)
        except PathIntegrityError as exc:
            checks.append(TruthCheck(name="repo_root_path_integrity", status="FAIL", detail=f"{exc.code}: {exc.detail} ({exc.path})"))
            return RepositoryTruthReport(schema_version="repository_truth_check/v2", status="FAIL", checks=tuple(checks))
        assert checked_root is not None
        root = checked_root

    docs_markdown_root: Path | None = None
    try:
        docs_markdown_root = _safe_docs_markdown_root(root)
    except PathIntegrityError as exc:
        checks.append(
            TruthCheck(
                name="docs_markdown_path_integrity",
                status="FAIL",
                detail=f"{exc.code}: {exc.detail} ({exc.path})",
            )
        )

    pyproject_path = root / "pyproject.toml"
    checks.append(_check(pyproject_path.exists(), "pyproject_present", "pyproject.toml exists", "pyproject.toml is missing"))
    pyproject = _load_pyproject(root) if pyproject_path.exists() else {}

    project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    if not isinstance(scripts, dict):
        scripts = {}
    checks.append(_check(bool(scripts), "project_scripts_declared", f"{len(scripts)} console scripts declared", "no console scripts declared"))

    optional_dependencies = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    dev_dependencies = optional_dependencies.get("dev", []) if isinstance(optional_dependencies, dict) else []
    checks.append(
        _check(
            isinstance(dev_dependencies, list) and {"pytest", "import-linter"}.issubset(
                {str(item).split(">=", 1)[0].strip() for item in dev_dependencies if isinstance(item, str)}
            ),
            "dev_optional_dependencies_declared",
            "dev optional dependency group includes pytest and import-linter",
            "dev optional dependency group must include pytest and import-linter",
        )
    )
    for script_name, entrypoint in sorted(scripts.items()):
        if not isinstance(entrypoint, str) or ":" not in entrypoint:
            checks.append(TruthCheck(name=f"script_entrypoint:{script_name}", status="FAIL", detail=f"invalid entrypoint {entrypoint!r}"))
            continue
        module_name, function_name = entrypoint.split(":", 1)
        module_path = root.joinpath(*module_name.split(".")).with_suffix(".py")
        checks.append(
            _check(
                module_path.exists(),
                f"script_module:{script_name}",
                f"{entrypoint} module exists",
                f"{entrypoint} module is missing at {module_path.relative_to(root) if module_path.is_absolute() else module_path}",
            )
        )
        if module_path.exists():
            checks.append(
                _check(
                    _function_defined(module_path, function_name),
                    f"script_callable:{script_name}",
                    f"{entrypoint} callable is defined",
                    f"{entrypoint} callable is not defined",
                )
            )

    local_ops_registry_path = root / _LOCAL_OPS_REGISTRY_REL
    if local_ops_registry_path.is_file():
        local_ops_errors: list[str] = []
        try:
            local_ops_payload = json.loads(_read_text(local_ops_registry_path))
        except json.JSONDecodeError as exc:
            local_ops_errors.append(f"invalid JSON in {_LOCAL_OPS_REGISTRY_REL.as_posix()}: {exc}")
        else:
            if not isinstance(local_ops_payload, dict):
                local_ops_errors.append("local ops registry root must be a JSON object")
            else:
                local_ops_errors.extend(_local_ops_registry_errors(root, scripts, local_ops_payload))
        checks.append(
            _check(
                not local_ops_errors,
                "local_ops_command_registry_mapped",
                "cockpit local-ops registry maps to pyproject scripts, scripts/, and docs",
                "local ops registry issues: " + "; ".join(local_ops_errors),
            )
        )
    else:
        checks.append(
            _check(
                False,
                "local_ops_command_registry_present",
                f"{_LOCAL_OPS_REGISTRY_REL.as_posix()} exists",
                f"missing {_LOCAL_OPS_REGISTRY_REL.as_posix()} (cockpit command registry)",
            )
        )

    documented_commands = sorted(set(_iter_documented_console_commands(root, docs_markdown_root)))
    missing_documented_commands = [name for name in documented_commands if name not in scripts]
    checks.append(
        _check(
            not missing_documented_commands,
            "documented_console_commands_are_packaged",
            f"{len(documented_commands)} documented strategy-validator console commands are packaged",
            "documented console commands missing from pyproject scripts: " + ", ".join(missing_documented_commands),
        )
    )

    documented_test_paths = sorted(set(_iter_documented_test_paths(root, docs_markdown_root)))
    missing_documented_tests = [path for path in documented_test_paths if not (root / path).exists()]
    checks.append(
        _check(
            not missing_documented_tests,
            "documented_test_paths_exist",
            f"{len(documented_test_paths)} documented test paths exist",
            "documented test paths are missing: " + ", ".join(missing_documented_tests),
        )
    )

    ci_path = root / ".github/workflows/ci.yml"
    checks.append(_check(ci_path.exists(), "ci_workflow_present", ".github/workflows/ci.yml exists", ".github/workflows/ci.yml is missing"))
    if ci_path.exists():
        ci_text = _read_text(ci_path)
        test_paths = sorted(set(_iter_test_paths_referenced_by_ci(ci_text)))
        missing = [path for path in test_paths if not (root / path).exists()]
        checks.append(
            _check(
                not missing,
                "ci_test_paths_exist",
                f"{len(test_paths)} referenced pytest paths exist",
                "missing CI pytest paths: " + ", ".join(missing),
            )
        )
        # Job-level `if: hashFiles(...)` is invalid on GitHub Actions; use step-level hashFiles or a
        # checkout-time lockfile probe (e.g. strategist_web_lock) so npm steps stay optional.
        frontend_guard_ok = (
            "ui/strategist-web/package-lock.json" not in ci_text
            or "hashFiles('ui/strategist-web/package-lock.json') != ''" in ci_text
            or "strategist_web_lock" in ci_text
        )
        checks.append(
            _check(
                frontend_guard_ok,
                "optional_frontend_is_guarded",
                "optional strategist-web job is guarded by package-lock presence",
                "strategist-web references are not guarded by package-lock presence",
            )
        )
        checks.append(
            _check(
                "python scripts/source_health.py" in ci_text,
                "ci_source_health_gate_present",
                "CI includes scripts/source_health.py",
                "CI does not include scripts/source_health.py",
            )
        )
        checks.append(
            _check(
                "python scripts/purge_repo_transients.py --json" in ci_text,
                "ci_purge_repo_transients_dry_run_gate_present",
                "CI includes scripts/purge_repo_transients.py --json (dry-run plan)",
                "CI does not include scripts/purge_repo_transients.py --json transient purge plan",
            )
        )
        checks.append(
            _check(
                "python scripts/repository_truth_check.py" in ci_text,
                "ci_repository_truth_gate_present",
                "CI includes scripts/repository_truth_check.py",
                "CI does not include scripts/repository_truth_check.py",
            )
        )
        checks.append(
            _check(
                "python scripts/migration_truth_check.py" in ci_text,
                "ci_migration_truth_gate_present",
                "CI includes scripts/migration_truth_check.py",
                "CI does not include scripts/migration_truth_check.py",
            )
        )
        checks.append(
            _check(
                "python scripts/package_repo.py --check" in ci_text,
                "ci_clean_archive_gate_present",
                "CI includes scripts/package_repo.py --check",
                "CI does not validate clean archive selection with scripts/package_repo.py --check",
            )
        )
        checks.append(
            _check(
                "python scripts/package_repo.py --output" in ci_text and "strategy-validator-clean.zip" in ci_text,
                "ci_clean_archive_build_smoke_present",
                "CI builds a clean repo ZIP into RUNNER_TEMP",
                "CI must build a clean repo ZIP into RUNNER_TEMP, not only dry-run archive selection",
            )
        )
        checks.append(
            _check(
                "python scripts/verify_repo_archive.py" in ci_text and "strategy-validator-clean.zip" in ci_text,
                "ci_clean_archive_verify_smoke_present",
                "CI verifies the clean repo ZIP against the checked-out source tree",
                "CI must verify the clean repo ZIP with scripts/verify_repo_archive.py",
            )
        )
        dev_environment_gate_count = ci_text.count("python scripts/environment_check.py --include-extra dev")
        checks.append(
            _check(
                dev_environment_gate_count >= 2,
                "ci_dev_environment_gates_include_dev_extra",
                f"{dev_environment_gate_count} CI dev environment gates include the dev optional dependency group",
                "CI dev jobs must run scripts/environment_check.py --include-extra dev",
            )
        )

    package_repo_path = root / "scripts/package_repo.py"
    package_repo_text = _read_text(package_repo_path) if package_repo_path.exists() else ""
    checks.append(
        _check(
            package_repo_path.exists()
            and "EXCLUDED_TOP_LEVEL" in package_repo_text
            and '"artifacts"' in package_repo_text
            and '"scratch"' in package_repo_text
            and "EXCLUDED_DIR_NAMES" in package_repo_text,
            "clean_archive_tool_filters_generated_dirs",
            "scripts/package_repo.py filters generated/scratch/cache directories from repo handoff ZIPs",
            "scripts/package_repo.py must exist and filter artifacts/scratch/cache directories",
        )
    )
    checks.append(
        _check(
            "EXCLUDED_SUFFIXES" in package_repo_text
            and '".zip"' in package_repo_text
            and "archive_sha256" in package_repo_text
            and "ZipInfo" in package_repo_text
            and "date_time = (1980, 1, 1, 0, 0, 0)" in package_repo_text
            and "sorted(iter_clean_repo_files" in package_repo_text,
            "clean_archive_tool_is_deterministic_and_digesting",
            "scripts/package_repo.py excludes archive outputs, normalizes ZIP metadata, and reports archive_sha256",
            "scripts/package_repo.py must exclude archive outputs, normalize ZIP metadata, and report archive_sha256",
        )
    )
    checks.append(
        _check(
            "_iter_paths_pruned" in package_repo_text
            and "os.walk" in package_repo_text
            and '".db-wal"' in package_repo_text
            and '".jsonl"' in package_repo_text,
            "clean_archive_tool_prunes_runtime_artifacts",
            "scripts/package_repo.py prunes excluded directories and runtime DB/log artifacts",
            "scripts/package_repo.py must prune excluded directories and filter runtime DB/log artifacts",
        )
    )

    checks.append(
        _check(
            "UnsafeArchiveOutputError" in package_repo_text
            and "_would_include_output_path" in package_repo_text
            and "archive output would be included in future clean archives" in package_repo_text,
            "clean_archive_tool_rejects_self_including_output",
            "scripts/package_repo.py rejects output paths that would become future archive members",
            "scripts/package_repo.py must reject non-excluded archive outputs inside the repo root",
        )
    )

    verify_repo_archive_path = root / "scripts/verify_repo_archive.py"
    verify_repo_archive_text = _read_text(verify_repo_archive_path) if verify_repo_archive_path.exists() else ""
    checks.append(
        _check(
            verify_repo_archive_path.exists()
            and "repo_archive_verify/v1" in verify_repo_archive_text
            and "EXPECTED_ZIP_TIMESTAMP" in verify_repo_archive_text
            and "entry_digest" in verify_repo_archive_text
            and "entry_compression" in verify_repo_archive_text,
            "clean_archive_verify_tool_present",
            "scripts/verify_repo_archive.py verifies archive metadata, compression, and source digests",
            "scripts/verify_repo_archive.py must verify clean archive metadata, compression, and source digests",
        )
    )

    migration_truth_path = root / "scripts/migration_truth_check.py"
    migration_truth_text = _read_text(migration_truth_path) if migration_truth_path.exists() else ""
    checks.append(
        _check(
            migration_truth_path.exists()
            and "migration_truth_check/v3" in migration_truth_text
            and "apply_sqlite_migrations" in migration_truth_text
            and "migration_idempotency" in migration_truth_text
            and "REQUIRED_COLUMNS" in migration_truth_text
            and "idempotency_uniqueness_enforced" in migration_truth_text
            and "sequence_uniqueness_enforced" in migration_truth_text,
            "migration_truth_tool_present",
            "scripts/migration_truth_check.py verifies migration idempotency, schema objects, columns, idempotency uniqueness, and sequence uniqueness",
            "scripts/migration_truth_check.py must verify migration idempotency, schema objects, columns, idempotency uniqueness, and sequence uniqueness",
        )
    )

    source_health_path = root / "scripts/source_health.py"
    source_health_text = _read_text(source_health_path) if source_health_path.exists() else ""
    checks.append(
        _check(
            "scripts/verify_repo_archive.py" in source_health_text,
            "source_health_includes_archive_verifier",
            "source-health default scope includes scripts/verify_repo_archive.py",
            "source-health default scope must include scripts/verify_repo_archive.py",
        )
    )
    checks.append(
        _check(
            "scripts/migration_truth_check.py" in source_health_text,
            "source_health_includes_migration_truth",
            "source-health default scope includes scripts/migration_truth_check.py",
            "source-health default scope must include scripts/migration_truth_check.py",
        )
    )
    source_health_roots = _literal_tuple_assignment(source_health_path, "HIGH_GRAVITY_ROOTS") if source_health_path.exists() else ()
    missing_source_health_roots = [value for value in source_health_roots if not (root / value).exists()]
    checks.append(
        _check(
            bool(source_health_roots) and not missing_source_health_roots,
            "source_health_default_roots_exist",
            f"{len(source_health_roots)} source-health default roots exist",
            "source-health default roots missing: " + ", ".join(missing_source_health_roots or ["HIGH_GRAVITY_ROOTS not found"]),
        )
    )

    release_candidate_path = root / "strategy_validator/cli/release_candidate.py"
    release_candidate_text = _read_text(release_candidate_path) if release_candidate_path.exists() else ""
    for gate_name, script_name in (
        ("release_candidate_environment_gate_present", "scripts/environment_check.py"),
        ("release_candidate_source_health_gate_present", "scripts/source_health.py"),
        ("release_candidate_repository_truth_gate_present", "scripts/repository_truth_check.py"),
        ("release_candidate_migration_truth_gate_present", "scripts/migration_truth_check.py"),
    ):
        checks.append(
            _check(
                script_name in release_candidate_text,
                gate_name,
                f"release-candidate assessment includes {script_name}",
                f"release-candidate assessment does not include {script_name}",
            )
        )
    checks.append(
        _check(
            '"--include-extra", "dev"' in release_candidate_text or "--include-extra dev" in release_candidate_text,
            "release_candidate_environment_gate_includes_dev_extra",
            "release-candidate environment gate includes the dev optional dependency group",
            "release-candidate assessment must validate dev dependencies required by pytest/import-linter checks",
        )
    )
    environment_gate_index = release_candidate_text.find('run_check("environment-check"')
    pytest_command_index = release_candidate_text.find('"pytest"')
    checks.append(
        _check(
            environment_gate_index >= 0 and (pytest_command_index < 0 or environment_gate_index < pytest_command_index),
            "release_candidate_environment_gate_precedes_pytest",
            "release-candidate assessment explains dependency drift before pytest-backed checks run",
            "release-candidate assessment must run the environment gate before pytest-backed checks",
        )
    )
    migration_gate_index = release_candidate_text.find('run_check("migration-truth"')
    checks.append(
        _check(
            migration_gate_index >= 0 and environment_gate_index >= 0 and migration_gate_index < environment_gate_index,
            "release_candidate_migration_truth_precedes_environment_gate",
            "release-candidate assessment checks migration idempotency before dependency-heavy gates",
            "release-candidate assessment must run migration truth before dependency-heavy environment gates",
        )
    )
    bundle_verify_index = release_candidate_text.find('cmd_verify_bundle(candidate)')
    source_health_index = release_candidate_text.find('run_check("source-health"')
    checks.append(
        _check(
            bundle_verify_index >= 0 and source_health_index >= 0 and bundle_verify_index < source_health_index,
            "release_candidate_assessment_verifies_bundle_first",
            "release-candidate assessment verifies bundle membership before readiness checks",
            "release-candidate assessment must verify bundle membership before readiness checks",
        )
    )
    checks.append(
        _check(
            '"name": "bundle-verify"' in release_candidate_text and '"schema": 2' in release_candidate_text,
            "release_candidate_assessment_records_bundle_verify",
            "release-candidate assessment records bundle verification as a schema 2 check",
            "release-candidate assessment must record bundle verification in schema 2 assessment output",
        )
    )
    checks.append(
        _check(
            release_candidate_text.count('rm_tree(Path(".pytest_cache"))') == 1
            and 'rm_tree(Path(".import_linter_cache"))' in release_candidate_text,
            "release_candidate_cleanup_cache_roots_unique",
            "release-candidate cleanup removes cache roots without duplicate cleanup entries",
            "release-candidate cleanup should remove each cache root once",
        )
    )
    checks.append(
        _check(
            "_include_in_archive_fallback_manifest" in release_candidate_text
            and "_ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL" in release_candidate_text
            and '"artifacts"' in release_candidate_text
            and '"scratch"' in release_candidate_text,
            "release_candidate_archive_fallback_filters_transients",
            "release-candidate archive fallback manifest filters transient top-level work dirs",
            "release-candidate no-git manifest fallback must filter artifacts/scratch/transient cache directories",
        )
    )
    checks.append(
        _check(
            "_ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES" in release_candidate_text
            and '".zip"' in release_candidate_text
            and '".tar"' in release_candidate_text
            and '".db-wal"' in release_candidate_text
            and '".jsonl"' in release_candidate_text,
            "release_candidate_archive_fallback_filters_archive_outputs",
            "release-candidate archive fallback filters local archive outputs and runtime state files",
            "release-candidate no-git manifest fallback must filter archive outputs and runtime state files",
        )
    )
    checks.append(
        _check(
            '_bundle_entries_content_sha256' in release_candidate_text
            and '"content_sha256"' in release_candidate_text
            and '"schema": 2' in release_candidate_text,
            "release_candidate_bundle_manifest_has_content_digest",
            "release-candidate bundle manifest seals normalized source membership with content_sha256",
            "release-candidate bundle manifest must include schema 2 and content_sha256",
        )
    )
    checks.append(
        _check(
            "missing_from_manifest" in release_candidate_text
            and "current_paths" in release_candidate_text
            and "stale_manifest_paths" in release_candidate_text,
            "release_candidate_bundle_verify_checks_manifest_membership",
            "release-candidate bundle verification compares manifest membership to current source selection",
            "release-candidate bundle verification must fail when manifest omits current source files",
        )
    )
    checks.append(
        _check(
            "manifest_schema = manifest.get" in release_candidate_text
            and "declared_entry_count" in release_candidate_text
            and "manifest_error_count" in release_candidate_text,
            "release_candidate_bundle_verify_checks_manifest_header",
            "release-candidate bundle verification validates schema, entry_count, and manifest header errors",
            "release-candidate bundle verification must validate schema and entry_count header fields",
        )
    )
    checks.append(
        _check(
            "digest_normalization_errors" in release_candidate_text
            and "content_sha256 cannot be recomputed" in release_candidate_text
            and "has invalid size_bytes" in release_candidate_text,
            "release_candidate_bundle_verify_handles_malformed_digest_entries",
            "release-candidate bundle verification reports malformed content-digest entries without crashing",
            "release-candidate bundle verification must catch malformed size/hash/path values during content digest recomputation",
        )
    )
    checks.append(
        _check(
            "json.JSONDecodeError" in release_candidate_text
            and "bundle manifest is not valid JSON" in release_candidate_text
            and "entries must be a list" in release_candidate_text
            and "bundle manifest must be a JSON object" in release_candidate_text
            and "_bundle_verify_failure_payload" in release_candidate_text,
            "release_candidate_bundle_verify_handles_malformed_manifest_container",
            "release-candidate bundle verification reports malformed manifest containers without crashing",
            "release-candidate bundle verification must write bundle-verify.json for invalid JSON, non-object manifests, and non-list entries",
        )
    )
    checks.append(
        _check(
            "is not a regular file" in release_candidate_text
            and "could not be read" in release_candidate_text
            and "abs_path.is_file()" in release_candidate_text,
            "release_candidate_bundle_verify_handles_non_regular_manifest_paths",
            "release-candidate bundle verification reports directories/non-readable files as malformed entries",
            "release-candidate bundle verification must not crash when a manifest entry points at a directory or unreadable path",
        )
    )
    checks.append(
        _check(
            "is a symbolic link" in release_candidate_text
            and "tracked file is a symbolic link and cannot be sealed" in release_candidate_text
            and "path.is_symlink()" in release_candidate_text,
            "release_candidate_excludes_symbolic_links",
            "release-candidate manifest generation and verification reject symbolic links",
            "release-candidate bundle manifests must not seal or verify symbolic links",
        )
    )
    checks.append(
        _check(
            "_is_canonical_manifest_path" in release_candidate_text
            and "PurePosixPath" in release_candidate_text
            and "canonical repo-relative POSIX path" in release_candidate_text
            and "rel.as_posix() == raw_path" in release_candidate_text,
            "release_candidate_bundle_verify_requires_canonical_manifest_paths",
            "release-candidate bundle verification rejects non-canonical manifest path aliases",
            "release-candidate bundle verification must reject manifest paths such as ./file, duplicate slashes, backslashes, and traversal aliases",
        )
    )
    checks.append(
        _check(
            "_safe_candidate_id" in release_candidate_text
            and "_CANDIDATE_ID_PATTERN" in release_candidate_text
            and "path separators are forbidden" in release_candidate_text
            and "resolved candidate path escapes release artifact root" in release_candidate_text,
            "release_candidate_rejects_path_traversal_candidate_ids",
            "release-candidate commands validate candidate ids before resolving artifact paths",
            "release-candidate commands must reject candidate ids with traversal or path separators",
        )
    )

    checks.append(
        _check(
            'sorted(_tracked_files(), key=lambda item: item.as_posix())' in release_candidate_text
            and 'entries must be sorted by canonical path' in release_candidate_text,
            "release_candidate_bundle_manifest_entries_are_sorted",
            "release-candidate manifests generate and verify lexicographically sorted entries",
            "release-candidate bundle manifests must be generated and verified in canonical sorted path order",
        )
    )
    package_repo_text = _read_text(root / "scripts/package_repo.py") if (root / "scripts/package_repo.py").exists() else ""
    checks.append(
        _check(
            package_repo_text.count('target = payload["output_path"] or "dry-run"') == 1,
            "clean_archive_cli_target_assignment_unique",
            "clean archive CLI formats its target exactly once",
            "clean archive CLI should not contain duplicate target assignment drift",
        )
    )
    checks.append(
        _check(
            "path.is_symlink()" in package_repo_text
            and "return path.is_file()" in package_repo_text,
            "clean_archive_excludes_symbolic_links",
            "clean archive selection excludes symbolic links before file inclusion",
            "clean repository handoff archives must not include symbolic links",
        )
    )

    importlinter_contracts = _importlinter_contracts(pyproject)
    checks.append(
        _check(
            bool(importlinter_contracts),
            "importlinter_contracts_declared",
            f"{len(importlinter_contracts)} import-linter contracts declared",
            "no import-linter contracts declared in pyproject.toml",
        )
    )
    missing_importlinter_modules: list[str] = []
    malformed_importlinter_ignores: list[str] = []
    for contract in importlinter_contracts:
        for field_name in ("source_modules", "forbidden_modules"):
            values = contract.get(field_name, [])
            if not isinstance(values, list):
                missing_importlinter_modules.append(f"{contract.get('name', '<unnamed>')}:{field_name} not a list")
                continue
            for module_name in values:
                if isinstance(module_name, str) and module_name.startswith("strategy_validator") and not _module_exists(root, module_name):
                    missing_importlinter_modules.append(module_name)
        ignore_imports = contract.get("ignore_imports", [])
        if ignore_imports and not isinstance(ignore_imports, list):
            malformed_importlinter_ignores.append(f"{contract.get('name', '<unnamed>')}: ignore_imports not a list")
            continue
        for ignored in ignore_imports if isinstance(ignore_imports, list) else []:
            if not isinstance(ignored, str) or " -> " not in ignored:
                malformed_importlinter_ignores.append(str(ignored))
                continue
            source_module, target_module = ignored.split(" -> ", 1)
            for module_name in (source_module.strip(), target_module.strip()):
                if module_name.startswith("strategy_validator") and not _module_exists(root, module_name):
                    missing_importlinter_modules.append(module_name)
    checks.append(
        _check(
            not missing_importlinter_modules,
            "importlinter_modules_exist",
            "import-linter source/forbidden/ignored modules exist",
            "import-linter references missing modules: " + ", ".join(sorted(set(missing_importlinter_modules))),
        )
    )
    checks.append(
        _check(
            not malformed_importlinter_ignores,
            "importlinter_ignore_imports_well_formed",
            "import-linter ignored imports are well formed",
            "malformed import-linter ignored imports: " + ", ".join(malformed_importlinter_ignores),
        )
    )

    migrations_init = root / "strategy_validator/migrations/__init__.py"
    migrations_text = _read_text(migrations_init) if migrations_init.exists() else ""
    match = re.search(r"EXPECTED_SCHEMA_VERSION\s*=\s*(\d+)", migrations_text)
    expected_schema = int(match.group(1)) if match else None
    try:
        sqlite_migration_files = _safe_sqlite_migration_files(root)
    except PathIntegrityError as exc:
        sqlite_migration_files = ()
        checks.append(
            TruthCheck(
                name="sqlite_migration_path_integrity",
                status="FAIL",
                detail=f"{exc.code}: {exc.detail} ({exc.path})",
            )
        )
    max_migration = _max_sqlite_migration_version(sqlite_migration_files)
    checks.append(
        _check(
            expected_schema == max_migration,
            "migration_schema_version_matches_files",
            f"EXPECTED_SCHEMA_VERSION={expected_schema} matches max sqlite migration {max_migration}",
            f"EXPECTED_SCHEMA_VERSION={expected_schema} does not match max sqlite migration {max_migration}",
        )
    )

    recorded_versions = _schema_versions_recorded_by_migrations(sqlite_migration_files)
    expected_recorded = set(range(1, max_migration + 1)) if max_migration else set()
    missing_recorded = sorted(expected_recorded - recorded_versions)
    checks.append(
        _check(
            not missing_recorded,
            "migration_tracking_records_exist",
            f"sqlite migrations record schema versions 1..{max_migration}",
            "sqlite migrations do not record schema versions: " + ", ".join(str(v) for v in missing_recorded),
        )
    )

    gitignore_path = root / ".gitignore"
    gitignore_missing = _ignore_file_missing_patterns(gitignore_path)
    checks.append(
        _check(
            gitignore_path.exists() and not gitignore_missing,
            "gitignore_hygiene_patterns",
            ".gitignore covers required transient/runtime artifact patterns",
            ".gitignore is missing required patterns: " + ", ".join(gitignore_missing),
        )
    )

    dockerignore_path = root / ".dockerignore"
    dockerignore_missing = _ignore_file_missing_patterns(dockerignore_path)
    checks.append(
        _check(
            dockerignore_path.exists() and not dockerignore_missing,
            "dockerignore_hygiene_patterns",
            ".dockerignore covers required transient/runtime artifact patterns",
            ".dockerignore is missing required patterns: " + ", ".join(dockerignore_missing),
        )
    )



    artifacts_manifest = root / "docs/artifacts/MANIFEST.json"
    artifacts_manifest_ok = False
    artifacts_manifest_detail = "docs/artifacts/MANIFEST.json is missing"
    if artifacts_manifest.exists():
        try:
            artifact_payload = json.loads(_read_text(artifacts_manifest))
            roots = artifact_payload.get("roots", []) if isinstance(artifact_payload, dict) else []
            classified_paths = {str(item.get("path")) for item in roots if isinstance(item, dict)}
            artifacts_manifest_ok = (
                artifact_payload.get("schema_version") == "docs_artifacts_classification/v1"
                and "docs/artifacts" in classified_paths
                and artifact_payload.get("default_classification") in {"historical_release_evidence", "fixture"}
            )
            artifacts_manifest_detail = "docs/artifacts classification manifest is present and classifies docs/artifacts"
        except json.JSONDecodeError:
            artifacts_manifest_detail = "docs/artifacts/MANIFEST.json is not valid JSON"
    checks.append(
        _check(
            artifacts_manifest_ok,
            "docs_artifacts_classification_manifest_present",
            artifacts_manifest_detail,
            artifacts_manifest_detail,
        )
    )



    dead_zone_doc = root / "docs/architecture/STRATEGIC_DEAD_ZONE_QUARANTINE.md"
    dead_zone_text = _read_text(dead_zone_doc) if dead_zone_doc.exists() else ""
    checks.append(
        _check(
            dead_zone_doc.exists()
            and "Frontend operator UI" in dead_zone_text
            and "Workflow engine integration" in dead_zone_text
            and "Multi-tenant operation" in dead_zone_text
            and "Oracle/advisory expansion" in dead_zone_text,
            "strategic_dead_zone_quarantine_documented",
            "strategic dead-zone quarantine document names deferred expansion surfaces",
            "strategic dead-zone quarantine document is missing required deferred surfaces",
        )
    )

    openapi_snapshot = root / "docs/architecture/openapi.snapshot.json"
    openapi_script = root / "scripts/openapi_contract_snapshot.py"
    checks.append(
        _check(
            openapi_script.exists() and openapi_snapshot.exists(),
            "openapi_contract_snapshot_present",
            "OpenAPI contract snapshot and generation script are present",
            "OpenAPI contract snapshot or generation script is missing",
        )
    )
    ci_text = _read_text(root / ".github/workflows/ci.yml") if (root / ".github/workflows/ci.yml").exists() else ""
    checks.append(
        _check(
            "scripts/openapi_contract_snapshot.py --check" in ci_text,
            "ci_openapi_contract_snapshot_gate_present",
            "CI validates the OpenAPI contract snapshot after dependency installation",
            "CI does not validate the OpenAPI contract snapshot",
        )
    )

    api_app_path = root / "strategy_validator/api/app.py"
    api_app_text = _read_text(api_app_path) if api_app_path.exists() else ""
    openapi_script_text = _read_text(openapi_script) if openapi_script.exists() else ""
    checks.append(
        _check(
            "def create_app" in api_app_text
            and "app = create_app()" in api_app_text
            and "from strategy_validator.api.app import create_app" in openapi_script_text,
            "api_app_factory_backs_openapi_snapshot",
            "API app exposes create_app() and the OpenAPI snapshot script uses it",
            "API app factory or OpenAPI snapshot wiring is missing",
        )
    )

    operator_actions_path = root / "strategy_validator/ledger/operator_actions.py"
    operator_actions_text = _read_text(operator_actions_path) if operator_actions_path.exists() else ""
    ledger_ops_path = root / "strategy_validator/cli/ledger_ops.py"
    ledger_ops_text = _read_text(ledger_ops_path) if ledger_ops_path.exists() else ""
    production_smoke_text = _read_text(root / "scripts/production_smoke_check.py") if (root / "scripts/production_smoke_check.py").exists() else ""
    checks.append(
        _check(
            "def read_operator_action_events_readonly" in operator_actions_text
            and "def verify_operator_action_event_chain_readonly" in operator_actions_text
            and "verify_hash_chain_readonly" in ledger_ops_text
            and "verify_operator_action_event_chain_readonly" in ledger_ops_text
            and "readonly=True" in production_smoke_text,
            "ledger_ops_operator_diagnostics_are_readonly",
            "ledger/operator diagnostics expose readonly paths and smoke tooling uses them",
            "ledger/operator diagnostics can still bootstrap the storage they inspect",
        )
    )

    provider_config_text = _read_text(root / "strategy_validator/core/config.py")
    checks.append(
        _check(
            "_env_provider_url_checked" in provider_config_text
            and "_env_provider_url_template_checked" in provider_config_text
            and "STRATEGY_VALIDATOR_ALPACA_DATA_BASE_URL" in provider_config_text,
            "provider_env_url_overrides_are_validated",
            "provider URL environment overrides are validated before assignment",
            "provider URL environment overrides can bypass URL policy validators",
        )
    )

    auth_text = _read_text(root / "strategy_validator/api/auth.py") if (root / "strategy_validator/api/auth.py").exists() else ""
    policy_text = _read_text(root / "strategy_validator/application/ui_command_policy.py") if (root / "strategy_validator/application/ui_command_policy.py").exists() else ""
    security_text = _read_text(root / "strategy_validator/api/security.py") if (root / "strategy_validator/api/security.py").exists() else ""
    projection_surface_text = _read_text(root / "strategy_validator/application/operator_action_projection.py") if (root / "strategy_validator/application/operator_action_projection.py").exists() else ""
    ui_detail_text = _read_text(root / "strategy_validator/api/routes/ui_routes_detail_runtime.py") if (root / "strategy_validator/api/routes/ui_routes_detail_runtime.py").exists() else ""
    checks.append(
        _check(
            "STRATEGY_VALIDATOR_API_TOKEN_SCOPES" in auth_text
            and "operator:command:write" in auth_text
            and "required_scope" in policy_text,
            "mutation_auth_context_has_scopes",
            "mutation auth context records scopes and command policy requires operator:command:write",
            "mutation auth scope enforcement is missing or not wired into command policy",
        )
    )
    checks.append(
        _check(
            "x-request-id" in security_text
            and "STRATEGY_VALIDATOR_API_MUTATION_RATE_LIMIT_PER_MINUTE" in security_text
            and "MUTATION_RATE_LIMIT_EXCEEDED" in security_text,
            "api_security_request_id_and_rate_limit_present",
            "API security envelope emits request ids and supports optional mutation rate limiting",
            "API security envelope must emit request ids and expose optional mutation rate limiting",
        )
    )
    checks.append(
        _check(
            "build_operator_action_event_index_payload" in projection_surface_text
            and "build_operator_action_event_projection_index" in projection_surface_text
            and "@router.get('/operator-actions')" in ui_detail_text,
            "operator_action_projection_api_boundary_present",
            "operator action projection is exposed through an application wrapper and UI read route",
            "operator action projection API boundary is missing or imports projections directly from API routes",
        )
    )

    checks.append(_check_ui_public_facade_contract(root))
    checks.append(_check_ui_public_facade_snapshot_contract(root))
    checks.append(_check_frontend_ui_facade_contract_gate(root))


    single_tenant_cli = root / "strategy_validator/cli/single_tenant_preflight.py"
    single_tenant_cli_text = _read_text(single_tenant_cli) if single_tenant_cli.exists() else ""
    deployment_env_sample = root / "deployment.env.sample"
    deployment_env_text = _read_text(deployment_env_sample) if deployment_env_sample.exists() else ""
    single_tenant_doc = root / "docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md"
    single_tenant_doc_text = _read_text(single_tenant_doc) if single_tenant_doc.exists() else ""
    checks.append(
        _check(
            single_tenant_cli.exists()
            and "single_tenant_deployment_preflight/v1" in single_tenant_cli_text
            and "--verify-backup-restore" in single_tenant_cli_text
            and "operator:command:write" in single_tenant_cli_text
            and "operator:projection:read" in single_tenant_cli_text,
            "single_tenant_preflight_cli_present",
            "single-tenant deployment preflight CLI verifies token scopes, ledger, backup, artifact and restore drill readiness",
            "single-tenant deployment preflight CLI is missing or incomplete",
        )
    )
    checks.append(
        _check(
            deployment_env_sample.exists()
            and "STRATEGY_VALIDATOR_MODE=PRODUCTION" in deployment_env_text
            and "STRATEGY_VALIDATOR_API_TOKEN=CHANGEME" in deployment_env_text
            and "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read" in deployment_env_text
            and "STRATEGY_VALIDATOR_LEDGER_DB_PATH" in deployment_env_text
            and "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR" in deployment_env_text
            and "STRATEGY_VALIDATOR_ARTIFACT_ROOT" in deployment_env_text,
            "single_tenant_env_sample_present",
            "single-tenant deployment environment sample names required production backend contract",
            "single-tenant deployment environment sample is missing required variables",
        )
    )
    sample_secret_violations = collect_sample_secret_hygiene_violations(root)
    checks.append(
        _check(
            not sample_secret_violations,
            "sample_secret_hygiene",
            "tracked *.env.sample, docs markdown, and scripts contain no plausible committed secrets (Alpaca-style key material, opaque tokens, PEM blobs)",
            "committed sample/docs/script hygiene: plausible secret material: " + "; ".join(sample_secret_violations),
        )
    )
    checks.append(
        _check(
            single_tenant_doc.exists()
            and "single_tenant_deployment_preflight/v1" in single_tenant_doc_text
            and "backend-only" in single_tenant_doc_text.lower()
            and "ui/strategist-web" in single_tenant_doc_text,
            "single_tenant_deployment_runbook_present",
            "single-tenant deployment readiness runbook documents scope, preflight and frontend non-readiness",
            "single-tenant deployment readiness runbook is missing or overclaims readiness",
        )
    )
    checks.append(
        _check(
            "strategy-validator-single-tenant-preflight --prepare --verify-backup-restore --require-ready" in ci_text
            and "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read" in ci_text,
            "ci_single_tenant_preflight_gate_present",
            "CI container smoke runs the single-tenant deployment preflight with required token scopes",
            "CI container smoke does not run the single-tenant deployment preflight",
        )
    )

    deployment_env_check = root / "strategy_validator/cli/deployment_env_check.py"
    deployment_env_check_text = _read_text(deployment_env_check) if deployment_env_check.exists() else ""
    api_smoke_script = root / "scripts/single_tenant_api_smoke.py"
    api_smoke_text = _read_text(api_smoke_script) if api_smoke_script.exists() else ""
    env_check_test = root / "tests/constitutional/test_single_tenant_deployment_env_check.py"
    api_smoke_test = root / "tests/constitutional/test_single_tenant_api_smoke_script.py"
    checks.append(
        _check(
            deployment_env_check.exists()
            and "single_tenant_deployment_env_check/v1" in deployment_env_check_text
            and "API_TOKEN_PLACEHOLDER" in deployment_env_check_text
            and "DEPLOYMENT_PATH_NOT_ABSOLUTE" in deployment_env_check_text
            and "strategy-validator-deployment-env-check" in _read_text(root / "pyproject.toml"),
            "single_tenant_deployment_env_check_present",
            "single-tenant deployment env checker validates production mode, token quality, scopes and absolute paths",
            "single-tenant deployment env checker is missing or incomplete",
        )
    )
    checks.append(
        _check(
            api_smoke_script.exists()
            and "strategy-validator-single-tenant-api-smoke" in _read_text(root / "pyproject.toml")
            and "single_tenant_api_http_smoke/v1" in _read_text(root / "strategy_validator/cli/single_tenant_api_smoke.py")
            and "/ui/facade" in _read_text(root / "strategy_validator/cli/single_tenant_api_smoke.py")
            and "unauthenticated_ui_command_rejected" in _read_text(root / "strategy_validator/cli/single_tenant_api_smoke.py")
            and "authenticated_ui_command_accepted" in _read_text(root / "strategy_validator/cli/single_tenant_api_smoke.py")
            and "python3 scripts/single_tenant_api_smoke.py" in ci_text,
            "single_tenant_api_http_smoke_present",
            "single-tenant API HTTP smoke verifies health, readiness, UI facade and mutation auth boundary",
            "single-tenant API HTTP smoke script or CI wiring is missing",
        )
    )
    checks.append(
        _check(
            env_check_test.exists() and api_smoke_test.exists(),
            "single_tenant_deployment_checks_tested",
            "single-tenant env checker and API smoke surfaces have constitutional tests",
            "single-tenant env checker/API smoke tests are missing",
        )
    )


    deployment_bundle_cli = root / "strategy_validator/cli/single_tenant_deployment_bundle.py"
    deployment_bundle_text = _read_text(deployment_bundle_cli) if deployment_bundle_cli.exists() else ""
    deployment_bundle_test = root / "tests/constitutional/test_single_tenant_deployment_bundle.py"
    deployment_bundle_ledger = root / "NEXT_SINGLE_TENANT_BUNDLE_LEDGER.md"
    checks.append(
        _check(
            deployment_bundle_cli.exists()
            and "single_tenant_deployment_bundle/v1" in deployment_bundle_text
            and "deployment.env.redacted.json" in deployment_bundle_text
            and "docker-compose.single-tenant.yml" in deployment_bundle_text
            and "systemd/strategy-validator.service" in deployment_bundle_text
            and "frontend_readiness_claimed" in deployment_bundle_text
            and "strategy-validator-single-tenant-bundle" in _read_text(root / "pyproject.toml")
            and "single_tenant_deployment_bundle/v1" in single_tenant_doc_text
            and "single_tenant_deployment_bundle" in ci_text,
            "single_tenant_deployment_bundle_present",
            "single-tenant deployment bundle generator creates secret-safe compose/systemd/smoke artifacts without frontend readiness claims",
            "single-tenant deployment bundle generator is missing or overclaims readiness",
        )
    )
    checks.append(
        _check(
            deployment_bundle_test.exists() and deployment_bundle_ledger.exists(),
            "single_tenant_deployment_bundle_tested",
            "single-tenant deployment bundle has constitutional tests and implementation ledger",
            "single-tenant deployment bundle tests or ledger are missing",
        )
    )

    deployment_acceptance_cli = root / "strategy_validator/cli/single_tenant_deployment_acceptance.py"
    deployment_acceptance_text = _read_text(deployment_acceptance_cli) if deployment_acceptance_cli.exists() else ""
    deployment_acceptance_test = root / "tests/constitutional/test_single_tenant_deployment_acceptance.py"
    deployment_acceptance_ledger = root / "NEXT_SINGLE_TENANT_ACCEPTANCE_LEDGER.md"
    checks.append(
        _check(
            deployment_acceptance_cli.exists()
            and "single_tenant_deployment_acceptance/v1" in deployment_acceptance_text
            and "deployment_env_valid" in deployment_acceptance_text
            and "deployment_bundle_valid" in deployment_acceptance_text
            and "frontend_readiness_claimed" in deployment_acceptance_text
            and "strategy-validator-single-tenant-acceptance" in _read_text(root / "pyproject.toml")
            and "single_tenant_deployment_acceptance/v1" in single_tenant_doc_text
            and "single_tenant_deployment_acceptance" in ci_text,
            "single_tenant_deployment_acceptance_present",
            "single-tenant deployment acceptance gate validates env, bundle, repo assets and backend-only scope",
            "single-tenant deployment acceptance gate is missing or incomplete",
        )
    )
    checks.append(
        _check(
            deployment_acceptance_test.exists() and deployment_acceptance_ledger.exists(),
            "single_tenant_deployment_acceptance_tested",
            "single-tenant deployment acceptance gate has constitutional tests and implementation ledger",
            "single-tenant deployment acceptance tests or ledger are missing",
        )
    )
    checks.append(
        _check(
            all(token in deployment_bundle_text for token in (
                "commands/verify-ledger.sh",
                "commands/backup-ledger.sh",
                "commands/restore-ledger.sh",
                "commands/acceptance.sh",
                "STRATEGY_VALIDATOR_CONFIRM_RESTORE",
            )),
            "single_tenant_bundle_rollback_helpers_present",
            "single-tenant deployment bundle includes guarded verify/backup/restore/acceptance helper scripts",
            "single-tenant deployment bundle is missing rollback/verification helper scripts",
        )
    )

    deployment_evidence_cli = root / "strategy_validator/cli/single_tenant_deployment_evidence.py"
    deployment_evidence_text = _read_text(deployment_evidence_cli) if deployment_evidence_cli.exists() else ""
    deployment_evidence_test = root / "tests/constitutional/test_single_tenant_deployment_evidence.py"
    checks.append(
        _check(
            deployment_evidence_cli.exists()
            and "single_tenant_deployment_evidence/v1" in deployment_evidence_text
            and "ledger_ops_verify/v1" in deployment_evidence_text
            and "ledger_ops_backup/v1" in deployment_evidence_text
            and "frontend_readiness_claimed" in deployment_evidence_text
            and "strategy-validator-single-tenant-evidence" in _read_text(root / "pyproject.toml")
            and "single_tenant_deployment_evidence/v1" in single_tenant_doc_text
            and "single_tenant_deployment_evidence" in ci_text,
            "single_tenant_deployment_evidence_present",
            "single-tenant deployment evidence pack records hashed go/no-go, smoke, ledger verification and backup reports",
            "single-tenant deployment evidence pack is missing or incomplete",
        )
    )
    checks.append(
        _check(
            deployment_evidence_test.exists(),
            "single_tenant_deployment_evidence_tested",
            "single-tenant deployment evidence pack has constitutional tests",
            "single-tenant deployment evidence test is missing",
        )
    )
    checks.append(
        _check(
            "commands/post-deploy-evidence.sh" in deployment_bundle_text
            and "strategy-validator-single-tenant-evidence" in deployment_bundle_text,
            "single_tenant_bundle_post_deploy_evidence_helper_present",
            "single-tenant deployment bundle includes post-deploy evidence collection helper",
            "single-tenant deployment bundle is missing post-deploy evidence helper",
        )
    )

    dockerfile = root / "Dockerfile"
    docker_text = _read_text(dockerfile) if dockerfile.exists() else ""
    checks.append(
        _check(
            any(line.strip().startswith("USER ") and line.strip() not in {"USER root", "USER 0"} for line in docker_text.splitlines()),
            "docker_non_root_user",
            "Dockerfile switches to a non-root user",
            "Dockerfile does not switch to a non-root user",
        )
    )
    checks.append(
        _check(
            "STRATEGY_VALIDATOR_MODE=PRODUCTION" in docker_text,
            "docker_production_mode_default",
            "Dockerfile defaults to production mode",
            "Dockerfile does not default to production mode",
        )
    )

    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    return RepositoryTruthReport(schema_version="repository_truth_check/v27", status=status, checks=tuple(checks))




def _check_ui_public_facade_contract(repo_root: Path) -> TruthCheck:
    route_module = repo_root / "strategy_validator" / "api" / "routes" / "ui.py"
    contract_test = repo_root / "tests" / "api" / "test_ui_public_facade_contract.py"
    application_module = repo_root / "strategy_validator" / "application" / "ui_public_facade.py"
    route_text = _read_text(route_module) if route_module.exists() else ""
    checks = (
        route_module.exists(),
        application_module.exists(),
        contract_test.exists(),
        "@router.get('/facade')" in route_text or '@router.get("/facade")' in route_text,
        "build_ui_public_facade_inventory" in route_text,
    )
    return _check(
        all(checks),
        "ui_public_facade_contract",
        "/ui/facade contract route, application inventory, and API alignment test are present.",
        "/ui/facade contract route, application inventory, or API alignment test is missing.",
    )


def _check_ui_public_facade_snapshot_contract(repo_root: Path) -> TruthCheck:
    snapshot_script = repo_root / "scripts" / "ui_facade_contract_snapshot.py"
    snapshot_file = repo_root / "docs" / "api" / "ui-public-facade.snapshot.json"
    snapshot_test = repo_root / "tests" / "api" / "test_ui_public_facade_snapshot_contract.py"
    frontend_routes_contract = repo_root / "ui" / "strategist-web" / "lib" / "contracts" / "ui-facade-routes.json"
    script_text = _read_text(snapshot_script) if snapshot_script.exists() else ""
    ci_file = repo_root / ".github" / "workflows" / "ci.yml"
    ci_text = _read_text(ci_file) if ci_file.exists() else ""
    checks = (
        snapshot_script.exists(),
        snapshot_file.exists(),
        snapshot_test.exists(),
        frontend_routes_contract.exists(),
        "build_frontend_ui_facade_routes_contract" in script_text,
        "ui_facade_contract_snapshot.py --check" in ci_text,
    )
    return _check(
        all(checks),
        "ui_public_facade_snapshot_contract",
        "UI facade contract snapshot, generator, test, and CI check are present.",
        "UI facade contract snapshot, generator, test, or CI check is missing.",
    )


def _check_frontend_ui_facade_contract_gate(repo_root: Path) -> TruthCheck:
    """Frontend generated facade contract + hook validation tooling is present and wired."""
    gen_json = repo_root / "ui" / "strategist-web" / "lib" / "generated" / "ui-facade-contract.json"
    gen_ts = repo_root / "ui" / "strategist-web" / "lib" / "generated" / "ui-facade-contract.ts"
    check_script = repo_root / "scripts" / "frontend_ui_contract_check.py"
    emit_script = repo_root / "scripts" / "generate_frontend_ui_facade_contract.py"
    docs = repo_root / "docs" / "frontend" / "ui-facade-contract.md"
    pkg = repo_root / "ui" / "strategist-web" / "package.json"
    ci_file = repo_root / ".github" / "workflows" / "ci.yml"
    pkg_text = _read_text(pkg) if pkg.exists() else ""
    ci_text = _read_text(ci_file) if ci_file.exists() else ""
    checks = (
        check_script.exists(),
        emit_script.exists(),
        gen_json.exists(),
        gen_ts.exists(),
        docs.exists(),
        '"contract:check"' in pkg_text,
        "frontend_ui_contract_check.py" in ci_text,
    )
    return _check(
        all(checks),
        "frontend_ui_facade_contract_gate",
        "Frontend UI facade generated contract, hook check script, docs, npm contract:check, and CI gate are present.",
        "Frontend UI facade contract gate artifacts or wiring are missing.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository metadata/config truth against files on disk.")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this script's parent repository")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = run_repository_truth_check(repo_root=args.repo_root)
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"repository_truth_check: {report.status}")
        for check in report.checks:
            print(f"{check.status:4} {check.name}: {check.detail}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
