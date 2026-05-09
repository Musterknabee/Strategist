"""Artifact entry builders for semantic validator handoff read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.research_integrity_release_handoff import (
    summarize_semantic_adjudication_release_decision_ledger,
    summarize_semantic_adjudication_release_handoff_certificate,
    verify_semantic_adjudication_release_decision_ledger,
    verify_semantic_adjudication_release_handoff_certificate,
)
from strategy_validator.application.research_integrity_validator_handoff import (
    summarize_semantic_validator_handoff_packet,
    summarize_semantic_validator_handoff_packet_ingress_certificate,
    verify_semantic_validator_handoff_packet,
    verify_semantic_validator_handoff_packet_ingress_certificate,
)
from strategy_validator.application.ui_semantic_validator_handoff_common import _sha256
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseHandoffCertificate,
)
from strategy_validator.contracts.semantic_validator_handoff import (
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIngressCertificate,
)


def _base_entry(
    *,
    artifact_kind: str,
    schema_version: str,
    artifact_id: str,
    experiment_id: str,
    payload_checksum: str | None,
    path: Path,
    verified: bool,
    handoff_allowed: bool,
    ready_for_validator_ingress: bool | None,
    recommended_action: str,
    blocker_codes: list[str],
    warning_codes: list[str],
    issue_codes: list[str],
    summary_line: str,
    include_raw: bool,
    raw: dict[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "artifact_kind": artifact_kind,
        "schema_version": schema_version,
        "artifact_id": artifact_id,
        "experiment_id": experiment_id,
        "payload_checksum": payload_checksum,
        "artifact_sha256": _sha256(path),
        "artifact_path": str(path.as_posix()),
        "verified": verified,
        "handoff_allowed": handoff_allowed,
        "ready_for_validator_ingress": ready_for_validator_ingress,
        "recommended_action": recommended_action,
        "blocker_codes": list(dict.fromkeys(blocker_codes)),
        "warning_codes": list(dict.fromkeys(warning_codes)),
        "issue_codes": list(dict.fromkeys(issue_codes)),
        "issue_count": len(list(dict.fromkeys(issue_codes))) if issue_codes else len(blocker_codes) + len(warning_codes),
        "summary_line": summary_line,
        **extra,
    }
    if include_raw:
        entry["raw_artifact"] = raw
    return entry


def _decision_ledger_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(raw)
    report = verify_semantic_adjudication_release_decision_ledger(ledger)
    summary = summarize_semantic_adjudication_release_decision_ledger(ledger, verification=report)
    terminal_entry = ledger.entries[-1] if ledger.entries else None
    return _base_entry(
        artifact_kind="decision_ledger",
        schema_version=ledger.schema_version,
        artifact_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        payload_checksum=ledger.payload_checksum,
        path=path,
        verified=report.verified,
        handoff_allowed=bool(summary.terminal_decision_allowed and summary.recommended_action == "HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR"),
        ready_for_validator_ingress=None,
        recommended_action=summary.recommended_action,
        blocker_codes=list(summary.blocker_codes),
        warning_codes=list(summary.warning_codes),
        issue_codes=list(dict.fromkeys([*summary.ledger_issue_codes, *report.issue_codes])),
        summary_line=f"decision_ledger · {ledger.experiment_id} · entries={ledger.entry_count} · verified={report.verified}",
        include_raw=include_raw,
        raw=raw,
        ledger_id=ledger.ledger_id,
        certificate_id=None,
        packet_id=None,
        evidence_id=None,
        entry_count=ledger.entry_count,
        accepted_decision_count=ledger.accepted_decision_count,
        blocked_decision_count=ledger.blocked_decision_count,
        terminal_decision_id=None if terminal_entry is None else terminal_entry.decision_id,
        terminal_decision=None if terminal_entry is None else terminal_entry.decision,
        terminal_decision_allowed=False if terminal_entry is None else terminal_entry.decision_allowed,
        terminal_recommended_action=ledger.terminal_recommended_action,
        verification=report.model_dump(mode="json"),
        summary=summary.model_dump(mode="json"),
    )


def _handoff_certificate_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    cert = SemanticAdjudicationReleaseHandoffCertificate.model_validate(raw)
    report = verify_semantic_adjudication_release_handoff_certificate(cert)
    summary = summarize_semantic_adjudication_release_handoff_certificate(cert, verification=report)
    return _base_entry(
        artifact_kind="handoff_certificate",
        schema_version=cert.schema_version,
        artifact_id=cert.certificate_id,
        experiment_id=cert.experiment_id,
        payload_checksum=cert.payload_checksum,
        path=path,
        verified=report.verified,
        handoff_allowed=report.handoff_allowed,
        ready_for_validator_ingress=None,
        recommended_action=summary.recommended_action,
        blocker_codes=list(summary.blocker_codes),
        warning_codes=list(summary.warning_codes),
        issue_codes=list(dict.fromkeys([*summary.certificate_issue_codes, *report.issue_codes])),
        summary_line=f"handoff_certificate · {cert.experiment_id} · allowed={report.handoff_allowed} · verified={report.verified}",
        include_raw=include_raw,
        raw=raw,
        ledger_id=cert.ledger_id,
        certificate_id=cert.certificate_id,
        packet_id=None,
        evidence_id=None,
        terminal_decision_id=cert.terminal_decision_id,
        terminal_decision=cert.terminal_decision,
        terminal_decision_allowed=cert.handoff_allowed,
        ledger_payload_checksum=cert.ledger_payload_checksum,
        issued_by=cert.issued_by,
        issue_reason=cert.issue_reason,
        verification=report.model_dump(mode="json"),
        summary=summary.model_dump(mode="json"),
    )


def _validator_packet_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    packet = SemanticValidatorHandoffPacket.model_validate(raw)
    report = verify_semantic_validator_handoff_packet(packet)
    summary = summarize_semantic_validator_handoff_packet(packet)
    return _base_entry(
        artifact_kind="validator_packet",
        schema_version=packet.schema_version,
        artifact_id=packet.packet_id,
        experiment_id=packet.experiment_id,
        payload_checksum=packet.payload_checksum,
        path=path,
        verified=report.verified,
        handoff_allowed=report.handoff_allowed,
        ready_for_validator_ingress=None,
        recommended_action=summary.recommended_action,
        blocker_codes=list(summary.blocker_codes),
        warning_codes=list(summary.warning_codes),
        issue_codes=list(dict.fromkeys([*summary.issue_codes, *report.issue_codes])),
        summary_line=f"validator_packet · {packet.experiment_id} · allowed={report.handoff_allowed} · verified={report.verified}",
        include_raw=include_raw,
        raw=raw,
        ledger_id=None,
        certificate_id=packet.certificate_id,
        packet_id=packet.packet_id,
        evidence_id=packet.evidence_id,
        evidence_payload_checksum=packet.evidence_payload_checksum,
        certificate_payload_checksum=packet.certificate_payload_checksum,
        packet_verified=summary.packet_verified,
        evidence_verified=summary.evidence_verified,
        verification=report.model_dump(mode="json"),
        summary=summary.model_dump(mode="json"),
    )


def _ingress_certificate_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    cert = SemanticValidatorHandoffPacketIngressCertificate.model_validate(raw)
    report = verify_semantic_validator_handoff_packet_ingress_certificate(cert, require_packet_evidence_on_proposal=False)
    summary = summarize_semantic_validator_handoff_packet_ingress_certificate(cert, require_packet_evidence_on_proposal=False)
    return _base_entry(
        artifact_kind="ingress_certificate",
        schema_version=cert.schema_version,
        artifact_id=cert.certificate_id,
        experiment_id=cert.experiment_id,
        payload_checksum=cert.payload_checksum,
        path=path,
        verified=report.verified,
        handoff_allowed=report.ready_for_validator_ingress,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        recommended_action=summary.recommended_action,
        blocker_codes=list(summary.blocker_codes),
        warning_codes=list(summary.warning_codes),
        issue_codes=list(dict.fromkeys([*summary.issue_codes, *report.issue_codes])),
        summary_line=f"ingress_certificate · {cert.experiment_id} · ready={report.ready_for_validator_ingress} · verified={report.verified}",
        include_raw=include_raw,
        raw=raw,
        ledger_id=None,
        certificate_id=cert.certificate_id,
        packet_id=cert.packet_id,
        evidence_id=cert.evidence_id,
        packet_payload_checksum=cert.packet_payload_checksum,
        evidence_payload_checksum=cert.evidence_payload_checksum,
        issued_by=cert.issued_by,
        issue_reason=cert.issue_reason,
        verification=report.model_dump(mode="json"),
        summary=summary.model_dump(mode="json"),
    )


def _artifact_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    schema = str(raw.get("schema_version") or "")
    if schema == "semantic_adjudication_release_decision_ledger/v1":
        return _decision_ledger_entry(path, raw, include_raw=include_raw)
    if schema == "semantic_adjudication_release_handoff_certificate/v1":
        return _handoff_certificate_entry(path, raw, include_raw=include_raw)
    if schema == "semantic_validator_handoff_packet/v1":
        return _validator_packet_entry(path, raw, include_raw=include_raw)
    if schema == "semantic_validator_handoff_packet_ingress_certificate/v1":
        return _ingress_certificate_entry(path, raw, include_raw=include_raw)
    raise ValueError(f"unsupported_semantic_validator_handoff_schema:{schema or 'missing'}")
