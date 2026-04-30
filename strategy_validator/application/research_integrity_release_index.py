from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.application.research_integrity_bundle import (
    summarize_semantic_adjudication_bundle,
    verify_semantic_adjudication_bundle,
)
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleManifestIssue,
    SemanticAdjudicationBundleManifestVerificationReport,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationBundleReleaseIndexIssue,
    SemanticAdjudicationBundleReleaseIndexVerificationReport,
    SemanticAdjudicationBundleReleasePreflightReport,
)


def _bundle_manifest_payload(manifest: SemanticAdjudicationBundleManifest) -> dict[str, Any]:
    payload = manifest.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def _bundle_manifest_checksum(manifest: SemanticAdjudicationBundleManifest) -> str:
    return _sha256_payload(_bundle_manifest_payload(manifest))


def build_semantic_adjudication_bundle_manifest(
    bundle: SemanticAdjudicationBundle,
    *,
    proposal: ExperimentManifest | None = None,
) -> SemanticAdjudicationBundleManifest:
    """Build a portable manifest that can be archived with a semantic bundle."""
    summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)
    gate = bundle.gate_artifact
    handoff = bundle.handoff_artifact
    seed = {
        "schema_version": "semantic_adjudication_bundle_manifest/v1",
        "bundle_id": bundle.bundle_id,
        "experiment_id": bundle.experiment_id,
        "bundle_payload_checksum": bundle.payload_checksum,
        "handoff_artifact_id": handoff.artifact_id,
    }
    manifest = SemanticAdjudicationBundleManifest(
        manifest_id=f"semantic-bundle-manifest-{bundle.experiment_id}-{_sha256_payload(seed)[:16]}",
        bundle_id=bundle.bundle_id,
        experiment_id=bundle.experiment_id,
        proposal_digest=bundle.proposal_digest,
        bundle_payload_checksum=bundle.payload_checksum,
        gate_artifact_id=None if gate is None else gate.artifact_id,
        gate_artifact_checksum=None if gate is None else gate.payload_checksum,
        handoff_artifact_id=handoff.artifact_id,
        handoff_artifact_checksum=handoff.payload_checksum,
        semantic_evidence_checksums=list(bundle.semantic_evidence_checksums),
        data_spine_fingerprint=bundle.data_spine_fingerprint,
        summary=summary,
        payload_checksum="pending",
    )
    return manifest.model_copy(update={"payload_checksum": _bundle_manifest_checksum(manifest)})


def verify_semantic_adjudication_bundle_manifest(
    manifest: SemanticAdjudicationBundleManifest,
    *,
    bundle: SemanticAdjudicationBundle | None = None,
    proposal: ExperimentManifest | None = None,
) -> SemanticAdjudicationBundleManifestVerificationReport:
    """Verify a bundle manifest against itself and optionally the supplied bundle/proposal."""
    issues: list[SemanticAdjudicationBundleManifestIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationBundleManifestIssue(code=code, message=message, severity=severity))

    observed_checksum = manifest.payload_checksum
    expected_checksum = _bundle_manifest_checksum(manifest)
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_BUNDLE_MANIFEST_CHECKSUM_MISMATCH", "manifest payload checksum does not match canonical payload")
    if manifest.schema_version != "semantic_adjudication_bundle_manifest/v1":
        issue("SEMANTIC_BUNDLE_MANIFEST_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic adjudication bundle manifest schema version")
    if manifest.experiment_id != manifest.summary.experiment_id:
        issue("SEMANTIC_BUNDLE_MANIFEST_EXPERIMENT_MISMATCH", "manifest experiment_id differs from summary experiment_id")
    if manifest.bundle_id != manifest.summary.bundle_id:
        issue("SEMANTIC_BUNDLE_MANIFEST_SUMMARY_BUNDLE_MISMATCH", "manifest bundle_id differs from summary bundle_id")

    if bundle is not None:
        expected_manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
        if manifest.bundle_id != bundle.bundle_id:
            issue("SEMANTIC_BUNDLE_MANIFEST_BUNDLE_ID_MISMATCH", "manifest bundle_id differs from supplied bundle")
        if manifest.bundle_payload_checksum != bundle.payload_checksum:
            issue("SEMANTIC_BUNDLE_MANIFEST_BUNDLE_CHECKSUM_MISMATCH", "manifest bundle checksum differs from supplied bundle")
        if manifest.proposal_digest != bundle.proposal_digest:
            issue("SEMANTIC_BUNDLE_MANIFEST_PROPOSAL_DIGEST_MISMATCH", "manifest proposal digest differs from supplied bundle")
        if manifest.gate_artifact_id != expected_manifest.gate_artifact_id:
            issue("SEMANTIC_BUNDLE_MANIFEST_GATE_ID_DRIFT", "manifest gate artifact id differs from supplied bundle")
        if manifest.gate_artifact_checksum != expected_manifest.gate_artifact_checksum:
            issue("SEMANTIC_BUNDLE_MANIFEST_GATE_CHECKSUM_DRIFT", "manifest gate artifact checksum differs from supplied bundle")
        if manifest.handoff_artifact_id != expected_manifest.handoff_artifact_id:
            issue("SEMANTIC_BUNDLE_MANIFEST_HANDOFF_ID_DRIFT", "manifest handoff artifact id differs from supplied bundle")
        if manifest.handoff_artifact_checksum != expected_manifest.handoff_artifact_checksum:
            issue("SEMANTIC_BUNDLE_MANIFEST_HANDOFF_CHECKSUM_DRIFT", "manifest handoff artifact checksum differs from supplied bundle")
        if manifest.semantic_evidence_checksums != expected_manifest.semantic_evidence_checksums:
            issue("SEMANTIC_BUNDLE_MANIFEST_EVIDENCE_CHECKSUM_DRIFT", "manifest semantic evidence checksums differ from supplied bundle")
        if manifest.data_spine_fingerprint != expected_manifest.data_spine_fingerprint:
            issue("SEMANTIC_BUNDLE_MANIFEST_DATA_SPINE_DRIFT", "manifest Data Spine fingerprint differs from supplied bundle")
        if manifest.summary != expected_manifest.summary:
            issue("SEMANTIC_BUNDLE_MANIFEST_SUMMARY_DRIFT", "manifest summary differs from recomputed bundle summary")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationBundleManifestVerificationReport(
        manifest_id=manifest.manifest_id,
        bundle_id=manifest.bundle_id,
        experiment_id=manifest.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_ADJUDICATION_BUNDLE_MANIFEST" if verified else "REBUILD_SEMANTIC_ADJUDICATION_BUNDLE_MANIFEST",
    )


def build_semantic_adjudication_bundle_release_preflight(
    bundle: SemanticAdjudicationBundle,
    *,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationBundleReleasePreflightReport:
    """Verify the complete semantic adjudication bundle release handoff.

    This is the final read-only operator/CI preflight before handing a semantic
    research lane to adjudication. It intentionally composes the lower-level
    bundle verifier, optional portable-manifest verifier, and compact bundle
    summary so the CLI/API can expose one stable release decision object.
    """
    bundle_report = verify_semantic_adjudication_bundle(bundle, proposal=proposal)
    summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)

    blocker_codes = list(dict.fromkeys(summary.blocker_codes + [
        code for code in bundle_report.issue_codes
        if code not in summary.blocker_codes
    ]))
    warning_codes = list(summary.warning_codes)
    manifest_issue_codes: list[str] = []
    manifest_verified = False
    manifest_payload_checksum: str | None = None
    manifest_id: str | None = None

    if manifest is None:
        if require_manifest:
            blocker_codes.append("SEMANTIC_BUNDLE_MANIFEST_REQUIRED")
    else:
        manifest_id = manifest.manifest_id
        manifest_payload_checksum = manifest.payload_checksum
        manifest_report = verify_semantic_adjudication_bundle_manifest(
            manifest,
            bundle=bundle,
            proposal=proposal,
        )
        manifest_verified = manifest_report.verified
        manifest_issue_codes = list(manifest_report.issue_codes)
        for item in manifest_report.issues:
            target = blocker_codes if item.severity == "BLOCKER" else warning_codes
            if item.code not in target:
                target.append(item.code)

    blocker_codes = list(dict.fromkeys(blocker_codes))
    warning_codes = [code for code in dict.fromkeys(warning_codes) if code not in blocker_codes]
    ready = (
        bundle_report.verified
        and summary.ready_for_adjudication
        and (manifest_verified or (manifest is None and not require_manifest))
        and not blocker_codes
    )
    return SemanticAdjudicationBundleReleasePreflightReport(
        bundle_id=bundle.bundle_id,
        experiment_id=bundle.experiment_id,
        proposal_digest=bundle.proposal_digest,
        manifest_id=manifest_id,
        bundle_verified=bundle_report.verified,
        manifest_required=require_manifest,
        manifest_verified=manifest_verified,
        ready_for_adjudication=ready,
        recommended_action="HAND_TO_ADJUDICATOR" if ready else "BLOCK_SEMANTIC_ADJUDICATION_RELEASE",
        bundle_payload_checksum=bundle.payload_checksum,
        manifest_payload_checksum=manifest_payload_checksum,
        semantic_evidence_count=len(bundle.semantic_evidence_checksums),
        data_spine_fingerprint_present=bundle.data_spine_fingerprint is not None,
        gate_artifact_present=bundle.gate_artifact is not None,
        handoff_artifact_present=bundle.handoff_artifact is not None,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        bundle_issue_codes=list(bundle_report.issue_codes),
        manifest_issue_codes=manifest_issue_codes,
        issue_count=len(blocker_codes) + len(warning_codes),
    )


def _bundle_release_index_checksum_payload(index: SemanticAdjudicationBundleReleaseIndex) -> dict[str, Any]:
    payload = index.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_adjudication_bundle_release_index(
    bundle: SemanticAdjudicationBundle,
    *,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationBundleReleaseIndex:
    """Build a compact release index for semantic adjudication handoff artifacts.

    The index is the operator/CI object that points at the sealed bundle and its
    manifest while repeating the final release preflight decision. It is safe to
    archive next to release artifacts because it contains checksums and ids, not
    the full proposal payload.
    """
    preflight = build_semantic_adjudication_bundle_release_preflight(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=require_manifest,
    )
    gate = bundle.gate_artifact
    handoff = bundle.handoff_artifact
    base = SemanticAdjudicationBundleReleaseIndex(
        index_id="pending",
        bundle_id=bundle.bundle_id,
        experiment_id=bundle.experiment_id,
        proposal_digest=bundle.proposal_digest,
        bundle_payload_checksum=bundle.payload_checksum,
        manifest_id=None if manifest is None else manifest.manifest_id,
        manifest_payload_checksum=None if manifest is None else manifest.payload_checksum,
        gate_artifact_id=None if gate is None else gate.artifact_id,
        gate_artifact_checksum=None if gate is None else gate.payload_checksum,
        handoff_artifact_id=handoff.artifact_id,
        handoff_artifact_checksum=handoff.payload_checksum,
        semantic_evidence_checksums=list(bundle.semantic_evidence_checksums),
        data_spine_fingerprint=bundle.data_spine_fingerprint,
        release_preflight=preflight,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_bundle_release_index_checksum_payload(base))
    indexed = base.model_copy(update={"index_id": f"semantic-release-index-{bundle.experiment_id}-{checksum[:16]}", "payload_checksum": checksum})
    final_checksum = _sha256_payload(_bundle_release_index_checksum_payload(indexed))
    return indexed.model_copy(update={"payload_checksum": final_checksum})


def verify_semantic_adjudication_bundle_release_index(
    index: SemanticAdjudicationBundleReleaseIndex,
    *,
    bundle: SemanticAdjudicationBundle | None = None,
    manifest: SemanticAdjudicationBundleManifest | None = None,
    proposal: ExperimentManifest | None = None,
    require_manifest: bool = True,
) -> SemanticAdjudicationBundleReleaseIndexVerificationReport:
    """Verify a release index against itself and optionally the source artifacts."""
    issues: list[SemanticAdjudicationBundleReleaseIndexIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationBundleReleaseIndexIssue(code=code, message=message, severity=severity))

    observed_checksum = index.payload_checksum
    expected_checksum = _sha256_payload(_bundle_release_index_checksum_payload(index))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_INDEX_CHECKSUM_MISMATCH", "release index payload checksum does not match canonical payload")

    if index.schema_version != "semantic_adjudication_bundle_release_index/v1":
        issue("SEMANTIC_RELEASE_INDEX_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic release index schema version")

    if index.experiment_id != index.release_preflight.experiment_id:
        issue("SEMANTIC_RELEASE_INDEX_EXPERIMENT_MISMATCH", "index experiment_id differs from embedded release preflight experiment_id")
    if index.bundle_id != index.release_preflight.bundle_id:
        issue("SEMANTIC_RELEASE_INDEX_BUNDLE_ID_MISMATCH", "index bundle_id differs from embedded release preflight bundle_id")
    if index.proposal_digest != index.release_preflight.proposal_digest:
        issue("SEMANTIC_RELEASE_INDEX_PROPOSAL_DIGEST_MISMATCH", "index proposal digest differs from embedded release preflight proposal digest")
    if index.bundle_payload_checksum != index.release_preflight.bundle_payload_checksum:
        issue("SEMANTIC_RELEASE_INDEX_BUNDLE_CHECKSUM_MISMATCH", "index bundle checksum differs from embedded release preflight bundle checksum")
    if index.manifest_payload_checksum != index.release_preflight.manifest_payload_checksum:
        issue("SEMANTIC_RELEASE_INDEX_MANIFEST_CHECKSUM_MISMATCH", "index manifest checksum differs from embedded release preflight manifest checksum")

    if bundle is not None:
        expected_index = build_semantic_adjudication_bundle_release_index(
            bundle,
            manifest=manifest,
            proposal=proposal,
            require_manifest=require_manifest,
        )
        if index.bundle_id != bundle.bundle_id:
            issue("SEMANTIC_RELEASE_INDEX_BUNDLE_ID_DRIFT", "index bundle_id differs from supplied bundle")
        if index.bundle_payload_checksum != bundle.payload_checksum:
            issue("SEMANTIC_RELEASE_INDEX_BUNDLE_PAYLOAD_DRIFT", "index bundle payload checksum differs from supplied bundle")
        if index.proposal_digest != bundle.proposal_digest:
            issue("SEMANTIC_RELEASE_INDEX_PROPOSAL_DIGEST_DRIFT", "index proposal digest differs from supplied bundle")
        if index.semantic_evidence_checksums != list(bundle.semantic_evidence_checksums):
            issue("SEMANTIC_RELEASE_INDEX_EVIDENCE_CHECKSUM_DRIFT", "index semantic evidence checksums differ from supplied bundle")
        if index.data_spine_fingerprint != bundle.data_spine_fingerprint:
            issue("SEMANTIC_RELEASE_INDEX_DATA_SPINE_DRIFT", "index Data Spine fingerprint differs from supplied bundle")
        if index.release_preflight != expected_index.release_preflight:
            issue("SEMANTIC_RELEASE_INDEX_PREFLIGHT_DRIFT", "index release preflight differs from recomputed preflight")
        if index.gate_artifact_id != expected_index.gate_artifact_id or index.gate_artifact_checksum != expected_index.gate_artifact_checksum:
            issue("SEMANTIC_RELEASE_INDEX_GATE_ARTIFACT_DRIFT", "index gate artifact reference differs from supplied bundle")
        if index.handoff_artifact_id != expected_index.handoff_artifact_id or index.handoff_artifact_checksum != expected_index.handoff_artifact_checksum:
            issue("SEMANTIC_RELEASE_INDEX_HANDOFF_ARTIFACT_DRIFT", "index handoff artifact reference differs from supplied bundle")

    if manifest is not None:
        if index.manifest_id != manifest.manifest_id:
            issue("SEMANTIC_RELEASE_INDEX_MANIFEST_ID_DRIFT", "index manifest_id differs from supplied manifest")
        if index.manifest_payload_checksum != manifest.payload_checksum:
            issue("SEMANTIC_RELEASE_INDEX_MANIFEST_PAYLOAD_DRIFT", "index manifest payload checksum differs from supplied manifest")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationBundleReleaseIndexVerificationReport(
        index_id=index.index_id,
        bundle_id=index.bundle_id,
        experiment_id=index.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_RELEASE_INDEX" if verified else "REBUILD_SEMANTIC_RELEASE_INDEX",
    )


__all__ = [
    "build_semantic_adjudication_bundle_manifest",
    "verify_semantic_adjudication_bundle_manifest",
    "build_semantic_adjudication_bundle_release_preflight",
    "build_semantic_adjudication_bundle_release_index",
    "verify_semantic_adjudication_bundle_release_index",
]
