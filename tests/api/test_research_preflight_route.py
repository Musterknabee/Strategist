from __future__ import annotations

from strategy_validator.api.routes.research import SemanticResearchPreflightRequest, semantic_research_preflight


def test_research_preflight_route_uses_application_surface(monkeypatch) -> None:
    observed = {}

    def fake_run(proposal, artifact, **kwargs):
        observed["proposal"] = proposal.experiment_id
        observed["artifact"] = artifact.event_id
        observed["kwargs"] = kwargs

        class Report:
            def model_dump(self, *, mode):
                return {
                    "schema_version": "semantic_research_preflight/v1",
                    "evidence_verified": True,
                    "recommended_action": "ATTACH_TO_ADJUDICATION_EVIDENCE",
                }

        return Report()

    monkeypatch.setattr("strategy_validator.api.routes.research.run_semantic_research_preflight", fake_run)
    request = SemanticResearchPreflightRequest(
        proposal={
            "experiment_id": "EXP-ROUTE-001",
            "strategy_name": "RouteAlpha",
            "version": "0.1",
            "proposer_id": "test",
            "state": "INVALID",
            "evidence_bundle": {
                "reproducibility": {
                    "code_hash": "12345678",
                    "data_snapshot_hash": "12345678",
                    "universe_hash": "12345678",
                    "feature_graph_hash": "12345678",
                    "parameter_manifest_hash": "12345678",
                    "benchmark_version": "bench-v1",
                    "cost_model_version": "cost-v1",
                    "calendar_version": "cal-v1",
                },
                "benchmark_rung": "paper",
                "search_breadth": 1,
            },
        },
        artifact={
            "event_id": "event-route-001",
            "forensic_status": "adjudicated",
            "novelty_score": 0.5,
            "polarity_score": 0.1,
            "belief_conflict": 0.2,
            "evidence_density": 0.9,
        },
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
        attach_to_proposal=False,
    )

    payload = semantic_research_preflight(request)

    assert payload["schema_version"] == "semantic_research_preflight/v1"
    assert observed["proposal"] == "EXP-ROUTE-001"
    assert observed["artifact"] == "event-route-001"
    assert observed["kwargs"]["attach_to_proposal"] is False


def test_research_integrity_route_uses_application_surface(monkeypatch) -> None:
    from strategy_validator.api.routes.research import SemanticResearchIntegrityRequest, semantic_research_integrity

    observed = {}

    def fake_verify(proposal, **kwargs):
        observed["proposal"] = proposal.experiment_id
        observed["kwargs"] = kwargs

        class Report:
            def model_dump(self, *, mode):
                return {
                    "schema_version": "semantic_research_integrity/v1",
                    "verified": True,
                    "recommended_action": "READY_FOR_ADJUDICATION_PREFLIGHT",
                }

        return Report()

    monkeypatch.setattr("strategy_validator.api.routes.research.verify_proposal_semantic_research_integrity", fake_verify)
    request = SemanticResearchIntegrityRequest(
        proposal={
            "experiment_id": "EXP-INTEGRITY-ROUTE-001",
            "strategy_name": "IntegrityRouteAlpha",
            "version": "0.1",
            "proposer_id": "test",
            "state": "INVALID",
            "evidence_bundle": {
                "reproducibility": {
                    "code_hash": "12345678",
                    "data_snapshot_hash": "12345678",
                    "universe_hash": "12345678",
                    "feature_graph_hash": "12345678",
                    "parameter_manifest_hash": "12345678",
                    "benchmark_version": "bench-v1",
                    "cost_model_version": "cost-v1",
                    "calendar_version": "cal-v1",
                },
                "benchmark_rung": "paper",
                "search_breadth": 1,
            },
        },
        require_semantic_evidence=False,
    )

    payload = semantic_research_integrity(request)

    assert payload["schema_version"] == "semantic_research_integrity/v1"
    assert observed["proposal"] == "EXP-INTEGRITY-ROUTE-001"
    assert observed["kwargs"]["require_semantic_evidence"] is False


def test_research_integrity_summary_route_is_compact(monkeypatch) -> None:
    from strategy_validator.api.routes.research import SemanticResearchIntegrityRequest, semantic_research_integrity_summary

    class Report:
        experiment_id = "EXP-INTEGRITY-SUMMARY-ROUTE-001"
        verified = True
        recommended_action = "READY_FOR_ADJUDICATION_PREFLIGHT"
        semantic_evidence_count = 1
        data_spine_seal_present = True
        issue_count = 0
        issues = []

    def fake_verify(proposal, **kwargs):
        return Report()

    monkeypatch.setattr("strategy_validator.api.routes.research.verify_proposal_semantic_research_integrity", fake_verify)
    request = SemanticResearchIntegrityRequest(
        proposal={
            "experiment_id": "EXP-INTEGRITY-SUMMARY-ROUTE-001",
            "strategy_name": "IntegritySummaryRouteAlpha",
            "version": "0.1",
            "proposer_id": "test",
            "state": "INVALID",
            "evidence_bundle": {
                "reproducibility": {
                    "code_hash": "12345678",
                    "data_snapshot_hash": "12345678",
                    "universe_hash": "12345678",
                    "feature_graph_hash": "12345678",
                    "parameter_manifest_hash": "12345678",
                    "benchmark_version": "bench-v1",
                    "cost_model_version": "cost-v1",
                    "calendar_version": "cal-v1",
                },
                "benchmark_rung": "paper",
                "search_breadth": 1,
            },
        },
        require_semantic_evidence=False,
    )

    payload = semantic_research_integrity_summary(request)

    assert payload["schema_version"] == "semantic_research_integrity_summary/v1"
    assert payload["verified"] is True
    assert "issues" not in payload


def test_research_adjudication_gate_summary_route_is_operator_compact(monkeypatch) -> None:
    from strategy_validator.api.routes.research import (
        SemanticResearchIntegrityRequest,
        semantic_research_adjudication_gate_summary,
    )

    class Summary:
        def model_dump(self, *, mode):
            return {
                "schema_version": "semantic_research_adjudication_gate_summary/v1",
                "experiment_id": "EXP-GATE-SUMMARY-ROUTE-001",
                "gate_passed": True,
                "recommended_action": "ALLOW_ADJUDICATION",
                "blocker_codes": [],
            }

    def fake_summary(proposal, **kwargs):
        assert proposal.experiment_id == "EXP-GATE-SUMMARY-ROUTE-001"
        assert kwargs["require_semantic_evidence"] is False
        return Summary()

    monkeypatch.setattr(
        "strategy_validator.api.routes.research.build_semantic_research_adjudication_gate_summary",
        fake_summary,
    )
    request = SemanticResearchIntegrityRequest(
        proposal={
            "experiment_id": "EXP-GATE-SUMMARY-ROUTE-001",
            "strategy_name": "GateSummaryRouteAlpha",
            "version": "0.1",
            "proposer_id": "test",
            "state": "INVALID",
            "evidence_bundle": {
                "reproducibility": {
                    "code_hash": "12345678",
                    "data_snapshot_hash": "12345678",
                    "universe_hash": "12345678",
                    "feature_graph_hash": "12345678",
                    "parameter_manifest_hash": "12345678",
                    "benchmark_version": "bench-v1",
                    "cost_model_version": "cost-v1",
                    "calendar_version": "cal-v1",
                },
                "benchmark_rung": "paper",
                "search_breadth": 1,
            },
        },
        require_semantic_evidence=False,
    )

    payload = semantic_research_adjudication_gate_summary(request)

    assert payload["schema_version"] == "semantic_research_adjudication_gate_summary/v1"
    assert payload["recommended_action"] == "ALLOW_ADJUDICATION"
