"""Deterministic archive packet and manifest template synthesis."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_archive_common import (
    _ARCHIVE_SCHEMA_VERSION,
    _RECORDED_CUSTODY_STATUS,
    _digest,
)


def _archive_packet(custody: dict[str, Any]) -> dict[str, Any]:
    source_seal = custody.get("selected_custody_seal") if isinstance(custody.get("selected_custody_seal"), dict) else {}
    source_evidence = {
        "custody_gate_id": custody.get("custody_gate_id"),
        "custody_seal_id": custody.get("custody_seal_id"),
        "signoff_gate_id": custody.get("signoff_gate_id"),
        "signoff_id": custody.get("signoff_id"),
        "decision_id": custody.get("decision_id"),
        "review_id": custody.get("review_id"),
        "chain_id": custody.get("chain_id"),
        "chain_digest": custody.get("chain_digest"),
        "experiment_id": custody.get("experiment_id"),
        "decision_packet_digest": custody.get("decision_packet_digest"),
        "custody_packet_digest": custody.get("custody_packet_digest"),
        "custody_seal_artifact_sha256": source_seal.get("artifact_sha256"),
        "human_custodian_id": custody.get("human_custodian_id"),
        "sealed_at_utc": custody.get("sealed_at_utc"),
        "source_custody_status": custody.get("custody_status"),
    }
    packet_digest = _digest([source_evidence, "semantic_validator_handoff_archive_packet/v1", "archive_write=false", "submit=false", "promote=false", "execute=false"])
    return {
        "packet_schema_version": "semantic_validator_handoff_archive_packet/v1",
        "packet_digest": packet_digest,
        "recommended_next_step": "CREATE_EXTERNAL_ARCHIVE_MANIFEST" if custody.get("custody_status") == _RECORDED_CUSTODY_STATUS else "DO_NOT_ARCHIVE_CUSTODY_SEAL_REQUIRED",
        "archive_root": "<REQUIRED_EXTERNALLY>",
        "manifest_artifact_count": "<REQUIRED_EXTERNALLY>",
        "archived_by": "<REQUIRED_EXTERNALLY>",
        "created_at_utc": "<REQUIRED_EXTERNALLY>",
        "source_evidence": source_evidence,
        "authority_assertions": {
            "read_plane_only": True,
            "archive_write_allowed": False,
            "artifact_mutation_allowed": False,
            "validator_submission_allowed": False,
            "adjudication_allowed": False,
            "promotion_allowed": False,
            "execution_allowed": False,
        },
    }


def _archive_template(custody: dict[str, Any], archive_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _ARCHIVE_SCHEMA_VERSION,
        "artifact_kind": "semantic_validator_handoff_archive_manifest",
        "archive_manifest_id": f"semantic-validator-archive-manifest-{_digest([custody.get('custody_gate_id'), archive_packet.get('packet_digest')])[:20]}",
        "custody_gate_id": custody.get("custody_gate_id"),
        "custody_seal_id": custody.get("custody_seal_id"),
        "signoff_gate_id": custody.get("signoff_gate_id"),
        "decision_id": custody.get("decision_id"),
        "chain_id": custody.get("chain_id"),
        "experiment_id": custody.get("experiment_id"),
        "archive_packet_digest": archive_packet.get("packet_digest"),
        "source_custody_status": custody.get("custody_status"),
        "source_custody_packet_digest": custody.get("custody_packet_digest"),
        "archive_root": "<REQUIRED_EXTERNALLY>",
        "manifest_artifact_count": "<REQUIRED_EXTERNALLY>",
        "archived_by": "<REQUIRED_EXTERNALLY>",
        "created_at_utc": "<REQUIRED_EXTERNALLY>",
        "source_evidence": archive_packet.get("source_evidence", {}),
        "authority_assertions": archive_packet.get("authority_assertions", {}),
    }
