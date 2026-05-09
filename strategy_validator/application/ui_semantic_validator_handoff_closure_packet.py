"""Closure packet and external attestation template synthesis."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_closure_common import (
    _CLOSURE_SCHEMA_VERSION,
    _digest,
)


def _closure_packet(archive: dict[str, Any]) -> dict[str, Any]:
    source_manifest = archive.get("selected_archive_manifest") if isinstance(archive.get("selected_archive_manifest"), dict) else {}
    source_evidence = {
        "archive_gate_id": archive.get("archive_gate_id"),
        "archive_manifest_id": archive.get("archive_manifest_id"),
        "custody_gate_id": archive.get("custody_gate_id"),
        "custody_seal_id": archive.get("custody_seal_id"),
        "signoff_gate_id": archive.get("signoff_gate_id"),
        "decision_id": archive.get("decision_id"),
        "review_id": archive.get("review_id"),
        "chain_id": archive.get("chain_id"),
        "chain_digest": archive.get("chain_digest"),
        "experiment_id": archive.get("experiment_id"),
        "decision_packet_digest": archive.get("decision_packet_digest"),
        "custody_packet_digest": archive.get("custody_packet_digest"),
        "archive_packet_digest": archive.get("archive_packet_digest"),
        "archive_manifest_artifact_sha256": source_manifest.get("artifact_sha256"),
        "archive_root": archive.get("archive_root"),
        "manifest_artifact_count": archive.get("manifest_artifact_count"),
        "archived_by": archive.get("archived_by"),
        "archive_created_at_utc": archive.get("created_at_utc"),
        "source_archive_status": archive.get("archive_status"),
    }
    packet_digest = _digest(
        [
            source_evidence,
            "semantic_validator_handoff_closure_packet/v1",
            "closure_write=false",
            "archive_write=false",
            "submit=false",
            "promote=false",
            "execute=false",
        ]
    )
    return {
        "packet_schema_version": "semantic_validator_handoff_closure_packet/v1",
        "packet_digest": packet_digest,
        "recommended_next_step": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
        "archive_gate_id": archive.get("archive_gate_id"),
        "archive_manifest_id": archive.get("archive_manifest_id"),
        "chain_id": archive.get("chain_id"),
        "experiment_id": archive.get("experiment_id"),
        "archive_packet_digest": archive.get("archive_packet_digest"),
        "source_evidence": source_evidence,
        "closure_attestation_template": {
            "schema_version": _CLOSURE_SCHEMA_VERSION,
            "artifact_kind": "semantic_validator_handoff_closure_attestation",
            "closure_attestation_id": "<REQUIRED_EXTERNALLY>",
            "archive_gate_id": archive.get("archive_gate_id"),
            "archive_manifest_id": archive.get("archive_manifest_id"),
            "custody_gate_id": archive.get("custody_gate_id"),
            "custody_seal_id": archive.get("custody_seal_id"),
            "signoff_gate_id": archive.get("signoff_gate_id"),
            "decision_id": archive.get("decision_id"),
            "chain_id": archive.get("chain_id"),
            "experiment_id": archive.get("experiment_id"),
            "archive_packet_digest": archive.get("archive_packet_digest"),
            "closure_packet_digest": packet_digest,
            "final_disposition": "<REQUIRED_EXTERNALLY>",
            "closure_statement": "<REQUIRED_EXTERNALLY>",
            "closed_by": "<REQUIRED_EXTERNALLY>",
            "closed_at_utc": "<REQUIRED_EXTERNALLY>",
            "authority_assertions": {
                "read_plane_only": True,
                "closure_write_allowed": False,
                "archive_write_allowed": False,
                "artifact_mutation_allowed": False,
                "validator_submission_allowed": False,
                "adjudication_allowed": False,
                "promotion_allowed": False,
                "execution_allowed": False,
            },
        },
        "authority_assertions": {
            "read_plane_only": True,
            "closure_write_allowed": False,
            "archive_write_allowed": False,
            "artifact_mutation_allowed": False,
            "validator_submission_allowed": False,
            "adjudication_allowed": False,
            "promotion_allowed": False,
            "execution_allowed": False,
        },
    }

def _closure_template(archive: dict[str, Any], closure_packet: dict[str, Any]) -> dict[str, Any]:
    template = closure_packet.get("closure_attestation_template")
    if isinstance(template, dict):
        return template
    return {
        "schema_version": _CLOSURE_SCHEMA_VERSION,
        "artifact_kind": "semantic_validator_handoff_closure_attestation",
        "archive_gate_id": archive.get("archive_gate_id"),
        "archive_manifest_id": archive.get("archive_manifest_id"),
        "closure_packet_digest": closure_packet.get("packet_digest"),
        "final_disposition": "<REQUIRED_EXTERNALLY>",
        "closure_statement": "<REQUIRED_EXTERNALLY>",
        "closed_by": "<REQUIRED_EXTERNALLY>",
        "closed_at_utc": "<REQUIRED_EXTERNALLY>",
    }


__all__ = ["_closure_packet", "_closure_template"]
