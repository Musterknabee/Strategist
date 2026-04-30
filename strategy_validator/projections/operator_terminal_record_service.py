from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_pack_terminal_record import (
    OracleOperatorPackTerminalRecord,
    render_operator_pack_terminal_record_markdown_lines,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _relative_or_absolute(path: Path, *, repo_root: Path | None) -> str:
    resolved = path.resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class OperatorTerminalRecordMaterializationResult:
    publication_root: Path
    json_path: Path
    markdown_path: Path
    manifest_path: Path
    index_path: Path


@dataclass(frozen=True)
class OperatorTerminalRecordPublication:
    manifest: dict[str, Any]
    index: dict[str, Any]
    result: OperatorTerminalRecordMaterializationResult


def build_operator_terminal_record_manifest(
    *,
    record: OracleOperatorPackTerminalRecord,
    result: OperatorTerminalRecordMaterializationResult,
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    outputs = [
        {
            'artifact_label': 'terminal_record_json',
            'path': _relative_or_absolute(result.json_path, repo_root=repo_root),
            'sha256': _sha256_file(result.json_path),
            'size_bytes': result.json_path.stat().st_size,
        },
        {
            'artifact_label': 'terminal_record_markdown',
            'path': _relative_or_absolute(result.markdown_path, repo_root=repo_root),
            'sha256': _sha256_file(result.markdown_path),
            'size_bytes': result.markdown_path.stat().st_size,
        },
    ]
    source_manifests = sorted({str(item.latest_manifest_path) for item in record.items})
    manifest = {
        'schema_version': 'oracle_operator_terminal_record_manifest/v1',
        'generated_at_utc': (generated_at_utc or _utc_now()).isoformat(),
        'record_schema_version': record.schema_version,
        'search_root': record.search_root,
        'current_pack_kind': record.current_pack_kind,
        'queue_key': record.queue_key,
        'review_target': record.review_target,
        'priority_band': record.priority_band,
        'board_label': record.board_label,
        'publication_root': _relative_or_absolute(result.publication_root, repo_root=repo_root),
        'record_count': record.total_record_count,
        'record_labels': [item.terminal_record_label for item in record.items],
        'record_keys': [item.terminal_record_key for item in record.items],
        'record_postures': [item.record_posture for item in record.items],
        'source_manifest_paths': [_relative_or_absolute(Path(path), repo_root=repo_root) for path in source_manifests],
        'output_artifact_count': len(outputs),
        'output_artifacts': outputs,
    }
    manifest['publication_digest_sha256'] = hashlib.sha256(
        json.dumps({k: v for k, v in manifest.items() if k != 'generated_at_utc'}, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    ).hexdigest()
    return manifest


def write_operator_terminal_record_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + '\n', encoding='utf-8')


def build_operator_terminal_record_index_entry(*, manifest_path: Path, manifest: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    return {
        'manifest_path': _relative_or_absolute(manifest_path, repo_root=repo_root),
        'generated_at_utc': manifest.get('generated_at_utc'),
        'record_schema_version': manifest.get('record_schema_version'),
        'current_pack_kind': manifest.get('current_pack_kind'),
        'queue_key': manifest.get('queue_key'),
        'review_target': manifest.get('review_target'),
        'priority_band': manifest.get('priority_band'),
        'board_label': manifest.get('board_label'),
        'record_count': manifest.get('record_count', 0),
        'record_labels': list(manifest.get('record_labels', [])),
        'record_postures': list(manifest.get('record_postures', [])),
        'publication_digest_sha256': manifest.get('publication_digest_sha256'),
        'output_artifact_labels': [item.get('artifact_label') for item in manifest.get('output_artifacts', [])],
        'output_artifact_paths': [item.get('path') for item in manifest.get('output_artifacts', [])],
    }


def load_operator_terminal_record_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def build_operator_terminal_record_index(
    *,
    existing_entries: list[dict[str, Any]],
    manifest_path: Path,
    manifest: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    new_entry = build_operator_terminal_record_index_entry(manifest_path=manifest_path, manifest=manifest, repo_root=repo_root)
    remaining = [entry for entry in existing_entries if entry.get('manifest_path') != new_entry['manifest_path']]
    entries = remaining + [new_entry]
    entries.sort(key=lambda item: ((item.get('generated_at_utc') or ''), (item.get('manifest_path') or '')))
    return {
        'schema_version': 'oracle_operator_terminal_record_index/v1',
        'generated_at_utc': (generated_at_utc or _utc_now()).isoformat(),
        'entry_count': len(entries),
        'entries': entries,
    }


def write_operator_terminal_record_index(path: Path, index: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, default=str) + '\n', encoding='utf-8')


def upsert_operator_terminal_record_index(
    *,
    index_path: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    existing_entries: list[dict[str, Any]] = []
    if index_path.exists():
        existing_entries = list(load_operator_terminal_record_index(index_path).get('entries', []))
    index = build_operator_terminal_record_index(
        existing_entries=existing_entries,
        manifest_path=manifest_path,
        manifest=manifest,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    write_operator_terminal_record_index(index_path, index)
    return index


def materialize_operator_terminal_record_publication(
    publication_root: Path,
    record: OracleOperatorPackTerminalRecord,
    *,
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
    index_path: Path | None = None,
) -> OperatorTerminalRecordPublication:
    publication_root.mkdir(parents=True, exist_ok=True)
    json_path = publication_root / 'ORACLE_OPERATOR_PACK_TERMINAL_RECORD.json'
    markdown_path = publication_root / 'ORACLE_OPERATOR_PACK_TERMINAL_RECORD.md'
    json_path.write_text(json.dumps(record.to_payload(), indent=2, default=str) + '\n', encoding='utf-8')
    markdown_path.write_text('\n'.join(render_operator_pack_terminal_record_markdown_lines(record)).lstrip() + '\n', encoding='utf-8')
    manifest_path = publication_root / 'ORACLE_OPERATOR_TERMINAL_RECORD_MANIFEST.json'
    resolved_index_path = index_path or publication_root.parent / 'ORACLE_OPERATOR_TERMINAL_RECORD_INDEX.json'
    result = OperatorTerminalRecordMaterializationResult(
        publication_root=publication_root,
        json_path=json_path,
        markdown_path=markdown_path,
        manifest_path=manifest_path,
        index_path=resolved_index_path,
    )
    manifest = build_operator_terminal_record_manifest(record=record, result=result, repo_root=repo_root, generated_at_utc=generated_at_utc)
    write_operator_terminal_record_manifest(manifest_path, manifest)
    index = upsert_operator_terminal_record_index(
        index_path=resolved_index_path,
        manifest_path=manifest_path,
        manifest=manifest,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    return OperatorTerminalRecordPublication(manifest=manifest, index=index, result=result)


__all__ = [
    'OperatorTerminalRecordMaterializationResult',
    'OperatorTerminalRecordPublication',
    'build_operator_terminal_record_manifest',
    'write_operator_terminal_record_manifest',
    'build_operator_terminal_record_index_entry',
    'load_operator_terminal_record_index',
    'build_operator_terminal_record_index',
    'write_operator_terminal_record_index',
    'upsert_operator_terminal_record_index',
    'materialize_operator_terminal_record_publication',
]
