from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, safe_input_dir  # noqa: E402

# Fallback used only when pyproject.toml is unavailable.  The normal gate derives
# required runtime distributions directly from [project].dependencies so the
# environment check cannot silently drift from packaging metadata.
FALLBACK_REQUIRED_DISTRIBUTIONS = (
    ("fastapi", "0.110"),
    ("uvicorn", "0.27"),
    ("pydantic", "2.6"),
    ("PyYAML", "6.0"),
    ("pandas", "2.1"),
    ("numpy", "1.26"),
    ("statsmodels", "0.14"),
    ("cryptography", "42.0"),
)


@dataclass(frozen=True)
class EnvironmentCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class EnvironmentReport:
    schema_version: str
    status: str
    checks: tuple[EnvironmentCheck, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "checks": [asdict(check) for check in self.checks],
        }


def _version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    # Strip common PEP 440 local/epoch decorations enough for floor checks used
    # by this repository.  This intentionally stays dependency-light.
    value = value.split("!", 1)[-1]
    for raw in value.split("."):
        match = re.match(r"\d+", raw)
        if match is None:
            break
        parts.append(int(match.group(0)))
    return tuple(parts)


def _distribution_version(distribution_name: str) -> str | None:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _normalise_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _parse_dependency_requirement(requirement: str) -> tuple[str, str | None] | None:
    # Intentionally small parser for the repo's dependency style, e.g.
    # "pydantic>=2.6" or "fastapi>=0.110".  Environment markers/extras are
    # stripped if they appear later.
    base = requirement.split(";", 1)[0].strip()
    match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(?:>=\s*([A-Za-z0-9!+_.-]+))?", base)
    if not match:
        return None
    return match.group(1), match.group(2)


def _load_pyproject(repo_root: Path) -> dict[str, object] | None:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    with pyproject.open("rb") as handle:
        return tomllib.load(handle)


def _dependency_entries_from_pyproject(repo_root: Path, *, include_extras: Sequence[str] = ()) -> tuple[str, ...]:
    payload = _load_pyproject(repo_root)
    if payload is None:
        return tuple("%s>=%s" % item for item in FALLBACK_REQUIRED_DISTRIBUTIONS)
    project = payload.get("project", {}) if isinstance(payload, dict) else {}
    dependencies = project.get("dependencies", []) if isinstance(project, dict) else []
    entries: list[str] = [dependency for dependency in dependencies if isinstance(dependency, str)] if isinstance(dependencies, list) else []
    optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    if include_extras and isinstance(optional, dict):
        for extra in include_extras:
            extra_dependencies = optional.get(extra, [])
            if isinstance(extra_dependencies, list):
                entries.extend(dependency for dependency in extra_dependencies if isinstance(dependency, str))
    return tuple(entries)


def _required_distributions_from_pyproject(
    repo_root: Path,
    *,
    include_extras: Sequence[str] = (),
) -> tuple[tuple[str, str | None], ...]:
    entries = _dependency_entries_from_pyproject(repo_root, include_extras=include_extras)
    required: list[tuple[str, str | None]] = []
    for dependency in entries:
        parsed = _parse_dependency_requirement(dependency)
        if parsed is not None:
            required.append(parsed)
    return tuple(required) if required else FALLBACK_REQUIRED_DISTRIBUTIONS


def _coerce_required_distribution(item: Sequence[str | None]) -> tuple[str, str | None]:
    # Backward-compatible support for older tests/callers that passed
    # (distribution_name, import_name).  If the second value does not look like a
    # version floor, it is treated as no minimum version.
    if len(item) < 1:
        raise ValueError("required distribution item must include a distribution name")
    name = str(item[0])
    floor = str(item[1]) if len(item) > 1 and item[1] is not None else None
    if floor and not re.match(r"^\d", floor):
        floor = None
    return name, floor


def _normalise_extra_names(values: Sequence[str] | None) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values or ():
        name = str(value).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def run_environment_check(
    required_distributions: Iterable[Sequence[str | None]] | None = None,
    *,
    repo_root: str | Path | None = None,
    include_extras: Sequence[str] = (),
) -> EnvironmentReport:
    checks: list[EnvironmentCheck] = []
    if repo_root is None:
        root = _REPO_ROOT
    else:
        try:
            checked_root = safe_input_dir(repo_root, label="ENVIRONMENT_CHECK_REPO_ROOT", required=True)
        except PathIntegrityError as exc:
            checks.append(
                EnvironmentCheck(
                    name="repo_root_path_integrity",
                    status="FAIL",
                    detail=f"{exc.code}: {exc.detail} ({exc.path})",
                )
            )
            return EnvironmentReport(schema_version="environment_check/v3", status="FAIL", checks=tuple(checks))
        assert checked_root is not None
        root = checked_root
    extras = _normalise_extra_names(include_extras)
    required = (
        tuple(_coerce_required_distribution(item) for item in required_distributions)
        if required_distributions is not None
        else _required_distributions_from_pyproject(root, include_extras=extras)
    )

    python_ok = sys.version_info >= (3, 11)
    checks.append(
        EnvironmentCheck(
            name="python_version",
            status="PASS" if python_ok else "FAIL",
            detail=f"required>=3.11 actual={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )

    if extras:
        payload = _load_pyproject(root)
        project = payload.get("project", {}) if isinstance(payload, dict) else {}
        optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
        for extra in extras:
            exists = isinstance(optional, dict) and extra in optional
            checks.append(
                EnvironmentCheck(
                    name=f"extra:{extra}",
                    status="PASS" if exists else "FAIL",
                    detail="optional dependency extra declared" if exists else "optional dependency extra is not declared in pyproject.toml",
                )
            )

    seen: set[str] = set()
    for distribution_name, minimum_version in required:
        normalized = _normalise_distribution_name(distribution_name)
        if normalized in seen:
            continue
        seen.add(normalized)
        version = _distribution_version(distribution_name)
        if version is None:
            checks.append(
                EnvironmentCheck(
                    name=f"distribution:{distribution_name}",
                    status="FAIL",
                    detail="missing distribution declared by pyproject.toml",
                )
            )
            continue
        checks.append(EnvironmentCheck(name=f"distribution:{distribution_name}", status="PASS", detail=version))
        if minimum_version:
            version_ok = _version_tuple(version) >= _version_tuple(minimum_version)
            checks.append(
                EnvironmentCheck(
                    name=f"min_version:{distribution_name}",
                    status="PASS" if version_ok else "FAIL",
                    detail=f"required>={minimum_version} actual={version}",
                )
            )

    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    return EnvironmentReport(schema_version="environment_check/v3", status=status, checks=tuple(checks))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate local dependency versions against pyproject expectations.")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this script's parent repository")
    parser.add_argument("--include-extra", action="append", default=[], help="Also validate dependencies from [project.optional-dependencies].<extra>")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = run_environment_check(repo_root=args.repo_root, include_extras=args.include_extra)
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"environment_check: {report.status}")
        for check in report.checks:
            print(f"{check.status:4} {check.name}: {check.detail}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
