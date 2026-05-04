from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from strategy_validator.contracts.data_spine import DataSpineAuditSeal, PITJoinProvenance
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticMaterializationEvidenceIssue,
    SemanticMaterializationEvidenceVerificationReport,
    SemanticResearchFeatureMaterialization,
)
from strategy_validator.core.enums import EvidenceType

_SOURCE_MODULE = "strategy_validator.application.research_evidence_bridge"
_SCHEMA_VERSION = "semantic_research_materialization_evidence/v1"
_DATA_SPINE_SEAL_VERSION = "semantic_research_data_spine/v1"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=True)


def _canonical_json_default(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, allow_nan=True)


def _checksum_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def build_semantic_materialization_evidence(
    materialization: SemanticResearchFeatureMaterialization,
    *,
    timestamp: datetime | None = None,
) -> Evidence:
    """Convert a typed semantic PIT materialization into adjudication evidence.

    The bridge is intentionally read/contract-only: it does not adjudicate and
    does not write the ledger. It gives the research intake lane a deterministic
    evidence item that can be attached to an ``ExperimentManifest`` and inspected
    by downstream gates without bypassing the orchestrator's authority boundary.
    """
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "experiment_id": materialization.experiment_id,
        "asset_id": materialization.asset_id,
        "feature_event_id": materialization.feature_event_id,
        "joined_row_count": materialization.joined_row_count,
        "feature_row": materialization.feature_row.model_dump(mode="json"),
        "pit_provenance": materialization.pit_provenance.model_dump(mode="json"),
        "adjudication_use": {
            "semantic_signal_available": materialization.joined_row_count > 0,
            "abstained": materialization.feature_row.abstain_flag,
            "missingness_reason": materialization.feature_row.missingness_reason,
            "pit_dataset_id": materialization.pit_provenance.dataset_id,
            "pit_row_count_after": materialization.pit_provenance.row_count_after,
        },
    }
    return Evidence(
        evidence_id=f"semantic-materialization:{materialization.experiment_id}:{materialization.feature_event_id}",
        experiment_id=materialization.experiment_id,
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        timestamp=timestamp or datetime.now(timezone.utc),
        payload=payload,
        source_module=_SOURCE_MODULE,
        checksum=_checksum_payload(payload),
    )


def verify_semantic_materialization_evidence(
    evidence: Evidence,
    *,
    materialization: SemanticResearchFeatureMaterialization | None = None,
    proposal: ExperimentManifest | None = None,
) -> SemanticMaterializationEvidenceVerificationReport:
    """Verify that semantic materialization evidence is deterministic and aligned.

    This gives the research intake lane a cheap pre-adjudication gate: checksum,
    schema, source module, experiment identity, and optional materialization/PIT
    alignment are checked before the orchestrator sees the evidence bundle.
    """
    issues: list[SemanticMaterializationEvidenceIssue] = []

    def issue(code: str, message: str, severity: str = "BLOCKER") -> None:
        issues.append(SemanticMaterializationEvidenceIssue(code=code, message=message, severity=severity))

    if evidence.evidence_type is not EvidenceType.TRIBUNAL_OPINION:
        issue("SEMANTIC_EVIDENCE_TYPE_MISMATCH", "semantic materialization evidence must use TRIBUNAL_OPINION")
    if evidence.source_module != _SOURCE_MODULE:
        issue("SEMANTIC_EVIDENCE_SOURCE_MISMATCH", f"unexpected source_module={evidence.source_module!r}")
    if evidence.payload.get("schema_version") != _SCHEMA_VERSION:
        issue("SEMANTIC_EVIDENCE_SCHEMA_MISMATCH", "unexpected or missing semantic evidence schema_version")

    expected_checksum = _checksum_payload(evidence.payload)
    if evidence.checksum != expected_checksum:
        issue("SEMANTIC_EVIDENCE_CHECKSUM_MISMATCH", "evidence checksum does not match canonical payload")

    payload_experiment_id = evidence.payload.get("experiment_id")
    if payload_experiment_id != evidence.experiment_id:
        issue("SEMANTIC_EVIDENCE_EXPERIMENT_MISMATCH", "payload experiment_id differs from evidence experiment_id")

    if proposal is not None and evidence.experiment_id != proposal.experiment_id:
        issue("SEMANTIC_EVIDENCE_PROPOSAL_MISMATCH", "evidence experiment_id differs from proposal experiment_id")

    if materialization is not None:
        if evidence.experiment_id != materialization.experiment_id:
            issue("SEMANTIC_EVIDENCE_MATERIALIZATION_EXPERIMENT_MISMATCH", "evidence/materialization experiment_id mismatch")
        if evidence.payload.get("feature_event_id") != materialization.feature_event_id:
            issue("SEMANTIC_EVIDENCE_FEATURE_EVENT_MISMATCH", "evidence/materialization feature_event_id mismatch")
        if evidence.payload.get("asset_id") != materialization.asset_id:
            issue("SEMANTIC_EVIDENCE_ASSET_MISMATCH", "evidence/materialization asset_id mismatch")
        pit_payload = evidence.payload.get("pit_provenance")
        if isinstance(pit_payload, dict):
            if pit_payload.get("dataset_id") != materialization.pit_provenance.dataset_id:
                issue("SEMANTIC_EVIDENCE_PIT_DATASET_MISMATCH", "evidence/materialization PIT dataset_id mismatch")
            if pit_payload.get("row_count_after") != materialization.pit_provenance.row_count_after:
                issue("SEMANTIC_EVIDENCE_PIT_ROW_COUNT_MISMATCH", "evidence/materialization PIT row_count_after mismatch")
        else:
            issue("SEMANTIC_EVIDENCE_PIT_PAYLOAD_MISSING", "semantic evidence payload lacks pit_provenance")

    return SemanticMaterializationEvidenceVerificationReport(
        evidence_id=evidence.evidence_id,
        experiment_id=evidence.experiment_id,
        verified=not any(item.severity == "BLOCKER" for item in issues),
        checksum=evidence.checksum,
        expected_checksum=expected_checksum,
        schema_version=str(evidence.payload.get("schema_version") or ""),
        issue_count=len(issues),
        issues=issues,
    )


def _data_spine_fingerprint(provenance_items: list[PITJoinProvenance]) -> str:
    payload = {
        "schema_version": _DATA_SPINE_SEAL_VERSION,
        "as_of_provenance": [item.model_dump(mode="json") for item in provenance_items],
    }
    return hashlib.sha256(_canonical_json_default(payload).encode("utf-8")).hexdigest()


def build_semantic_materialization_data_spine_seal(
    materialization: SemanticResearchFeatureMaterialization,
    *,
    existing: DataSpineAuditSeal | None = None,
) -> DataSpineAuditSeal:
    """Build a deterministic DataSpineAuditSeal from semantic PIT provenance."""
    provenance_items = list(existing.as_of_provenance) if existing is not None else []
    candidate = materialization.pit_provenance
    candidate_key = (
        candidate.dataset_id,
        candidate.decision_time_utc,
        candidate.available_at_cutoff_utc,
        candidate.row_count_after,
    )
    existing_keys = {
        (item.dataset_id, item.decision_time_utc, item.available_at_cutoff_utc, item.row_count_after)
        for item in provenance_items
    }
    if candidate_key not in existing_keys:
        provenance_items.append(candidate)
    return DataSpineAuditSeal(
        spine_version=_DATA_SPINE_SEAL_VERSION,
        as_of_provenance=provenance_items,
        path_provenance=existing.path_provenance if existing is not None else None,
        universe_provenance=existing.universe_provenance if existing is not None else None,
        fingerprint=_data_spine_fingerprint(provenance_items),
    )


def attach_semantic_materialization_data_spine_seal(
    proposal: ExperimentManifest,
    materialization: SemanticResearchFeatureMaterialization,
) -> DataSpineAuditSeal:
    """Attach or update the proposal's Data Spine seal with semantic PIT lineage."""
    if proposal.experiment_id != materialization.experiment_id:
        raise ValueError(
            "proposal/materialization experiment_id mismatch: "
            f"{proposal.experiment_id!r} != {materialization.experiment_id!r}"
        )
    seal = build_semantic_materialization_data_spine_seal(
        materialization,
        existing=proposal.evidence_bundle.data_spine_seal,
    )
    proposal.evidence_bundle.data_spine_seal = seal
    return seal


def attach_semantic_materialization_evidence(
    proposal: ExperimentManifest,
    materialization: SemanticResearchFeatureMaterialization,
    *,
    timestamp: datetime | None = None,
    attach_data_spine_seal: bool = True,
) -> Evidence:
    """Attach semantic materialization evidence to a proposal manifest.

    This is the first bounded research-to-adjudication bridge: proposal and PIT
    materialization identifiers must match, the returned evidence is checksummed
    for reproducible downstream ledger snapshots, and the bundle can be sealed
    with PIT provenance for the data-spine audit trail.
    """
    if proposal.experiment_id != materialization.experiment_id:
        raise ValueError(
            "proposal/materialization experiment_id mismatch: "
            f"{proposal.experiment_id!r} != {materialization.experiment_id!r}"
        )
    evidence = build_semantic_materialization_evidence(materialization, timestamp=timestamp)
    report = verify_semantic_materialization_evidence(evidence, materialization=materialization, proposal=proposal)
    if not report.verified:
        blocker_codes = ", ".join(item.code for item in report.issues if item.severity == "BLOCKER")
        raise ValueError(f"semantic materialization evidence failed verification: {blocker_codes}")
    proposal.evidence_bundle.evidence_items.append(evidence)
    if attach_data_spine_seal:
        attach_semantic_materialization_data_spine_seal(proposal, materialization)
    return evidence


__all__ = [
    "build_semantic_materialization_evidence",
    "verify_semantic_materialization_evidence",
    "build_semantic_materialization_data_spine_seal",
    "attach_semantic_materialization_data_spine_seal",
    "attach_semantic_materialization_evidence",
]
