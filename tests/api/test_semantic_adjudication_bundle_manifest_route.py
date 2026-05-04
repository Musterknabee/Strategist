from __future__ import annotations

from strategy_validator.api.routes.research_bundle import (
    SemanticAdjudicationBundleRequest,
    semantic_adjudication_bundle,
)
from strategy_validator.api.routes.research_release import (
    SemanticAdjudicationBundleManifestRequest,
    SemanticAdjudicationBundleManifestVerificationRequest,
    SemanticAdjudicationBundleVerificationRequest,
    semantic_adjudication_bundle_manifest,
    semantic_adjudication_bundle_manifest_verify,
    semantic_adjudication_bundle_summary,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_bundle_summary_route() -> None:
    proposal = _verified_proposal()
    bundle = semantic_adjudication_bundle(SemanticAdjudicationBundleRequest(proposal=proposal.model_dump(mode="json")))

    payload = semantic_adjudication_bundle_summary(
        SemanticAdjudicationBundleVerificationRequest(bundle=bundle, proposal=proposal.model_dump(mode="json"))
    )

    assert payload["schema_version"] == "semantic_adjudication_bundle_summary/v1"
    assert payload["ready_for_adjudication"] is True


def test_semantic_adjudication_bundle_manifest_route_and_verify() -> None:
    proposal = _verified_proposal()
    bundle = semantic_adjudication_bundle(SemanticAdjudicationBundleRequest(proposal=proposal.model_dump(mode="json")))
    manifest = semantic_adjudication_bundle_manifest(
        SemanticAdjudicationBundleManifestRequest(bundle=bundle, proposal=proposal.model_dump(mode="json"))
    )

    report = semantic_adjudication_bundle_manifest_verify(
        SemanticAdjudicationBundleManifestVerificationRequest(
            manifest=manifest,
            bundle=bundle,
            proposal=proposal.model_dump(mode="json"),
        )
    )

    assert manifest["schema_version"] == "semantic_adjudication_bundle_manifest/v1"
    assert report["verified"] is True
