from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.projections.operator_materialization import OperatorBundleMaterializationResult


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


def _build_output_descriptor(*, artifact_label: str, path: Path, repo_root: Path | None) -> dict[str, Any]:
    return {
        'artifact_label': artifact_label,
        'path': _relative_or_absolute(path, repo_root=repo_root),
        'sha256': _sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def build_operator_pack_manifest(
    *,
    pack_kind: str,
    report: Any,
    result: OperatorBundleMaterializationResult,
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    outputs = [
        _build_output_descriptor(artifact_label='report_json', path=result.json_path, repo_root=repo_root),
        _build_output_descriptor(artifact_label='report_markdown', path=result.markdown_path, repo_root=repo_root),
    ]
    if result.html_path is not None and result.html_path.exists():
        outputs.append(_build_output_descriptor(artifact_label='report_html', path=result.html_path, repo_root=repo_root))

    artifact_descriptors = [
        {
            'artifact_label': source_path,
            'pack_path': pack_path,
        }
        for source_path, pack_path in sorted(result.artifact_pack_paths.items())
    ]
    if not artifact_descriptors and hasattr(report, 'artifacts'):
        artifact_descriptors = [
            {
                'artifact_label': getattr(item, 'source_path', ''),
                'pack_path': getattr(item, 'pack_path', None),
            }
            for item in getattr(report, 'artifacts', [])
            if getattr(item, 'pack_path', None)
        ]

    manifest = {
        'schema_version': 'oracle_operator_pack_manifest/v1',
        'generated_at_utc': (generated_at_utc or _utc_now()).isoformat(),
        'pack_kind': pack_kind,
        'report_schema_version': getattr(report, 'schema_version', None),
        'report_generated_at_utc': getattr(report, 'generated_at_utc', None),
        'report_provenance_digest_sha256': getattr(report, 'provenance_digest_sha256', ''),
        'repo_root': getattr(report, 'repo_root', None),
        'search_root': getattr(report, 'search_root', None),
        'trust_status': getattr(report, 'trust_status', None),
        'summary_line': getattr(report, 'summary_line', ''),
        'pack_root': _relative_or_absolute(result.pack_root, repo_root=repo_root),
        'output_artifact_count': len(outputs),
        'artifact_copy_count': len(artifact_descriptors),
        'output_artifacts': outputs,
        'artifact_copies': artifact_descriptors,
    }
    manifest['pack_digest_sha256'] = hashlib.sha256(
        json.dumps({k: v for k, v in manifest.items() if k != 'generated_at_utc'}, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    ).hexdigest()
    return manifest


def write_operator_pack_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + '\n', encoding='utf-8')


def build_operator_pack_index_entry(*, manifest_path: Path, manifest: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    return {
        'manifest_path': _relative_or_absolute(manifest_path, repo_root=repo_root),
        'pack_kind': manifest.get('pack_kind'),
        'generated_at_utc': manifest.get('generated_at_utc'),
        'report_schema_version': manifest.get('report_schema_version'),
        'report_generated_at_utc': manifest.get('report_generated_at_utc'),
        'report_provenance_digest_sha256': manifest.get('report_provenance_digest_sha256'),
        'trust_status': manifest.get('trust_status'),
        'summary_line': manifest.get('summary_line'),
        'pack_root': manifest.get('pack_root'),
        'pack_digest_sha256': manifest.get('pack_digest_sha256'),
        'output_artifact_labels': [item.get('artifact_label') for item in manifest.get('output_artifacts', [])],
        'output_artifact_paths': [item.get('path') for item in manifest.get('output_artifacts', [])],
    }


def load_operator_pack_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def build_operator_pack_index(
    *,
    existing_entries: list[dict[str, Any]],
    manifest_path: Path,
    manifest: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    new_entry = build_operator_pack_index_entry(manifest_path=manifest_path, manifest=manifest, repo_root=repo_root)
    remaining = [entry for entry in existing_entries if entry.get('manifest_path') != new_entry['manifest_path']]
    entries = remaining + [new_entry]
    entries.sort(key=lambda item: ((item.get('generated_at_utc') or ''), (item.get('manifest_path') or '')))
    return {
        'schema_version': 'oracle_operator_pack_index/v1',
        'generated_at_utc': (generated_at_utc or _utc_now()).isoformat(),
        'entry_count': len(entries),
        'entries': entries,
    }


def write_operator_pack_index(path: Path, index: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, default=str) + '\n', encoding='utf-8')


def upsert_operator_pack_index(
    *,
    index_path: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    existing_entries: list[dict[str, Any]] = []
    if index_path.exists():
        existing_entries = list(load_operator_pack_index(index_path).get('entries', []))
    index = build_operator_pack_index(
        existing_entries=existing_entries,
        manifest_path=manifest_path,
        manifest=manifest,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    write_operator_pack_index(index_path, index)
    return index


def write_operator_pack_manifest_with_index(
    path: Path,
    manifest: dict[str, Any],
    *,
    repo_root: Path | None = None,
    index_path: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    write_operator_pack_manifest(path, manifest)
    resolved_index_path = index_path or path.parent.parent / 'ORACLE_OPERATOR_PACK_INDEX.json'
    return upsert_operator_pack_index(
        index_path=resolved_index_path,
        manifest_path=path,
        manifest=manifest,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )


def discover_latest_operator_pack(search_root: Path, *, pack_kind: str | None = None) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for index_path in sorted(search_root.rglob('ORACLE_OPERATOR_PACK_INDEX.json')):
        payload = load_operator_pack_index(index_path)
        for entry in payload.get('entries', []):
            if pack_kind and entry.get('pack_kind') != pack_kind:
                continue
            matches.append(entry)
    if not matches:
        return None
    matches.sort(key=lambda item: ((item.get('generated_at_utc') or ''), (item.get('manifest_path') or '')))
    return matches[-1]


__all__ = [
    'build_operator_pack_manifest',
    'write_operator_pack_manifest',
    'build_operator_pack_index_entry',
    'build_operator_pack_index',
    'load_operator_pack_index',
    'write_operator_pack_index',
    'upsert_operator_pack_index',
    'write_operator_pack_manifest_with_index',
    'discover_latest_operator_pack',
]
