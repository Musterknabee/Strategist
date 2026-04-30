from __future__ import annotations

from strategy_validator.application.research_integrity import build_semantic_adjudication_bundle_release_preflight
from strategy_validator.contracts.semantic import SemanticAdjudicationBundle, SemanticAdjudicationBundleManifest


def test_release_preflight_requires_manifest_when_configured(valid_semantic_adjudication_bundle_payload):
    bundle = SemanticAdjudicationBundle.model_validate(valid_semantic_adjudication_bundle_payload)

    report = build_semantic_adjudication_bundle_release_preflight(bundle, require_manifest=True)

    assert report.ready_for_adjudication is False
    assert "SEMANTIC_BUNDLE_MANIFEST_REQUIRED" in report.blocker_codes
    assert report.recommended_action == "BLOCK_SEMANTIC_ADJUDICATION_RELEASE"


def test_release_preflight_accepts_verified_bundle_and_manifest(valid_semantic_adjudication_bundle_payload, valid_semantic_adjudication_bundle_manifest_payload):
    bundle = SemanticAdjudicationBundle.model_validate(valid_semantic_adjudication_bundle_payload)
    manifest = SemanticAdjudicationBundleManifest.model_validate(valid_semantic_adjudication_bundle_manifest_payload)

    report = build_semantic_adjudication_bundle_release_preflight(bundle, manifest=manifest, require_manifest=True)

    assert report.bundle_id == bundle.bundle_id
    assert report.manifest_id == manifest.manifest_id
    assert report.manifest_required is True
    assert isinstance(report.blocker_codes, list)
