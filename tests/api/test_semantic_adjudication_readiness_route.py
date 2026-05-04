from __future__ import annotations

from strategy_validator.api.routes.research_bundle import (
    SemanticAdjudicationReadinessRequest,
    semantic_adjudication_readiness,
)
from strategy_validator.application.research_integrity import build_semantic_research_gate_artifact
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_readiness_route_accepts_verified_artifact() -> None:
    proposal = _verified_proposal()
    artifact = build_semantic_research_gate_artifact(proposal)

    payload = semantic_adjudication_readiness(
        SemanticAdjudicationReadinessRequest(
            proposal=proposal.model_dump(mode="json"),
            gate_artifact=artifact.model_dump(mode="json"),
            require_gate_artifact=True,
        )
    )

    assert payload["schema_version"] == "semantic_adjudication_readiness/v1"
    assert payload["ready_for_adjudication"] is True
    assert payload["gate_artifact_verified"] is True


def test_semantic_adjudication_readiness_route_blocks_missing_required_artifact() -> None:
    proposal = _verified_proposal()

    payload = semantic_adjudication_readiness(
        SemanticAdjudicationReadinessRequest(
            proposal=proposal.model_dump(mode="json"),
            require_gate_artifact=True,
        )
    )

    assert payload["ready_for_adjudication"] is False
    assert "SEMANTIC_GATE_ARTIFACT_REQUIRED" in payload["blocker_codes"]
