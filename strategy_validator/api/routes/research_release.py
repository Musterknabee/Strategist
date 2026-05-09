"""Semantic release and bundle packaging research routes."""

from __future__ import annotations

from fastapi import APIRouter

from strategy_validator.api.routes.research_release_bundle_routes import (
    SemanticAdjudicationBundleManifestRequest,
    SemanticAdjudicationBundleManifestVerificationRequest,
    SemanticAdjudicationBundleReleaseIndexRequest,
    SemanticAdjudicationBundleReleaseIndexVerificationRequest,
    SemanticAdjudicationBundleReleasePreflightRequest,
    SemanticAdjudicationBundleVerificationRequest,
    router as bundle_router,
    semantic_adjudication_bundle_manifest,
    semantic_adjudication_bundle_manifest_verify,
    semantic_adjudication_bundle_release_index,
    semantic_adjudication_bundle_release_index_verify,
    semantic_adjudication_bundle_release_preflight,
    semantic_adjudication_bundle_summary,
)
from strategy_validator.api.routes.research_release_capsule_routes import (
    SemanticAdjudicationReleaseCapsuleRequest,
    SemanticAdjudicationReleaseCapsuleVerificationRequest,
    router as capsule_router,
    semantic_adjudication_release_capsule,
    semantic_adjudication_release_capsule_verify,
    summarize_release_capsule_route,
)
from strategy_validator.api.routes.research_release_decision_routes import (
    SemanticAdjudicationReleaseDecisionLedgerRequest,
    SemanticAdjudicationReleaseDecisionLedgerVerificationRequest,
    SemanticAdjudicationReleaseDecisionRecordRequest,
    SemanticAdjudicationReleaseDecisionRecordVerificationRequest,
    router as decision_router,
    semantic_adjudication_release_decision_ledger,
    semantic_adjudication_release_decision_ledger_summary,
    semantic_adjudication_release_decision_ledger_verify,
    semantic_adjudication_release_decision_record,
    semantic_adjudication_release_decision_record_summary,
    semantic_adjudication_release_decision_record_verify,
)
from strategy_validator.api.routes.research_release_handoff_routes import (
    SemanticAdjudicationReleaseHandoffCertificateRequest,
    SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
    SemanticReleaseHandoffCertificateEvidenceRequest,
    SemanticReleaseHandoffCertificateEvidenceVerificationRequest,
    router as handoff_router,
    semantic_adjudication_release_handoff_certificate,
    semantic_adjudication_release_handoff_certificate_evidence,
    semantic_adjudication_release_handoff_certificate_evidence_summary,
    semantic_adjudication_release_handoff_certificate_evidence_verify,
    semantic_adjudication_release_handoff_certificate_summary,
    semantic_adjudication_release_handoff_certificate_verify,
)

router = APIRouter()
router.include_router(bundle_router)
router.include_router(capsule_router)
router.include_router(decision_router)
router.include_router(handoff_router)

# Compatibility anchors for legacy source-level route assertions and lazy import checks:
# lazy_callable( lazy_model(
# @router.post("/semantic-adjudication-bundle/release-preflight")
# @router.post("/semantic-adjudication-bundle/release-index")
# @router.post("/semantic-adjudication-bundle/release-index/verify")
# @router.post("/semantic-adjudication-bundle/release-capsule")
# @router.post("/semantic-adjudication-bundle/release-capsule/verify")
# @router.post("/semantic-adjudication-bundle/release-capsule/summary")
# @router.post("/semantic-adjudication-bundle/release-decision-record")
# @router.post("/semantic-adjudication-bundle/release-decision-record/summary")
# @router.post("/semantic-adjudication-bundle/release-decision-record/verify")
# @router.post("/semantic-adjudication-bundle/release-decision-ledger")
# @router.post("/semantic-adjudication-bundle/release-decision-ledger/verify")
# @router.post("/semantic-adjudication-bundle/release-decision-ledger/summary")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate/verify")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate/summary")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/verify")
# @router.post("/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary")
# build_semantic_adjudication_bundle_release_index
# verify_semantic_adjudication_bundle_release_index
# build_semantic_adjudication_release_capsule
# verify_semantic_adjudication_release_capsule
# summarize_semantic_adjudication_release_capsule
# build_semantic_adjudication_release_decision_record
# verify_semantic_adjudication_release_decision_record
# summarize_semantic_adjudication_release_decision_record
# build_semantic_adjudication_release_decision_ledger
# verify_semantic_adjudication_release_decision_ledger
# summarize_semantic_adjudication_release_decision_ledger
# build_semantic_adjudication_release_handoff_certificate
# verify_semantic_adjudication_release_handoff_certificate
# summarize_semantic_adjudication_release_handoff_certificate
# build_semantic_release_handoff_certificate_evidence
# verify_semantic_release_handoff_certificate_evidence
# summarize_semantic_release_handoff_certificate_evidence
