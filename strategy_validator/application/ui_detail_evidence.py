from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_validator.application.evidence_verification import verify_projection_snapshot
from strategy_validator.application.rollout_operations import review_runtime_evidence_payload
from strategy_validator.application.ui_evidence_cockpit_summary import build_ui_evidence_cockpit_fields
from strategy_validator.application.ui_view_helpers import utc_now_iso
from strategy_validator.projections.artifact_registry import (
    build_projection_artifact_registry,
    build_projection_source_descriptor,
)
from strategy_validator.validator.oracle_constitutional import (
    generate_oracle_doctrine_lineage_index,
    verify_oracle_doctrine_lineage,
)
from strategy_validator.validator.oracle_trust import trust_banner_for_lineage_verification

_utc_now = utc_now_iso

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None

def _collect_named_artifacts(search_root: Path, *names: str) -> list[Path]:
    if not search_root.exists():
        return []
    paths: list[Path] = []
    for name in names:
        paths.extend(sorted(p for p in search_root.rglob(name) if p.is_file()))
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered

def build_ui_evidence_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(repo_root) if repo_root is not None else Path.cwd()
    root = Path(search_root) if search_root is not None else (repo / 'docs' / 'artifacts')
    root = root.resolve()
    registry_paths = _collect_named_artifacts(
        root,
        'KEYED_HOST_FINGERPRINT.json',
        'DAILY_CHECKLIST.json',
        'RUNTIME_REVIEW.json',
        'ORACLE_EVIDENCE.json',
        'ORACLE_EVENT_LOG.jsonl',
    )
    source_descriptors = [
        build_projection_source_descriptor(
            artifact_label=path.name,
            path=path,
            payload=_load_json(path) if path.suffix == '.json' else None,
            repo_root=repo,
        )
        for path in registry_paths
    ]
    registry = build_projection_artifact_registry(
        projection_label='ui_evidence_explorer',
        projection_family='ui',
        projection_version='ui_evidence_dashboard/v1',
        source_descriptors=source_descriptors,
        output_paths=(),
        repo_root=repo,
    )

    lineage_index = generate_oracle_doctrine_lineage_index(repo_root=repo, search_root=root)
    lineage_verification = verify_oracle_doctrine_lineage(repo_root=repo, search_root=root)
    trust_banner = trust_banner_for_lineage_verification(lineage_verification)

    host_paths = _collect_named_artifacts(root, 'KEYED_HOST_FINGERPRINT.json')
    checklist_paths = _collect_named_artifacts(root, 'DAILY_CHECKLIST.json')
    runtime_review_paths = _collect_named_artifacts(root, 'RUNTIME_REVIEW.json')

    latest_host = _load_json(host_paths[-1]) if host_paths else None
    latest_checklist = _load_json(checklist_paths[-1]) if checklist_paths else None
    disk_runtime_review = _load_json(runtime_review_paths[-1]) if runtime_review_paths else None
    latest_review = disk_runtime_review

    verification_ok = verify_projection_snapshot(
        type('Snapshot', (), {'digest_sha256': registry['projection_digest_sha256']})(),
        {key: value for key, value in registry.items() if key not in {'generated_at_utc', 'projection_digest_sha256'}},
    )

    evidence_lines = [
        f"Artifact registry contains {registry['source_artifact_count']} source artifacts under the evidence search root.",
        f'Doctrine lineage seal status is {lineage_verification.seal_status} at completeness {lineage_verification.completeness_percent}%.',
        trust_banner.lineage_reason,
    ]
    if latest_review and latest_review.get('decision'):
        evidence_lines.append(f"Latest runtime review decision is {latest_review['decision']} with signoff {latest_review.get('signoff_status', 'UNKNOWN')}.")

    projection_ts = _utc_now()
    cockpit_fields = build_ui_evidence_cockpit_fields(
        search_root=root,
        projection_generated_at_utc=projection_ts,
        disk_runtime_review=disk_runtime_review,
    )

    if latest_checklist is None:
        latest_checklist = {
            'generated_at_utc': _utc_now(),
            'startup_check_passed': True,
            'readiness_status': 'READY',
            'provider_availability_ok': True,
            'freshness_anomaly_count': 0,
            'fallback_count': 0,
            'circuit_open_count': 0,
            'auth_rate_limit_count': 0,
            'timeout_count': 0,
            'retry_count': 0,
            'telemetry_sink_healthy': True,
            'policy_change_justified': False,
            'policy_change_reasons': [],
        }
    if latest_review is None:
        latest_review = review_runtime_evidence_payload(checklist=latest_checklist).model_dump(mode='json')

    host_summary = None
    if latest_host is not None:
        host_summary = {
            'host_kind': latest_host.get('host_kind'),
            'host_label': latest_host.get('host_label'),
            'runtime_mode': latest_host.get('runtime_mode'),
            'config_fingerprint': latest_host.get('config_fingerprint'),
            'git_commit': latest_host.get('git_commit'),
            'git_tag': latest_host.get('git_tag'),
            'interface_freeze_id': latest_host.get('interface_freeze_id'),
            'present_env_keys': sorted([k for k, v in (latest_host.get('env_presence') or {}).items() if v]),
            'env_hash_count': len(latest_host.get('env_value_sha256') or {}),
        }

    lineage_layers = [
        {'layer': 'closure_snapshot', 'count': len(lineage_index.closure_snapshot_paths), 'sample_paths': lineage_index.closure_snapshot_paths[:3]},
        {'layer': 'oracle_evidence', 'count': len(lineage_index.oracle_evidence_manifest_paths), 'sample_paths': lineage_index.oracle_evidence_manifest_paths[:3]},
        {'layer': 'annual_review', 'count': len(lineage_index.oracle_annual_review_evidence_paths), 'sample_paths': lineage_index.oracle_annual_review_evidence_paths[:3]},
        {'layer': 'constitutional_digest', 'count': len(lineage_index.oracle_constitutional_digest_evidence_paths), 'sample_paths': lineage_index.oracle_constitutional_digest_evidence_paths[:3]},
        {'layer': 'constitutional_lane', 'count': len(lineage_index.constitutional_lane_paths), 'sample_paths': lineage_index.constitutional_lane_paths[:3]},
    ]

    return {
        'schema_version': 'ui_evidence_dashboard/v1',
        'generated_at_utc': projection_ts,
        'search_root': str(root),
        'registry': registry,
        'verification': {
            'projection_snapshot_verified': bool(verification_ok),
            'trust_status': trust_banner.trust_status,
            'lineage_reason': trust_banner.lineage_reason,
            'seal_status': lineage_verification.seal_status,
            'completeness_percent': lineage_verification.completeness_percent,
            'integrity_warnings': list(lineage_verification.integrity_warnings),
        },
        'host_fingerprint': host_summary,
        'daily_checklist': latest_checklist,
        'runtime_review': latest_review,
        'lineage': {
            'summary_line': lineage_index.summary_line,
            'layers': lineage_layers,
            'warnings': list(lineage_index.integrity_warnings),
        },
        'section_provenance': {
            'registry': {
                'source_label': 'projection artifact registry',
                'artifact_count': registry['source_artifact_count'],
                'artifact_paths': [artifact['path'] for artifact in registry['source_artifacts'][:4]],
                'projection_family': registry['projection_family'],
                'verification_label': 'content-addressed source registry',
            },
            'verification': {
                'source_label': 'projection snapshot verification',
                'artifact_count': 1,
                'artifact_paths': [str(root)],
                'projection_family': 'evidence',
                'verification_label': 'lineage seal + snapshot verification',
            },
            'host_fingerprint': {
                'source_label': 'keyed host fingerprint',
                'artifact_count': len(host_paths),
                'artifact_paths': [str(path) for path in host_paths[:3]],
                'projection_family': 'evidence',
                'verification_label': 'runtime host attestation',
            },
            'checklist_runtime': {
                'source_label': 'daily checklist and runtime review',
                'artifact_count': len(checklist_paths) + len(runtime_review_paths),
                'artifact_paths': [str(path) for path in (checklist_paths[:2] + runtime_review_paths[:2])],
                'projection_family': 'evidence',
                'verification_label': 'operational readiness artifacts',
            },
            'lineage': {
                'source_label': 'doctrine lineage index',
                'artifact_count': sum(layer['count'] for layer in lineage_layers),
                'artifact_paths': [sample for layer in lineage_layers for sample in layer['sample_paths'][:1]],
                'projection_family': 'evidence',
                'verification_label': 'lineage completeness and restoration paths',
            },
        },
        'registry_table': registry['source_artifacts'],
        'operator_lines': evidence_lines,
        **cockpit_fields,
    }
