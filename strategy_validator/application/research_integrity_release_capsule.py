from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.application.research_integrity_release_index import (
    verify_semantic_adjudication_bundle_release_index,
)
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationBundleVerificationReport,
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseCapsuleIssue,
    SemanticAdjudicationReleaseCapsuleSummary,
    SemanticAdjudicationReleaseCapsuleVerificationReport,
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionRecordIssue,
    SemanticAdjudicationReleaseDecisionRecordSummary,
    SemanticAdjudicationReleaseDecisionRecordVerificationReport,
)


def _release_capsule_checksum_payload(capsule: SemanticAdjudicationReleaseCapsule) -> dict[str, Any]:
    payload = capsule.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def _release_decision_record_checksum_payload(record: SemanticAdjudicationReleaseDecisionRecord) -> dict[str, Any]:
    payload = record.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_adjudication_release_capsule(
    index: SemanticAdjudicationBundleReleaseIndex,
    *,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseCapsule:
    """Build the final checksummed release capsule for the semantic adjudication lane."""
    verification = verify_semantic_adjudication_bundle_release_index(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=require_manifest,
    )
    blocker_codes = [item.code for item in verification.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in verification.issues if item.severity != "BLOCKER"]
    ready = bool(verification.verified and index.release_preflight.ready_for_adjudication)
    if not index.release_preflight.ready_for_adjudication:
        blocker_codes = [*blocker_codes, *[code for code in index.release_preflight.blocker_codes if code not in blocker_codes]]
    base = SemanticAdjudicationReleaseCapsule(
        capsule_id="pending",
        index_id=index.index_id,
        bundle_id=index.bundle_id,
        experiment_id=index.experiment_id,
        proposal_digest=index.proposal_digest,
        index_payload_checksum=index.payload_checksum,
        release_preflight_recommended_action=index.release_preflight.recommended_action,
        ready_for_adjudication=ready,
        index_verification=verification,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_release_capsule_checksum_payload(base))
    with_id = base.model_copy(update={"capsule_id": f"semantic-release-capsule-{index.experiment_id}-{checksum[:16]}", "payload_checksum": checksum})
    final_checksum = _sha256_payload(_release_capsule_checksum_payload(with_id))
    return with_id.model_copy(update={"payload_checksum": final_checksum})


def verify_semantic_adjudication_release_capsule(
    capsule: SemanticAdjudicationReleaseCapsule,
    *,
    index: SemanticAdjudicationBundleReleaseIndex | None = None,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseCapsuleVerificationReport:
    """Verify a final release capsule against itself and optionally the source index chain."""
    issues: list[SemanticAdjudicationReleaseCapsuleIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationReleaseCapsuleIssue(code=code, message=message, severity=severity))

    observed_checksum = capsule.payload_checksum
    expected_checksum = _sha256_payload(_release_capsule_checksum_payload(capsule))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_CAPSULE_CHECKSUM_MISMATCH", "release capsule payload checksum does not match canonical payload")

    if capsule.schema_version != "semantic_adjudication_release_capsule/v1":
        issue("SEMANTIC_RELEASE_CAPSULE_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic release capsule schema version")

    embedded = capsule.index_verification
    if capsule.index_id != embedded.index_id:
        issue("SEMANTIC_RELEASE_CAPSULE_INDEX_ID_MISMATCH", "capsule index_id differs from embedded verification index_id")
    if capsule.bundle_id != embedded.bundle_id:
        issue("SEMANTIC_RELEASE_CAPSULE_BUNDLE_ID_MISMATCH", "capsule bundle_id differs from embedded verification bundle_id")
    if capsule.experiment_id != embedded.experiment_id:
        issue("SEMANTIC_RELEASE_CAPSULE_EXPERIMENT_MISMATCH", "capsule experiment_id differs from embedded verification experiment_id")
    if capsule.ready_for_adjudication and not embedded.verified:
        issue("SEMANTIC_RELEASE_CAPSULE_READY_WITH_FAILED_INDEX", "capsule is ready even though embedded index verification failed")

    if index is not None:
        expected_capsule = build_semantic_adjudication_release_capsule(
            index,
            bundle=bundle,
            manifest=manifest,
            proposal=proposal,
            require_manifest=require_manifest,
        )
        if capsule.index_id != index.index_id:
            issue("SEMANTIC_RELEASE_CAPSULE_INDEX_ID_DRIFT", "capsule index_id differs from supplied release index")
        if capsule.index_payload_checksum != index.payload_checksum:
            issue("SEMANTIC_RELEASE_CAPSULE_INDEX_CHECKSUM_DRIFT", "capsule index checksum differs from supplied release index")
        if capsule.proposal_digest != index.proposal_digest:
            issue("SEMANTIC_RELEASE_CAPSULE_PROPOSAL_DIGEST_DRIFT", "capsule proposal digest differs from supplied release index")
        if capsule.index_verification != expected_capsule.index_verification:
            issue("SEMANTIC_RELEASE_CAPSULE_INDEX_VERIFICATION_DRIFT", "capsule embedded index verification differs from recomputed verification")
        if capsule.ready_for_adjudication != expected_capsule.ready_for_adjudication:
            issue("SEMANTIC_RELEASE_CAPSULE_READINESS_DRIFT", "capsule readiness differs from recomputed release capsule")
        if capsule.blocker_codes != expected_capsule.blocker_codes:
            issue("SEMANTIC_RELEASE_CAPSULE_BLOCKER_DRIFT", "capsule blocker codes differ from recomputed release capsule")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationReleaseCapsuleVerificationReport(
        capsule_id=capsule.capsule_id,
        index_id=capsule.index_id,
        bundle_id=capsule.bundle_id,
        experiment_id=capsule.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_RELEASE_CAPSULE" if verified else "REBUILD_SEMANTIC_RELEASE_CAPSULE",
    )


def summarize_semantic_adjudication_release_capsule(
    capsule: SemanticAdjudicationReleaseCapsule,
    *,
    verification: SemanticAdjudicationReleaseCapsuleVerificationReport | None = None,
    index: SemanticAdjudicationBundleReleaseIndex | None = None,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseCapsuleSummary:
    """Build a compact operator/CI summary for a semantic release capsule."""
    report = verification or verify_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=require_manifest,
    )
    blocker_codes = list(dict.fromkeys([
        *capsule.blocker_codes,
        *[item.code for item in report.issues if item.severity == "BLOCKER"],
        *[code for code in capsule.index_verification.issue_codes if not capsule.index_verification.verified],
    ]))
    warning_codes = list(dict.fromkeys([
        *capsule.warning_codes,
        *[item.code for item in report.issues if item.severity != "BLOCKER"],
    ]))
    release_ready = bool(report.verified and capsule.index_verification.verified and capsule.ready_for_adjudication)
    if release_ready:
        recommended_action = "ACCEPT_SEMANTIC_RELEASE_CAPSULE_FOR_ADJUDICATION"
    elif report.verified and not capsule.ready_for_adjudication:
        recommended_action = "BLOCK_ADJUDICATION_UNTIL_PREFLIGHT_READY"
    else:
        recommended_action = "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_CAPSULE"
    return SemanticAdjudicationReleaseCapsuleSummary(
        capsule_id=capsule.capsule_id,
        index_id=capsule.index_id,
        bundle_id=capsule.bundle_id,
        experiment_id=capsule.experiment_id,
        capsule_verified=report.verified,
        embedded_index_verified=capsule.index_verification.verified,
        ready_for_adjudication=release_ready,
        release_preflight_recommended_action=capsule.release_preflight_recommended_action,
        recommended_action=recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        capsule_issue_codes=report.issue_codes,
        index_issue_codes=capsule.index_verification.issue_codes,
        index_payload_checksum=capsule.index_payload_checksum,
        capsule_payload_checksum=capsule.payload_checksum,
        issue_count=len(blocker_codes) + len(warning_codes),
    )


def build_semantic_adjudication_release_decision_record(
    capsule: SemanticAdjudicationReleaseCapsule,
    *,
    decision: str | None = None,
    decided_by: str = "operator",
    decision_reason: str | None = None,
    verification: SemanticAdjudicationReleaseCapsuleVerificationReport | None = None,
    index: SemanticAdjudicationBundleReleaseIndex | None = None,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseDecisionRecord:
    """Build the terminal operator/CI decision record over a release capsule.

    The record is checksummed and deliberately separate from adjudication; it is
    a portable handoff receipt proving which capsule summary was accepted or
    blocked before the proposal enters the validator authority path.
    """
    summary = summarize_semantic_adjudication_release_capsule(
        capsule,
        verification=verification,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=require_manifest,
    )
    normalized_decision = decision or (
        "ACCEPT_FOR_ADJUDICATION" if summary.ready_for_adjudication else "BLOCK_ADJUDICATION"
    )
    allowed = bool(summary.ready_for_adjudication and normalized_decision == "ACCEPT_FOR_ADJUDICATION")
    if normalized_decision == "ACCEPT_FOR_ADJUDICATION" and not summary.ready_for_adjudication:
        blocker_codes = list(dict.fromkeys([*summary.blocker_codes, "SEMANTIC_RELEASE_DECISION_ACCEPTED_UNREADY_CAPSULE"]))
    else:
        blocker_codes = list(summary.blocker_codes)
    base = SemanticAdjudicationReleaseDecisionRecord(
        decision_id="pending",
        capsule_id=capsule.capsule_id,
        index_id=capsule.index_id,
        bundle_id=capsule.bundle_id,
        experiment_id=capsule.experiment_id,
        proposal_digest=capsule.proposal_digest,
        capsule_payload_checksum=capsule.payload_checksum,
        capsule_summary=summary,
        decision=normalized_decision,
        decision_allowed=allowed,
        decided_by=decided_by,
        decision_reason=decision_reason,
        blocker_codes=blocker_codes,
        warning_codes=summary.warning_codes,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_release_decision_record_checksum_payload(base))
    with_id = base.model_copy(update={
        "decision_id": f"semantic-release-decision-{capsule.experiment_id}-{checksum[:16]}",
        "payload_checksum": checksum,
    })
    final_checksum = _sha256_payload(_release_decision_record_checksum_payload(with_id))
    return with_id.model_copy(update={"payload_checksum": final_checksum})


def verify_semantic_adjudication_release_decision_record(
    record: SemanticAdjudicationReleaseDecisionRecord,
    *,
    capsule: SemanticAdjudicationReleaseCapsule | None = None,
    index: SemanticAdjudicationBundleReleaseIndex | None = None,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseDecisionRecordVerificationReport:
    """Verify a terminal release decision record and optionally replay its capsule chain."""
    issues: list[SemanticAdjudicationReleaseDecisionRecordIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationReleaseDecisionRecordIssue(code=code, message=message, severity=severity))

    observed_checksum = record.payload_checksum
    expected_checksum = _sha256_payload(_release_decision_record_checksum_payload(record))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_DECISION_RECORD_CHECKSUM_MISMATCH", "release decision record payload checksum does not match canonical payload")

    if record.schema_version != "semantic_adjudication_release_decision_record/v1":
        issue("SEMANTIC_RELEASE_DECISION_RECORD_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic release decision record schema version")

    if record.decision == "ACCEPT_FOR_ADJUDICATION" and not record.decision_allowed:
        issue("SEMANTIC_RELEASE_DECISION_ACCEPT_NOT_ALLOWED", "decision accepts adjudication even though decision_allowed is false")
    if record.decision_allowed and not record.capsule_summary.ready_for_adjudication:
        issue("SEMANTIC_RELEASE_DECISION_ALLOWED_UNREADY_CAPSULE", "decision_allowed is true for an unready capsule summary")
    if record.capsule_id != record.capsule_summary.capsule_id:
        issue("SEMANTIC_RELEASE_DECISION_CAPSULE_ID_MISMATCH", "record capsule_id differs from capsule summary")
    if record.index_id != record.capsule_summary.index_id:
        issue("SEMANTIC_RELEASE_DECISION_INDEX_ID_MISMATCH", "record index_id differs from capsule summary")
    if record.bundle_id != record.capsule_summary.bundle_id:
        issue("SEMANTIC_RELEASE_DECISION_BUNDLE_ID_MISMATCH", "record bundle_id differs from capsule summary")
    if record.experiment_id != record.capsule_summary.experiment_id:
        issue("SEMANTIC_RELEASE_DECISION_EXPERIMENT_MISMATCH", "record experiment_id differs from capsule summary")
    if record.capsule_payload_checksum != record.capsule_summary.capsule_payload_checksum:
        issue("SEMANTIC_RELEASE_DECISION_CAPSULE_CHECKSUM_MISMATCH", "record capsule checksum differs from capsule summary")

    if capsule is not None:
        expected_record = build_semantic_adjudication_release_decision_record(
            capsule,
            decision=record.decision,
            decided_by=record.decided_by,
            decision_reason=record.decision_reason,
            index=index,
            bundle=bundle,
            manifest=manifest,
            proposal=proposal,
            require_manifest=require_manifest,
        )
        if record.capsule_id != capsule.capsule_id:
            issue("SEMANTIC_RELEASE_DECISION_CAPSULE_ID_DRIFT", "record capsule_id differs from supplied capsule")
        if record.capsule_payload_checksum != capsule.payload_checksum:
            issue("SEMANTIC_RELEASE_DECISION_CAPSULE_PAYLOAD_DRIFT", "record capsule checksum differs from supplied capsule")
        if record.proposal_digest != capsule.proposal_digest:
            issue("SEMANTIC_RELEASE_DECISION_PROPOSAL_DIGEST_DRIFT", "record proposal digest differs from supplied capsule")
        if record.capsule_summary != expected_record.capsule_summary:
            issue("SEMANTIC_RELEASE_DECISION_SUMMARY_DRIFT", "record capsule summary differs from recomputed capsule summary")
        if record.decision_allowed != expected_record.decision_allowed:
            issue("SEMANTIC_RELEASE_DECISION_ALLOWED_DRIFT", "record decision_allowed differs from recomputed decision allowance")
        if record.blocker_codes != expected_record.blocker_codes:
            issue("SEMANTIC_RELEASE_DECISION_BLOCKER_DRIFT", "record blocker codes differ from recomputed decision record")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationReleaseDecisionRecordVerificationReport(
        decision_id=record.decision_id,
        capsule_id=record.capsule_id,
        experiment_id=record.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_RELEASE_DECISION_RECORD" if verified else "REBUILD_SEMANTIC_RELEASE_DECISION_RECORD",
    )


def summarize_semantic_adjudication_release_decision_record(
    record: SemanticAdjudicationReleaseDecisionRecord,
    *,
    verification: SemanticAdjudicationReleaseDecisionRecordVerificationReport | None = None,
    capsule: SemanticAdjudicationReleaseCapsule | None = None,
    index: SemanticAdjudicationBundleReleaseIndex | None = None,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationReleaseDecisionRecordSummary:
    """Build a compact terminal summary for a semantic release decision record.

    This is the CI/operator status object that should be used by release
    scripts when deciding whether the sealed semantic chain may be handed to
    the validator authority path.
    """
    report = verification or verify_semantic_adjudication_release_decision_record(
        record,
        capsule=capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=require_manifest,
    )
    blocker_codes = list(dict.fromkeys([
        *record.blocker_codes,
        *[item.code for item in report.issues if item.severity == "BLOCKER"],
    ]))
    warning_codes = list(dict.fromkeys([
        *record.warning_codes,
        *[item.code for item in report.issues if item.severity != "BLOCKER"],
    ]))
    accepted = bool(
        report.verified
        and record.decision_allowed
        and record.decision == "ACCEPT_FOR_ADJUDICATION"
        and record.capsule_summary.ready_for_adjudication
    )
    if accepted:
        recommended_action = "HAND_OFF_TO_VALIDATOR_ADJUDICATION"
    elif report.verified and record.decision == "BLOCK_ADJUDICATION":
        recommended_action = "RESPECT_RECORDED_BLOCK_DECISION"
    else:
        recommended_action = "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_DECISION_RECORD"
    return SemanticAdjudicationReleaseDecisionRecordSummary(
        decision_id=record.decision_id,
        capsule_id=record.capsule_id,
        index_id=record.index_id,
        bundle_id=record.bundle_id,
        experiment_id=record.experiment_id,
        decision=record.decision,
        decision_allowed=record.decision_allowed,
        record_verified=report.verified,
        capsule_ready_for_adjudication=record.capsule_summary.ready_for_adjudication,
        capsule_summary_recommended_action=record.capsule_summary.recommended_action,
        recommended_action=recommended_action,
        decided_by=record.decided_by,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        record_issue_codes=report.issue_codes,
        capsule_payload_checksum=record.capsule_payload_checksum,
        decision_payload_checksum=record.payload_checksum,
        issue_count=len(blocker_codes) + len(warning_codes),
    )
