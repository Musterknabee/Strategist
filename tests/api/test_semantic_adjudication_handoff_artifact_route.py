from __future__ import annotations

from strategy_validator.api.routes.research_bundle import (
    SemanticAdjudicationHandoffArtifactVerificationRequest,
    SemanticAdjudicationReadinessRequest,
    semantic_adjudication_handoff_artifact,
    semantic_adjudication_handoff_artifact_verify,
)
from strategy_validator.application.research_integrity import build_semantic_research_gate_artifact
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_handoff_artifact_route_builds_artifact() -> None:
    proposal = _verified_proposal()
    gate_artifact = build_semantic_research_gate_artifact(proposal)

    payload = semantic_adjudication_handoff_artifact(
        SemanticAdjudicationReadinessRequest(
            proposal=proposal.model_dump(mode="json"),
            gate_artifact=gate_artifact.model_dump(mode="json"),
            require_gate_artifact=True,
        )
    )

    assert payload["schema_version"] == "semantic_adjudication_handoff_artifact/v1"
    assert payload["readiness_report"]["ready_for_adjudication"] is True
    assert payload["gate_artifact"]["artifact_id"] == gate_artifact.artifact_id


def test_semantic_adjudication_handoff_artifact_verify_route_accepts_artifact() -> None:
    proposal = _verified_proposal()
    artifact_payload = semantic_adjudication_handoff_artifact(
        SemanticAdjudicationReadinessRequest(proposal=proposal.model_dump(mode="json"))
    )

    payload = semantic_adjudication_handoff_artifact_verify(
        SemanticAdjudicationHandoffArtifactVerificationRequest(
            artifact=artifact_payload,
            proposal=proposal.model_dump(mode="json"),
        )
    )

    assert payload["schema_version"] == "semantic_adjudication_handoff_artifact_verification/v1"
    assert payload["verified"] is True
