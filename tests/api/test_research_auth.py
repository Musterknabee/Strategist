from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


_PAYLOAD = {
    "proposal": {
        "experiment_id": "EXP-HTTP-RESEARCH",
        "strategy_name": "ResearchAuthSmoke",
        "version": "1.0.0",
        "proposer_id": "test",
        "evidence_bundle": {
            "reproducibility": {
                "code_hash": "a" * 64,
                "data_snapshot_hash": "b" * 64,
                "universe_hash": "c" * 64,
                "feature_graph_hash": "d" * 64,
                "parameter_manifest_hash": "e" * 64,
                "benchmark_version": "v1",
                "cost_model_version": "v1",
                "calendar_version": "v1",
            },
            "benchmark_rung": "core-equity",
            "search_breadth": 1,
        },
    }
}


def test_research_routes_require_token_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "secret-token")
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    client = TestClient(app)

    unauthorized = client.post("/research/semantic-integrity", json=_PAYLOAD)
    assert unauthorized.status_code == 401
    assert unauthorized.json()["detail"] == "INVALID_RESEARCH_API_TOKEN"

    authorized = client.post(
        "/research/semantic-integrity",
        headers={"Authorization": "Bearer secret-token"},
        json=_PAYLOAD,
    )
    assert authorized.status_code == 200
    assert authorized.json()["schema_version"] == "semantic_research_integrity/v1"


def test_research_routes_allow_local_non_production_without_token(monkeypatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    client = TestClient(app)

    response = client.post("/research/semantic-integrity", json=_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["schema_version"] == "semantic_research_integrity/v1"


def test_research_routes_prefer_dedicated_research_token(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'mutation-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_RESEARCH_API_TOKEN', 'research-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    client = TestClient(app)

    wrong_scope = client.post(
        '/research/semantic-integrity',
        headers={'Authorization': 'Bearer mutation-token'},
        json=_PAYLOAD,
    )
    assert wrong_scope.status_code == 401

    authorized = client.post(
        '/research/semantic-integrity',
        headers={'Authorization': 'Bearer research-token'},
        json=_PAYLOAD,
    )
    assert authorized.status_code == 200
