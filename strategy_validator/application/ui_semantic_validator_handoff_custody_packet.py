"""Deterministic custody packet and seal-template synthesis."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_custody_common import (
    _CUSTODY_SEAL_SCHEMA_VERSION,
    _RECORDED_SIGNOFF_STATUS,
    _digest,
    _s,
)


def _custody_packet_digest(signoff: dict[str, Any]) -> str:
    packet = signoff.get("custody_packet")
    if isinstance(packet, dict):
        return _s(packet.get("packet_digest"))
    return _digest(
        [
            signoff.get("signoff_gate_id"),
            signoff.get("signoff_id"),
            signoff.get("decision_id"),
            signoff.get("decision_packet_digest"),
            signoff.get("human_reviewer_id"),
            signoff.get("signed_at_utc"),
            "custody_seal_packet/v1",
            "submit=false",
            "promote=false",
            "execute=false",
        ]
    )


def _custody_packet(signoff: dict[str, Any]) -> dict[str, Any]:
    source_signoff = signoff.get("selected_signoff") if isinstance(signoff.get("selected_signoff"), dict) else {}
    source_evidence = {
        "signoff_gate_id": signoff.get("signoff_gate_id"),
        "signoff_id": signoff.get("signoff_id"),
        "decision_id": signoff.get("decision_id"),
        "review_id": signoff.get("review_id"),
        "chain_id": signoff.get("chain_id"),
        "chain_digest": signoff.get("chain_digest"),
        "experiment_id": signoff.get("experiment_id"),
        "decision_packet_digest": signoff.get("decision_packet_digest"),
        "signoff_artifact_sha256": source_signoff.get("artifact_sha256"),
        "human_reviewer_id": signoff.get("human_reviewer_id"),
        "signed_at_utc": signoff.get("signed_at_utc"),
        "source_signoff_status": signoff.get("signoff_status"),
    }
    packet_digest = _digest([
        source_evidence,
        "semantic_validator_handoff_custody_packet/v1",
        "write=false",
        "submit=false",
        "promote=false",
        "execute=false",
    ])
    return {
        "packet_schema_version": "semantic_validator_handoff_custody_packet/v1",
        "packet_digest": packet_digest,
        "recommended_next_step": "CREATE_EXTERNAL_CUSTODY_SEAL"
        if signoff.get("signoff_status") == _RECORDED_SIGNOFF_STATUS
        else "DO_NOT_SEAL_SIGNOFF_REQUIRED",
        "human_custodian_id": "<REQUIRED_EXTERNALLY>",
        "custody_statement": "<REQUIRED_EXTERNALLY>",
        "sealed_at_utc": "<REQUIRED_EXTERNALLY>",
        "source_evidence": source_evidence,
        "authority_assertions": {
            "read_plane_only": True,
            "custody_seal_write_allowed": False,
            "archive_write_allowed": False,
            "artifact_mutation_allowed": False,
            "validator_submission_allowed": False,
            "adjudication_allowed": False,
            "promotion_allowed": False,
            "execution_allowed": False,
        },
    }


def _custody_template(signoff: dict[str, Any], custody_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _CUSTODY_SEAL_SCHEMA_VERSION,
        "artifact_kind": "semantic_validator_handoff_custody_seal",
        "custody_seal_id": f"semantic-validator-custody-seal-{_digest([signoff.get('signoff_gate_id'), custody_packet.get('packet_digest')])[:20]}",
        "signoff_gate_id": signoff.get("signoff_gate_id"),
        "signoff_id": signoff.get("signoff_id"),
        "decision_id": signoff.get("decision_id"),
        "chain_id": signoff.get("chain_id"),
        "experiment_id": signoff.get("experiment_id"),
        "custody_packet_digest": custody_packet.get("packet_digest"),
        "source_signoff_status": signoff.get("signoff_status"),
        "source_decision_packet_digest": signoff.get("decision_packet_digest"),
        "human_custodian_id": "<REQUIRED_EXTERNALLY>",
        "custody_statement": "<REQUIRED_EXTERNALLY>",
        "sealed_at_utc": "<REQUIRED_EXTERNALLY>",
        "source_evidence": custody_packet.get("source_evidence", {}),
        "authority_assertions": custody_packet.get("authority_assertions", {}),
    }
