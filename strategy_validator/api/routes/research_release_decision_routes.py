"""Semantic adjudication release decision record and ledger routes."""

from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.research_release_common import *  # noqa: F403

router = APIRouter()

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
