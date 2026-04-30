from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.application.research_integrity_preflight import _is_semantic_materialization_evidence
from strategy_validator.contracts.experiments import ExperimentManifest


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=True).encode("utf-8")


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _proposal_digest_for_semantic_gate(proposal: ExperimentManifest) -> str:
    """Digest the proposal fields that the semantic gate depends on."""
    bundle = proposal.evidence_bundle
    payload = {
        "experiment_id": proposal.experiment_id,
        "strategy_name": proposal.strategy_name,
        "semantic_artifacts": [item.model_dump(mode="json") for item in bundle.semantic_artifacts],
        "semantic_evidence": [
            item.model_dump(mode="json")
            for item in bundle.evidence_items
            if _is_semantic_materialization_evidence(item)
        ],
        "data_spine_seal": None if bundle.data_spine_seal is None else bundle.data_spine_seal.model_dump(mode="json"),
    }
    return _sha256_payload(payload)


def _semantic_evidence_checksums(proposal: ExperimentManifest) -> list[str]:
    return [
        item.checksum
        for item in proposal.evidence_bundle.evidence_items
        if _is_semantic_materialization_evidence(item)
    ]


__all__ = [
    "_canonical_json_bytes",
    "_sha256_payload",
    "_proposal_digest_for_semantic_gate",
    "_semantic_evidence_checksums",
]
