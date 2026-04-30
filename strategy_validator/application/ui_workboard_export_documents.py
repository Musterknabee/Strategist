from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from strategy_validator.contracts.ui_workboard_export import UiWorkboardExportDocument, UiWorkboardExportPayload


def canonicalize_ui_workboard_export_payload(export_payload: Mapping[str, Any]) -> dict[str, Any]:
    return UiWorkboardExportPayload.from_mapping(export_payload).to_payload()


def serialize_ui_workboard_export_document(export_payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical_payload_model = UiWorkboardExportPayload.from_mapping(export_payload)
    canonical_payload = canonical_payload_model.to_payload()
    bundle_root = str(canonical_payload.get('bundle_root') or 'generated/publications/operator/governance-main')
    published_bundle_root = canonical_payload.get('published_bundle_root')
    relative_document_path = f"{bundle_root.rstrip('/')}/board_export_payload.json"
    published_relative_document_path = (
        f"{str(published_bundle_root).rstrip('/')}/board_export_payload.json" if published_bundle_root else None
    )
    canonical_json = json.dumps(canonical_payload, sort_keys=True, indent=2, ensure_ascii=False) + '\n'
    document_sha256 = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    line_count = len(canonical_json.splitlines())
    byte_count = len(canonical_json.encode('utf-8'))
    summary_line = (
        f"Deterministic board export document: {canonical_payload.get('member_count', 0)} member(s) are serialized to "
        f"{relative_document_path} with fingerprint {document_sha256[:12]}."
    )
    return UiWorkboardExportDocument(
        schema_version='oracle_operator_board_export_document/v1',
        document_family='oracle_operator_board_export_document',
        document_media_type='application/json',
        summary_line=summary_line,
        relative_document_path=relative_document_path,
        published_relative_document_path=published_relative_document_path,
        document_sha256=document_sha256,
        byte_count=byte_count,
        line_count=line_count,
        export_state=canonical_payload.get('export_state'),
        export_completeness_state=canonical_payload.get('export_completeness_state'),
        verification_state=canonical_payload.get('verification_state'),
        generated_at_utc=canonical_payload.get('generated_at_utc'),
        canonical_payload=canonical_payload_model,
        canonical_json=canonical_json,
    ).to_payload()


__all__ = [
    'canonicalize_ui_workboard_export_payload',
    'serialize_ui_workboard_export_document',
]
