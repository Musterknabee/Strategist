from __future__ import annotations

from strategy_validator.api.routes.research_bundle import (
    SemanticAdjudicationBundleRequest,
    SemanticAdjudicationBundleVerificationRequest,
    semantic_adjudication_bundle,
    semantic_adjudication_bundle_verify,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_bundle_route_builds_bundle() -> None:
    proposal = _verified_proposal()

    payload = semantic_adjudication_bundle(
        SemanticAdjudicationBundleRequest(
            proposal=proposal.model_dump(mode="json"),
            require_gate_artifact=True,
        )
    )

    assert payload["schema_version"] == "semantic_adjudication_bundle/v1"
    assert payload["handoff_artifact"]["schema_version"] == "semantic_adjudication_handoff_artifact/v1"
    assert payload["gate_artifact"]["schema_version"] == "semantic_research_gate_artifact/v1"


def test_semantic_adjudication_bundle_verify_route_accepts_bundle() -> None:
    proposal = _verified_proposal()
    bundle_payload = semantic_adjudication_bundle(
        SemanticAdjudicationBundleRequest(proposal=proposal.model_dump(mode="json"))
    )

    payload = semantic_adjudication_bundle_verify(
        SemanticAdjudicationBundleVerificationRequest(
            bundle=bundle_payload,
            proposal=proposal.model_dump(mode="json"),
        )
    )

    assert payload["schema_version"] == "semantic_adjudication_bundle_verification/v1"
    assert payload["verified"] is True
