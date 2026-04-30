from __future__ import annotations

from strategy_validator.api.routes.research import (
    SemanticResearchGateArtifactVerificationRequest,
    SemanticResearchIntegrityRequest,
    semantic_research_adjudication_gate_artifact,
    semantic_research_adjudication_gate_artifact_verify,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_gate_artifact_route_builds_artifact() -> None:
    proposal = _verified_proposal()

    payload = semantic_research_adjudication_gate_artifact(
        SemanticResearchIntegrityRequest(proposal=proposal.model_dump(mode="json"))
    )

    assert payload["schema_version"] == "semantic_research_gate_artifact/v1"
    assert payload["summary"]["gate_passed"] is True
    assert payload["payload_checksum"]


def test_semantic_gate_artifact_verify_route_accepts_matching_proposal() -> None:
    proposal = _verified_proposal()
    artifact = semantic_research_adjudication_gate_artifact(
        SemanticResearchIntegrityRequest(proposal=proposal.model_dump(mode="json"))
    )

    report = semantic_research_adjudication_gate_artifact_verify(
        SemanticResearchGateArtifactVerificationRequest(
            artifact=artifact,
            proposal=proposal.model_dump(mode="json"),
        )
    )

    assert report["schema_version"] == "semantic_research_gate_artifact_verification/v1"
    assert report["verified"] is True
