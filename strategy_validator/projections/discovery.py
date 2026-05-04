from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from strategy_validator.core.path_guards import PathBoundaryError, resolve_within_root


@dataclass(frozen=True)
class ProjectionArtifactDiscoveryWarning:
    code: str
    message: str
    index_path: Path | None = None
    raw_path: str | None = None


@dataclass(frozen=True)
class ProjectionArtifactDiscoveryMatch:
    index_path: Path
    registry_path: Path
    projection_label: str
    projection_family: str | None
    projection_version: str | None
    generated_at_utc: str | None
    output_artifact_path: Path
    output_artifact_label: str | None


def _warn(
    warnings: list[ProjectionArtifactDiscoveryWarning] | None,
    *,
    code: str,
    message: str,
    index_path: Path | None = None,
    raw_path: str | None = None,
) -> None:
    if warnings is not None:
        warnings.append(
            ProjectionArtifactDiscoveryWarning(
                code=code,
                message=message,
                index_path=index_path.resolve() if index_path is not None else None,
                raw_path=raw_path,
            )
        )


def _resolve_artifact_path(
    raw_path: str | None,
    *,
    repo_root: Path | None,
    index_path: Path,
    field_name: str,
    warnings: list[ProjectionArtifactDiscoveryWarning] | None = None,
) -> Path | None:
    if not raw_path:
        return None
    root = repo_root.resolve() if repo_root is not None else index_path.parent.resolve()
    try:
        return resolve_within_root(raw_path, root=root, label=field_name)
    except PathBoundaryError as exc:
        _warn(
            warnings,
            code="PROJECTION_ARTIFACT_PATH_OUTSIDE_ROOT",
            message=str(exc),
            index_path=index_path,
            raw_path=raw_path,
        )
        return None


def _iter_index_paths(
    search_root: Path,
    *,
    index_filename: str = "ORACLE_PROJECTION_ARTIFACT_INDEX.json",
    warnings: list[ProjectionArtifactDiscoveryWarning] | None = None,
) -> Iterable[Path]:
    safe_root = search_root.resolve()
    if not safe_root.exists():
        _warn(
            warnings,
            code="PROJECTION_SEARCH_ROOT_MISSING",
            message=f"projection search root does not exist: {safe_root}",
        )
        return []
    return sorted(safe_root.rglob(index_filename))


def _load_index_entries(
    index_path: Path,
    *,
    warnings: list[ProjectionArtifactDiscoveryWarning] | None = None,
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except OSError as exc:
        _warn(
            warnings,
            code="PROJECTION_INDEX_UNREADABLE",
            message=f"could not read projection index: {exc}",
            index_path=index_path,
        )
        return []
    except json.JSONDecodeError as exc:
        _warn(
            warnings,
            code="PROJECTION_INDEX_MALFORMED_JSON",
            message=f"could not parse projection index JSON: {exc}",
            index_path=index_path,
        )
        return []

    if not isinstance(payload, dict):
        _warn(
            warnings,
            code="PROJECTION_INDEX_INVALID_SHAPE",
            message="projection index payload must be an object",
            index_path=index_path,
        )
        return []
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        _warn(
            warnings,
            code="PROJECTION_INDEX_INVALID_ENTRIES",
            message="projection index entries must be a list",
            index_path=index_path,
        )
        return []

    valid_entries: list[dict[str, Any]] = []
    for idx, entry in enumerate(entries):
        if isinstance(entry, dict):
            valid_entries.append(entry)
        else:
            _warn(
                warnings,
                code="PROJECTION_INDEX_ENTRY_INVALID_SHAPE",
                message=f"projection index entry {idx} is not an object",
                index_path=index_path,
            )
    return valid_entries


@dataclass(frozen=True)
class ProjectionArtifactQueryReport:
    schema_version: str
    search_root: str
    projection_labels: tuple[str, ...]
    projection_family: str | None
    output_artifact_label_contains: str | None
    match_count: int
    matches: tuple[ProjectionArtifactDiscoveryMatch, ...]
    warning_count: int = 0
    warnings: tuple[ProjectionArtifactDiscoveryWarning, ...] = ()


def discover_projection_artifact_matches(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_suffixes: Sequence[str] = ('.json',),
    exclude_suffixes: Sequence[str] = ('.projection.registry.json',),
    exclude_filenames: Sequence[str] = ('ORACLE_PROJECTION_ARTIFACT_INDEX.json',),
    output_artifact_label_contains: str | None = None,
    warnings: list[ProjectionArtifactDiscoveryWarning] | None = None,
) -> tuple[ProjectionArtifactDiscoveryMatch, ...]:
    label_rank = {label: idx for idx, label in enumerate(projection_labels)}
    safe_search_root = search_root.resolve()
    safe_repo_root = repo_root.resolve() if repo_root is not None else safe_search_root
    matches: list[ProjectionArtifactDiscoveryMatch] = []
    for index_path in _iter_index_paths(safe_search_root, warnings=warnings):
        try:
            index_path.resolve().relative_to(safe_search_root)
        except ValueError:
            _warn(
                warnings,
                code="PROJECTION_INDEX_OUTSIDE_SEARCH_ROOT",
                message=f"projection index is outside search root: {index_path}",
                index_path=index_path,
            )
            continue
        for entry in _load_index_entries(index_path, warnings=warnings):
            label = str(entry.get('projection_label') or '')
            if projection_labels and label not in label_rank:
                continue
            family = entry.get('projection_family')
            if projection_family is not None and family != projection_family:
                continue
            registry_path = (
                _resolve_artifact_path(
                    entry.get('registry_path'),
                    repo_root=safe_repo_root,
                    index_path=index_path,
                    field_name="projection_registry_path",
                    warnings=warnings,
                )
                or index_path
            )
            output_paths = list(entry.get('output_artifact_paths', []))
            output_labels = list(entry.get('output_artifact_labels', []))
            if len(output_paths) != len(output_labels):
                _warn(
                    warnings,
                    code="PROJECTION_INDEX_OUTPUT_LABEL_MISMATCH",
                    message="output_artifact_paths and output_artifact_labels should have matching lengths",
                    index_path=index_path,
                )
            for raw_output_path, output_label in zip(output_paths, output_labels):
                resolved_output_path = _resolve_artifact_path(
                    raw_output_path,
                    repo_root=safe_repo_root,
                    index_path=index_path,
                    field_name="projection_output_artifact_path",
                    warnings=warnings,
                )
                if resolved_output_path is None:
                    continue
                output_name = resolved_output_path.name
                if any(output_name.endswith(suffix) for suffix in exclude_suffixes):
                    continue
                if output_name in exclude_filenames:
                    continue
                if output_suffixes and not any(output_name.endswith(suffix) for suffix in output_suffixes):
                    continue
                output_label_text = str(output_label) if output_label is not None else None
                if output_artifact_label_contains and output_artifact_label_contains not in (output_label_text or ''):
                    continue
                matches.append(
                    ProjectionArtifactDiscoveryMatch(
                        index_path=index_path.resolve(),
                        registry_path=registry_path.resolve(),
                        projection_label=label,
                        projection_family=str(family) if family is not None else None,
                        projection_version=str(entry.get('projection_version')) if entry.get('projection_version') is not None else None,
                        generated_at_utc=str(entry.get('generated_at_utc')) if entry.get('generated_at_utc') is not None else None,
                        output_artifact_path=resolved_output_path,
                        output_artifact_label=output_label_text,
                    )
                )
    matches.sort(
        key=lambda item: (
            label_rank.get(item.projection_label, len(label_rank)),
            -(0 if item.generated_at_utc is None else 1),
            item.generated_at_utc or '',
            str(item.output_artifact_path),
        )
    )
    return tuple(matches)


def build_projection_artifact_query_report(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> ProjectionArtifactQueryReport:
    warnings: list[ProjectionArtifactDiscoveryWarning] = []
    matches = discover_projection_artifact_matches(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=projection_labels,
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
        warnings=warnings,
    )
    return ProjectionArtifactQueryReport(
        schema_version='oracle_projection_artifact_query_report/v1',
        search_root=str(search_root.resolve()),
        projection_labels=tuple(projection_labels),
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
        match_count=len(matches),
        matches=matches,
        warning_count=len(warnings),
        warnings=tuple(warnings),
    )


def find_projection_artifact_match(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_suffixes: Sequence[str] = ('.json',),
    exclude_suffixes: Sequence[str] = ('.projection.registry.json',),
    exclude_filenames: Sequence[str] = ('ORACLE_PROJECTION_ARTIFACT_INDEX.json',),
) -> ProjectionArtifactDiscoveryMatch | None:
    label_rank = {label: idx for idx, label in enumerate(projection_labels)}
    matches = list(
        discover_projection_artifact_matches(
            search_root=search_root,
            repo_root=repo_root,
            projection_labels=projection_labels,
            projection_family=projection_family,
            output_suffixes=output_suffixes,
            exclude_suffixes=exclude_suffixes,
            exclude_filenames=exclude_filenames,
        )
    )
    if not matches:
        return None
    matches.sort(
        key=lambda item: (
            label_rank.get(item.projection_label, len(label_rank)),
            item.generated_at_utc or '',
            str(item.output_artifact_path),
        ),
        reverse=False,
    )
    grouped = sorted(
        matches,
        key=lambda item: (
            label_rank.get(item.projection_label, len(label_rank)),
            item.generated_at_utc or '',
            str(item.output_artifact_path),
        ),
    )
    # prefer the newest artifact within the highest-priority projection label
    best_label_rank = label_rank.get(grouped[0].projection_label, len(label_rank)) if projection_labels else 0
    same_label = [item for item in matches if label_rank.get(item.projection_label, len(label_rank)) == best_label_rank] if projection_labels else matches
    same_label.sort(key=lambda item: (item.generated_at_utc or '', str(item.output_artifact_path)), reverse=True)
    return same_label[0]


def discover_latest_projection_output(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_suffixes: Sequence[str] = ('.json',),
    exclude_suffixes: Sequence[str] = ('.projection.registry.json',),
    exclude_filenames: Sequence[str] = ('ORACLE_PROJECTION_ARTIFACT_INDEX.json',),
) -> Path | None:
    match = find_projection_artifact_match(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=projection_labels,
        projection_family=projection_family,
        output_suffixes=output_suffixes,
        exclude_suffixes=exclude_suffixes,
        exclude_filenames=exclude_filenames,
    )
    return match.output_artifact_path if match is not None else None
