"""Semantic release and bundle packaging research routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle_manifest,
    summarize_semantic_adjudication_bundle,
    verify_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_preflight,
    build_semantic_adjudication_bundle_release_index,
    verify_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_release_capsule,
    verify_semantic_adjudication_release_capsule,
    summarize_semantic_adjudication_release_capsule,
    build_semantic_adjudication_release_decision_record,
    verify_semantic_adjudication_release_decision_record,
    summarize_semantic_adjudication_release_decision_record,
    build_semantic_adjudication_release_decision_ledger,
    verify_semantic_adjudication_release_decision_ledger,
    summarize_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    verify_semantic_adjudication_release_handoff_certificate,
    summarize_semantic_adjudication_release_handoff_certificate,
    build_semantic_release_handoff_certificate_evidence,
    verify_semantic_release_handoff_certificate_evidence,
    summarize_semantic_release_handoff_certificate_evidence,
)
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseHandoffCertificate,
)

router = APIRouter()


class SemanticAdjudicationBundleVerificationRequest(BaseModel):
    bundle: dict[str, Any]
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleManifestRequest(BaseModel):
    bundle: dict[str, Any]
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleManifestVerificationRequest(BaseModel):
    manifest: dict[str, Any]
    bundle: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None


class SemanticAdjudicationBundleReleasePreflightRequest(BaseModel):
    bundle: dict[str, Any]
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/summary")
def semantic_adjudication_bundle_summary(
    request: SemanticAdjudicationBundleVerificationRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)
    return summary.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/manifest")
def semantic_adjudication_bundle_manifest(request: SemanticAdjudicationBundleManifestRequest) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    return manifest.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/manifest/verify")
def semantic_adjudication_bundle_manifest_verify(
    request: SemanticAdjudicationBundleManifestVerificationRequest,
) -> dict[str, object]:
    manifest = SemanticAdjudicationBundleManifest.model_validate(request.manifest)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_bundle_manifest(manifest, bundle=bundle, proposal=proposal)
    return report.model_dump(mode="json")


class SemanticAdjudicationBundleReleaseIndexRequest(BaseModel):
    bundle: dict[str, Any]
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


class SemanticAdjudicationBundleReleaseIndexVerificationRequest(BaseModel):
    index: dict[str, Any]
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/release-preflight")
def semantic_adjudication_bundle_release_preflight(
    request: SemanticAdjudicationBundleReleasePreflightRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = build_semantic_adjudication_bundle_release_preflight(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-index")
def semantic_adjudication_bundle_release_index(
    request: SemanticAdjudicationBundleReleaseIndexRequest,
) -> dict[str, object]:
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle)
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    index = build_semantic_adjudication_bundle_release_index(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return index.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-index/verify")
def semantic_adjudication_bundle_release_index_verify(
    request: SemanticAdjudicationBundleReleaseIndexVerificationRequest,
) -> dict[str, object]:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_bundle_release_index(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")



class SemanticAdjudicationReleaseCapsuleRequest(BaseModel):
    index: dict[str, Any]
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


class SemanticAdjudicationReleaseCapsuleVerificationRequest(BaseModel):
    capsule: dict[str, Any]
    index: dict[str, Any] | None = None
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/release-capsule")
def semantic_adjudication_release_capsule(
    request: SemanticAdjudicationReleaseCapsuleRequest,
) -> dict[str, object]:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index)
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    capsule = build_semantic_adjudication_release_capsule(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return capsule.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-capsule/verify")
def semantic_adjudication_release_capsule_verify(
    request: SemanticAdjudicationReleaseCapsuleVerificationRequest,
) -> dict[str, object]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule)
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-capsule/summary")
def summarize_release_capsule_route(
    request: SemanticAdjudicationReleaseCapsuleVerificationRequest,
) -> dict[str, object]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule)
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return summary.model_dump(mode="json")
class SemanticAdjudicationReleaseDecisionRecordRequest(BaseModel):
    capsule: dict[str, Any]
    decision: str | None = None
    decided_by: str = "operator"
    decision_reason: str | None = None
    index: dict[str, Any] | None = None
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


class SemanticAdjudicationReleaseDecisionRecordVerificationRequest(BaseModel):
    decision_record: dict[str, Any]
    capsule: dict[str, Any] | None = None
    index: dict[str, Any] | None = None
    bundle: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    require_manifest: bool = True


@router.post("/semantic-adjudication-bundle/release-decision-record")
def semantic_adjudication_release_decision_record(
    request: SemanticAdjudicationReleaseDecisionRecordRequest,
) -> dict[str, object]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule)
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    record = build_semantic_adjudication_release_decision_record(
        capsule,
        decision=request.decision,
        decided_by=request.decided_by,
        decision_reason=request.decision_reason,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return record.model_dump(mode="json")




@router.post("/semantic-adjudication-bundle/release-decision-record/summary")
def semantic_adjudication_release_decision_record_summary(
    request: SemanticAdjudicationReleaseDecisionRecordVerificationRequest,
) -> dict[str, object]:
    record = SemanticAdjudicationReleaseDecisionRecord.model_validate(request.decision_record)
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule) if request.capsule is not None else None
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    summary = summarize_semantic_adjudication_release_decision_record(
        record,
        capsule=capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return summary.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-decision-record/verify")
def semantic_adjudication_release_decision_record_verify(
    request: SemanticAdjudicationReleaseDecisionRecordVerificationRequest,
) -> dict[str, object]:
    record = SemanticAdjudicationReleaseDecisionRecord.model_validate(request.decision_record)
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(request.capsule) if request.capsule is not None else None
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(request.index) if request.index is not None else None
    bundle = SemanticAdjudicationBundle.model_validate(request.bundle) if request.bundle is not None else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(request.manifest)
        if request.manifest is not None
        else None
    )
    proposal = ExperimentManifest.model_validate(request.proposal) if request.proposal is not None else None
    report = verify_semantic_adjudication_release_decision_record(
        record,
        capsule=capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=request.require_manifest,
    )
    return report.model_dump(mode="json")



class SemanticAdjudicationReleaseDecisionLedgerRequest(BaseModel):
    decision_records: list[dict[str, Any]]


class SemanticAdjudicationReleaseDecisionLedgerVerificationRequest(BaseModel):
    decision_ledger: dict[str, Any]
    decision_records: list[dict[str, Any]] | None = None


@router.post("/semantic-adjudication-bundle/release-decision-ledger")
def semantic_adjudication_release_decision_ledger(
    request: SemanticAdjudicationReleaseDecisionLedgerRequest,
) -> dict[str, object]:
    records = [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
    ledger = build_semantic_adjudication_release_decision_ledger(records)
    return ledger.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-decision-ledger/verify")
def semantic_adjudication_release_decision_ledger_verify(
    request: SemanticAdjudicationReleaseDecisionLedgerVerificationRequest,
) -> dict[str, object]:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    report = verify_semantic_adjudication_release_decision_ledger(ledger, records=records)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-decision-ledger/summary")
def semantic_adjudication_release_decision_ledger_summary(
    request: SemanticAdjudicationReleaseDecisionLedgerVerificationRequest,
) -> dict[str, object]:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    summary = summarize_semantic_adjudication_release_decision_ledger(ledger, records=records)
    return summary.model_dump(mode="json")


class SemanticAdjudicationReleaseHandoffCertificateRequest(BaseModel):
    decision_ledger: dict[str, Any]
    decision_records: list[dict[str, Any]] | None = None
    issued_by: str = "operator"
    issue_reason: str | None = None


class SemanticAdjudicationReleaseHandoffCertificateVerificationRequest(BaseModel):
    certificate: dict[str, Any]
    decision_ledger: dict[str, Any] | None = None
    decision_records: list[dict[str, Any]] | None = None


@router.post("/semantic-adjudication-bundle/release-handoff-certificate")
def semantic_adjudication_release_handoff_certificate(
    request: SemanticAdjudicationReleaseHandoffCertificateRequest,
) -> dict[str, object]:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    certificate = build_semantic_adjudication_release_handoff_certificate(
        ledger,
        records=records,
        issued_by=request.issued_by,
        issue_reason=request.issue_reason,
    )
    return certificate.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/verify")
def semantic_adjudication_release_handoff_certificate_verify(
    request: SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
        if request.decision_ledger is not None
        else None
    )
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    report = verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records,
    )
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/summary")
def semantic_adjudication_release_handoff_certificate_summary(
    request: SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(request.decision_ledger)
        if request.decision_ledger is not None
        else None
    )
    records = (
        [SemanticAdjudicationReleaseDecisionRecord.model_validate(item) for item in request.decision_records]
        if request.decision_records is not None
        else None
    )
    summary = summarize_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records,
    )
    return summary.model_dump(mode="json")


class SemanticReleaseHandoffCertificateEvidenceRequest(BaseModel):
    certificate: dict[str, Any]


class SemanticReleaseHandoffCertificateEvidenceVerificationRequest(BaseModel):
    evidence: dict[str, Any]


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence")
def semantic_adjudication_release_handoff_certificate_evidence(
    request: SemanticReleaseHandoffCertificateEvidenceRequest,
) -> dict[str, object]:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(request.certificate)
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    return evidence.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/verify")
def semantic_adjudication_release_handoff_certificate_evidence_verify(
    request: SemanticReleaseHandoffCertificateEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    report = verify_semantic_release_handoff_certificate_evidence(evidence)
    return report.model_dump(mode="json")


@router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary")
def semantic_adjudication_release_handoff_certificate_evidence_summary(
    request: SemanticReleaseHandoffCertificateEvidenceVerificationRequest,
) -> dict[str, object]:
    evidence = Evidence.model_validate(request.evidence)
    summary = summarize_semantic_release_handoff_certificate_evidence(evidence)
    return summary.model_dump(mode="json")
