from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_export_documents import serialize_ui_workboard_export_document
from strategy_validator.contracts.ui_workboard_export import UiWorkboardExportIndex, UiWorkboardExportPayload


def build_ui_workboard_export_index_from_payload(
    *,
    board_label: str,
    export_payload: Mapping[str, Any],
) -> dict[str, Any]:
    canonical_export_payload = UiWorkboardExportPayload.from_mapping(export_payload)
    export_document = serialize_ui_workboard_export_document(canonical_export_payload.to_payload())
    publication_payloads = dict(canonical_export_payload.publication_payloads)
    verification_envelope = dict(canonical_export_payload.verification_envelope)
    content_inventory = {
        str(item.get('export_key') or ''): item
        for item in list(verification_envelope.get('content_inventory', []) or [])
        if str(item.get('export_key') or '')
    }
    normalized_members: list[dict[str, Any]] = []
    for export_key in list(canonical_export_payload.payload_keys):
        publication_member = dict(publication_payloads.get(export_key, {}) or {})
        content_item = dict(content_inventory.get(export_key, {}) or {})
        normalized_members.append({
            'export_key': export_key,
            'schema_version': publication_member.get('schema_version'),
            'title': publication_member.get('title'),
            'payload_state': publication_member.get('payload_state'),
            'payload_sha256': content_item.get('payload_sha256'),
            'relative_publication_path': publication_member.get('relative_publication_path'),
            'generated_relative_path': publication_member.get('generated_relative_path'),
            'published_relative_path': publication_member.get('published_relative_path'),
            'artifact_class': publication_member.get('artifact_class'),
            'publication_stage': publication_member.get('publication_stage'),
            'source_backing_state': publication_member.get('source_backing_state'),
            'source_path_count': len(list(publication_member.get('source_paths', []) or [])),
        })

    summary_line = (
        f"Board export index: {len(normalized_members)} member(s) and document {export_document.get('relative_document_path')} "
        f"are cataloged for direct external consumption."
    )
    index_model = UiWorkboardExportIndex(
        schema_version='oracle_operator_board_export_index/v1',
        index_family='oracle_operator_board_export_index',
        summary_line=summary_line,
        board_label=board_label,
        generated_at_utc=canonical_export_payload.generated_at_utc,
        source_surface='ui/workboard/export/index',
        export_state=canonical_export_payload.export_state,
        export_completeness_state=canonical_export_payload.export_completeness_state,
        verification_state=canonical_export_payload.verification_state,
        bundle_root=canonical_export_payload.bundle_root,
        published_bundle_root=canonical_export_payload.published_bundle_root,
        relative_document_path=export_document.get('relative_document_path'),
        published_relative_document_path=export_document.get('published_relative_document_path'),
        document_media_type=export_document.get('document_media_type'),
        document_sha256=export_document.get('document_sha256'),
        document_byte_count=int(export_document.get('byte_count') or 0),
        document_line_count=int(export_document.get('line_count') or 0),
        bundle_fingerprint_sha256=canonical_export_payload.bundle_fingerprint_sha256,
        member_count=canonical_export_payload.member_count,
        mutation_safety=dict(canonical_export_payload.mutation_safety),
        materialization=dict(canonical_export_payload.materialization),
        queue_provenance=canonical_export_payload.queue_provenance,
        operational_truth=canonical_export_payload.operational_truth,
        embedded_payload_count=canonical_export_payload.embedded_payload_count,
        payload_keys=list(canonical_export_payload.payload_keys),
        schema_versions=list(canonical_export_payload.schema_versions),
        canonical_source_paths=list(canonical_export_payload.canonical_source_paths),
        verification_summary_line=verification_envelope.get('summary_line'),
        normalized_members=normalized_members,
    )
    return index_model.to_payload()


__all__ = ['build_ui_workboard_export_index_from_payload']
