from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.projections.operator_pack_registry import load_operator_pack_index


@dataclass(frozen=True)
class OperatorPackDiscoveryMatch:
    index_path: Path
    manifest_path: Path
    pack_kind: str
    generated_at_utc: str | None
    report_schema_version: str | None
    report_generated_at_utc: str | None
    report_provenance_digest_sha256: str | None
    trust_status: str | None
    summary_line: str | None
    pack_root: Path
    output_artifact_labels: tuple[str, ...]
    output_artifact_paths: tuple[Path, ...]


@dataclass(frozen=True)
class OperatorPackQuery:
    search_root: Path
    repo_root: Path | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None


@dataclass(frozen=True)
class OperatorPackQueryReport:
    schema_version: str
    search_root: str
    pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    match_count: int
    matches: tuple[OperatorPackDiscoveryMatch, ...]


@dataclass(frozen=True)
class OperatorPackOperatorQueryResult:
    query: OperatorPackQuery
    report: OperatorPackQueryReport

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.report.schema_version,
            'search_root': self.report.search_root,
            'pack_kinds': list(self.report.pack_kinds),
            'trust_statuses': list(self.report.trust_statuses),
            'summary_line_contains': self.report.summary_line_contains,
            'output_artifact_label_contains': self.report.output_artifact_label_contains,
            'match_count': self.report.match_count,
            'matches': [
                {
                    'index_path': str(item.index_path),
                    'manifest_path': str(item.manifest_path),
                    'pack_kind': item.pack_kind,
                    'generated_at_utc': item.generated_at_utc,
                    'report_schema_version': item.report_schema_version,
                    'report_generated_at_utc': item.report_generated_at_utc,
                    'report_provenance_digest_sha256': item.report_provenance_digest_sha256,
                    'trust_status': item.trust_status,
                    'summary_line': item.summary_line,
                    'pack_root': str(item.pack_root),
                    'output_artifact_labels': list(item.output_artifact_labels),
                    'output_artifact_paths': [str(path) for path in item.output_artifact_paths],
                }
                for item in self.report.matches
            ],
        }


def _resolve_entry_path(raw_path: str | None, *, index_path: Path, repo_root: Path | None) -> Path:
    if not raw_path:
        return index_path.parent
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    if repo_root is not None:
        return (repo_root / candidate).resolve()
    return (index_path.parent / candidate).resolve()


def _build_match(entry: dict[str, Any], *, index_path: Path, repo_root: Path | None) -> OperatorPackDiscoveryMatch:
    return OperatorPackDiscoveryMatch(
        index_path=index_path.resolve(),
        manifest_path=_resolve_entry_path(entry.get('manifest_path'), index_path=index_path, repo_root=repo_root),
        pack_kind=entry.get('pack_kind', ''),
        generated_at_utc=entry.get('generated_at_utc'),
        report_schema_version=entry.get('report_schema_version'),
        report_generated_at_utc=entry.get('report_generated_at_utc'),
        report_provenance_digest_sha256=entry.get('report_provenance_digest_sha256'),
        trust_status=entry.get('trust_status'),
        summary_line=entry.get('summary_line'),
        pack_root=_resolve_entry_path(entry.get('pack_root'), index_path=index_path, repo_root=repo_root),
        output_artifact_labels=tuple(str(item) for item in entry.get('output_artifact_labels', []) if item),
        output_artifact_paths=tuple(
            _resolve_entry_path(str(item), index_path=index_path, repo_root=repo_root)
            for item in entry.get('output_artifact_paths', [])
            if item
        ),
    )


def build_operator_pack_query(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> OperatorPackQuery:
    return OperatorPackQuery(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
    )


def discover_operator_pack_matches(query: OperatorPackQuery) -> tuple[OperatorPackDiscoveryMatch, ...]:
    matches: list[OperatorPackDiscoveryMatch] = []
    for index_path in sorted(query.search_root.rglob('ORACLE_OPERATOR_PACK_INDEX.json')):
        payload = load_operator_pack_index(index_path)
        for entry in payload.get('entries', []):
            if query.pack_kinds and entry.get('pack_kind') not in query.pack_kinds:
                continue
            if query.trust_statuses and entry.get('trust_status') not in query.trust_statuses:
                continue
            summary_line = str(entry.get('summary_line') or '')
            if query.summary_line_contains and query.summary_line_contains.lower() not in summary_line.lower():
                continue
            labels = tuple(str(item) for item in entry.get('output_artifact_labels', []) if item)
            if query.output_artifact_label_contains and not any(
                query.output_artifact_label_contains.lower() in label.lower() for label in labels
            ):
                continue
            matches.append(_build_match(entry, index_path=index_path, repo_root=query.repo_root))
    matches.sort(key=lambda item: ((item.generated_at_utc or ''), str(item.manifest_path)))
    return tuple(matches)


def build_operator_pack_query_report(query: OperatorPackQuery) -> OperatorPackQueryReport:
    matches = discover_operator_pack_matches(query)
    return OperatorPackQueryReport(
        schema_version='oracle_operator_pack_query_report/v1',
        search_root=str(query.search_root),
        pack_kinds=query.pack_kinds,
        trust_statuses=query.trust_statuses,
        summary_line_contains=query.summary_line_contains,
        output_artifact_label_contains=query.output_artifact_label_contains,
        match_count=len(matches),
        matches=matches,
    )


def run_operator_pack_query(query: OperatorPackQuery) -> OperatorPackOperatorQueryResult:
    return OperatorPackOperatorQueryResult(query=query, report=build_operator_pack_query_report(query))


def discover_latest_operator_pack_match(query: OperatorPackQuery) -> OperatorPackDiscoveryMatch | None:
    matches = discover_operator_pack_matches(query)
    if not matches:
        return None
    return matches[-1]


__all__ = [
    'OperatorPackDiscoveryMatch',
    'OperatorPackQuery',
    'OperatorPackQueryReport',
    'OperatorPackOperatorQueryResult',
    'build_operator_pack_query',
    'build_operator_pack_query_report',
    'discover_operator_pack_matches',
    'discover_latest_operator_pack_match',
    'run_operator_pack_query',
]
