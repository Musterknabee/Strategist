from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


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


def _resolve_artifact_path(raw_path: str | None, *, repo_root: Path | None, index_path: Path) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    if repo_root is not None:
        return (repo_root / candidate).resolve()
    return (index_path.parent / candidate).resolve()


def _iter_index_paths(search_root: Path, *, index_filename: str = 'ORACLE_PROJECTION_ARTIFACT_INDEX.json') -> Iterable[Path]:
    if not search_root.exists():
        return []
    return sorted(search_root.rglob(index_filename))


def _load_index_entries(index_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(index_path.read_text(encoding='utf-8'))
    return list(payload.get('entries', []))




@dataclass(frozen=True)
class ProjectionArtifactQueryReport:
    schema_version: str
    search_root: str
    projection_labels: tuple[str, ...]
    projection_family: str | None
    output_artifact_label_contains: str | None
    match_count: int
    matches: tuple[ProjectionArtifactDiscoveryMatch, ...]


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
) -> tuple[ProjectionArtifactDiscoveryMatch, ...]:
    label_rank = {label: idx for idx, label in enumerate(projection_labels)}
    matches: list[ProjectionArtifactDiscoveryMatch] = []
    for index_path in _iter_index_paths(search_root):
        for entry in _load_index_entries(index_path):
            label = str(entry.get('projection_label') or '')
            if projection_labels and label not in label_rank:
                continue
            family = entry.get('projection_family')
            if projection_family is not None and family != projection_family:
                continue
            registry_path = _resolve_artifact_path(entry.get('registry_path'), repo_root=repo_root, index_path=index_path) or index_path
            output_paths = list(entry.get('output_artifact_paths', []))
            output_labels = list(entry.get('output_artifact_labels', []))
            for raw_output_path, output_label in zip(output_paths, output_labels):
                resolved_output_path = _resolve_artifact_path(raw_output_path, repo_root=repo_root, index_path=index_path)
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
    matches = discover_projection_artifact_matches(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=projection_labels,
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
    )
    return ProjectionArtifactQueryReport(
        schema_version='oracle_projection_artifact_query_report/v1',
        search_root=str(search_root.resolve()),
        projection_labels=tuple(projection_labels),
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
        match_count=len(matches),
        matches=matches,
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
