from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class UiWorkboardQueueProvenance:
    governed_work_item_count: int
    journaled_work_item_count: int
    queue_key: str | None
    review_target: str | None
    materialization_state: str | None
    freshness_state: str | None
    latest_journaled_action_at_utc: str | None
    latest_projection_generated_at_utc: str | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> 'UiWorkboardQueueProvenance':
        source = dict(value or {})
        return cls(
            governed_work_item_count=int(source.get('governed_work_item_count') or 0),
            journaled_work_item_count=int(source.get('journaled_work_item_count') or 0),
            queue_key=source.get('queue_key'),
            review_target=source.get('review_target'),
            materialization_state=source.get('materialization_state'),
            freshness_state=source.get('freshness_state'),
            latest_journaled_action_at_utc=source.get('latest_journaled_action_at_utc'),
            latest_projection_generated_at_utc=source.get('latest_projection_generated_at_utc'),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            'governed_work_item_count': self.governed_work_item_count,
            'journaled_work_item_count': self.journaled_work_item_count,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'materialization_state': self.materialization_state,
            'freshness_state': self.freshness_state,
            'latest_journaled_action_at_utc': self.latest_journaled_action_at_utc,
            'latest_projection_generated_at_utc': self.latest_projection_generated_at_utc,
        }


@dataclass(frozen=True)
class UiWorkboardOperationalTruth:
    mutation_safety: dict[str, Any]
    materialization: dict[str, Any]
    queue_provenance: UiWorkboardQueueProvenance

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> 'UiWorkboardOperationalTruth':
        source = dict(value or {})
        return cls(
            mutation_safety=dict(source.get('mutation_safety', {}) or {}),
            materialization=dict(source.get('materialization', {}) or {}),
            queue_provenance=UiWorkboardQueueProvenance.from_mapping(source.get('queue_provenance')),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            'mutation_safety': dict(self.mutation_safety),
            'materialization': dict(self.materialization),
            'queue_provenance': self.queue_provenance.to_payload(),
        }


@dataclass(frozen=True)
class UiWorkboardExportPayload:
    schema_version: str
    export_family: str
    board_label: str | None
    generated_at_utc: str | None
    summary_line: str
    export_line: str
    export_state: str
    export_completeness_state: str
    verification_state: str
    bundle_root: str | None
    published_bundle_root: str | None
    focus_work_item_key: str | None
    focus_action: str | None
    top_cluster_signal_kind: str | None
    embedded_payload_count: int
    member_count: int
    queue_work_item_count: int
    pack_item_count: int
    pack_column_count: int
    materialization: dict[str, Any]
    queue_provenance: UiWorkboardQueueProvenance
    mutation_safety: dict[str, Any]
    operational_truth: UiWorkboardOperationalTruth
    schema_versions: list[str] = field(default_factory=list)
    canonical_source_paths: list[str] = field(default_factory=list)
    bundle_fingerprint_sha256: str | None = None
    payload_keys: list[str] = field(default_factory=list)
    publication_payloads: dict[str, Any] = field(default_factory=dict)
    bundle_manifest: dict[str, Any] = field(default_factory=dict)
    verification_envelope: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> 'UiWorkboardExportPayload':
        source = dict(value or {})
        known = {
            'schema_version', 'export_family', 'board_label', 'generated_at_utc', 'summary_line', 'export_line',
            'export_state', 'export_completeness_state', 'verification_state', 'bundle_root', 'published_bundle_root',
            'focus_work_item_key', 'focus_action', 'top_cluster_signal_kind', 'embedded_payload_count', 'member_count',
            'queue_work_item_count', 'pack_item_count', 'pack_column_count', 'materialization', 'queue_provenance',
            'mutation_safety', 'operational_truth', 'schema_versions', 'canonical_source_paths',
            'bundle_fingerprint_sha256', 'payload_keys', 'publication_payloads', 'bundle_manifest',
            'verification_envelope', 'source_surface'
        }
        extras = {k: v for k, v in source.items() if k not in known}
        queue_provenance = UiWorkboardQueueProvenance.from_mapping(source.get('queue_provenance'))
        operational_truth = UiWorkboardOperationalTruth.from_mapping(
            source.get('operational_truth') or {
                'mutation_safety': source.get('mutation_safety', {}),
                'materialization': source.get('materialization', {}),
                'queue_provenance': queue_provenance.to_payload(),
            }
        )
        return cls(
            schema_version=str(source.get('schema_version') or 'oracle_operator_board_export_payload/v1'),
            export_family=str(source.get('export_family') or 'oracle_operator_board_export_payload'),
            board_label=source.get('board_label'),
            generated_at_utc=source.get('generated_at_utc'),
            summary_line=str(source.get('summary_line') or ''),
            export_line=str(source.get('export_line') or ''),
            export_state=str(source.get('export_state') or 'IDLE'),
            export_completeness_state=str(source.get('export_completeness_state') or 'IDLE'),
            verification_state=str(source.get('verification_state') or 'IDLE'),
            bundle_root=source.get('bundle_root'),
            published_bundle_root=source.get('published_bundle_root'),
            focus_work_item_key=source.get('focus_work_item_key'),
            focus_action=source.get('focus_action'),
            top_cluster_signal_kind=source.get('top_cluster_signal_kind'),
            embedded_payload_count=int(source.get('embedded_payload_count') or 0),
            member_count=int(source.get('member_count') or 0),
            queue_work_item_count=int(source.get('queue_work_item_count') or 0),
            pack_item_count=int(source.get('pack_item_count') or 0),
            pack_column_count=int(source.get('pack_column_count') or 0),
            materialization=dict(source.get('materialization', {}) or {}),
            queue_provenance=queue_provenance,
            mutation_safety=dict(source.get('mutation_safety', {}) or {}),
            operational_truth=operational_truth,
            schema_versions=list(source.get('schema_versions', []) or []),
            canonical_source_paths=list(source.get('canonical_source_paths', []) or []),
            bundle_fingerprint_sha256=source.get('bundle_fingerprint_sha256'),
            payload_keys=list(source.get('payload_keys', []) or []),
            publication_payloads=dict(source.get('publication_payloads', {}) or {}),
            bundle_manifest=dict(source.get('bundle_manifest', {}) or {}),
            verification_envelope=dict(source.get('verification_envelope', {}) or {}),
            extras=extras,
        )

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.extras)
        payload.update({
            'schema_version': self.schema_version,
            'export_family': self.export_family,
            'board_label': self.board_label,
            'generated_at_utc': self.generated_at_utc,
            'summary_line': self.summary_line,
            'export_line': self.export_line,
            'export_state': self.export_state,
            'export_completeness_state': self.export_completeness_state,
            'verification_state': self.verification_state,
            'bundle_root': self.bundle_root,
            'published_bundle_root': self.published_bundle_root,
            'focus_work_item_key': self.focus_work_item_key,
            'focus_action': self.focus_action,
            'top_cluster_signal_kind': self.top_cluster_signal_kind,
            'embedded_payload_count': self.embedded_payload_count,
            'member_count': self.member_count,
            'queue_work_item_count': self.queue_work_item_count,
            'pack_item_count': self.pack_item_count,
            'pack_column_count': self.pack_column_count,
            'materialization': dict(self.materialization),
            'queue_provenance': self.queue_provenance.to_payload(),
            'mutation_safety': dict(self.mutation_safety),
            'operational_truth': self.operational_truth.to_payload(),
            'schema_versions': list(self.schema_versions),
            'canonical_source_paths': list(self.canonical_source_paths),
            'bundle_fingerprint_sha256': self.bundle_fingerprint_sha256,
            'payload_keys': list(self.payload_keys),
            'publication_payloads': dict(self.publication_payloads),
            'bundle_manifest': dict(self.bundle_manifest),
            'verification_envelope': dict(self.verification_envelope),
        })
        return payload


@dataclass(frozen=True)
class UiWorkboardExportDocument:
    schema_version: str
    document_family: str
    document_media_type: str
    summary_line: str
    relative_document_path: str
    published_relative_document_path: str | None
    document_sha256: str
    byte_count: int
    line_count: int
    export_state: str | None
    export_completeness_state: str | None
    verification_state: str | None
    generated_at_utc: str | None
    canonical_payload: UiWorkboardExportPayload
    canonical_json: str

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'document_family': self.document_family,
            'document_media_type': self.document_media_type,
            'summary_line': self.summary_line,
            'relative_document_path': self.relative_document_path,
            'published_relative_document_path': self.published_relative_document_path,
            'document_sha256': self.document_sha256,
            'byte_count': self.byte_count,
            'line_count': self.line_count,
            'export_state': self.export_state,
            'export_completeness_state': self.export_completeness_state,
            'verification_state': self.verification_state,
            'generated_at_utc': self.generated_at_utc,
            'canonical_payload': self.canonical_payload.to_payload(),
            'canonical_json': self.canonical_json,
        }


@dataclass(frozen=True)
class UiWorkboardExportIndex:
    schema_version: str
    index_family: str
    summary_line: str
    board_label: str
    generated_at_utc: str | None
    source_surface: str
    export_state: str | None
    export_completeness_state: str | None
    verification_state: str | None
    bundle_root: str | None
    published_bundle_root: str | None
    relative_document_path: str | None
    published_relative_document_path: str | None
    document_media_type: str | None
    document_sha256: str | None
    document_byte_count: int
    document_line_count: int
    bundle_fingerprint_sha256: str | None
    member_count: int
    mutation_safety: dict[str, Any]
    materialization: dict[str, Any]
    queue_provenance: UiWorkboardQueueProvenance
    operational_truth: UiWorkboardOperationalTruth
    embedded_payload_count: int
    payload_keys: list[str]
    schema_versions: list[str]
    canonical_source_paths: list[str]
    verification_summary_line: str | None
    normalized_members: list[dict[str, Any]]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'index_family': self.index_family,
            'summary_line': self.summary_line,
            'board_label': self.board_label,
            'generated_at_utc': self.generated_at_utc,
            'source_surface': self.source_surface,
            'export_state': self.export_state,
            'export_completeness_state': self.export_completeness_state,
            'verification_state': self.verification_state,
            'bundle_root': self.bundle_root,
            'published_bundle_root': self.published_bundle_root,
            'relative_document_path': self.relative_document_path,
            'published_relative_document_path': self.published_relative_document_path,
            'document_media_type': self.document_media_type,
            'document_sha256': self.document_sha256,
            'document_byte_count': self.document_byte_count,
            'document_line_count': self.document_line_count,
            'bundle_fingerprint_sha256': self.bundle_fingerprint_sha256,
            'member_count': self.member_count,
            'mutation_safety': dict(self.mutation_safety),
            'materialization': dict(self.materialization),
            'queue_provenance': self.queue_provenance.to_payload(),
            'operational_truth': self.operational_truth.to_payload(),
            'embedded_payload_count': self.embedded_payload_count,
            'payload_keys': list(self.payload_keys),
            'schema_versions': list(self.schema_versions),
            'canonical_source_paths': list(self.canonical_source_paths),
            'verification_summary_line': self.verification_summary_line,
            'normalized_members': list(self.normalized_members),
        }


__all__ = [
    'UiWorkboardExportDocument',
    'UiWorkboardExportIndex',
    'UiWorkboardExportPayload',
    'UiWorkboardOperationalTruth',
    'UiWorkboardQueueProvenance',
]
