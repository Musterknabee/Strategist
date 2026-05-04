"""Shared pytest fixtures for strategy-validator tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
)
from strategy_validator.proposers.experiments.generator import build_strategy_proposal

# Process env vars that commonly leak from developer shells, Docker Compose, or Cursor-injected
# deployment.env. They must not change adjudication, API auth, or readiness fingerprints unless a
# test explicitly sets them after this baseline runs.
_HERMETIC_CLEAR_STRATEGY_VALIDATOR_ENV: tuple[str, ...] = (
    "STRATEGY_VALIDATOR_MODE",
    "STRATEGY_VALIDATOR_API_TOKEN",
    "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
    "STRATEGY_VALIDATOR_RESEARCH_API_TOKEN",
    "STRATEGY_VALIDATOR_LEDGER_DB_PATH",
    "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR",
    "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
    "STRATEGY_VALIDATOR_BASE_URL",
    "STRATEGY_VALIDATOR_HOST_PORT",
    "STRATEGY_VALIDATOR_ALLOW_REMOTE_NON_PRODUCTION_MUTATION_BYPASS",
    "STRATEGY_VALIDATOR_UI_CORS_ORIGINS",
    "STRATEGY_VALIDATOR_REQUIRE_ABSOLUTE_LEDGER_PATH",
    "STRATEGY_VALIDATOR_STRICT_PRODUCTION_MODE",
)


@pytest.fixture(autouse=True)
def _hermetic_strategy_validator_runtime_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip deployment-sensitive env before each test; tests opt into PRODUCTION/token/scopes.

    Ledger: clearing ``STRATEGY_VALIDATOR_LEDGER_DB_PATH`` lets ``ledger._append_only`` derive a
    per-test SQLite path from ``PYTEST_CURRENT_TEST`` (see ``_coerce_database_path``).
    """
    for key in _HERMETIC_CLEAR_STRATEGY_VALIDATOR_ENV:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(scope="module")
def _semantic_preflight_chain():
    proposal = build_strategy_proposal(
        experiment_id="EXP-SEMANTIC-PREFLIGHT-FIXTURE-001",
        strategy_name="PreflightFixture",
        proposer_id="pytest",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
    )
    bundle = build_semantic_adjudication_bundle(proposal, require_gate_artifact=False)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    return bundle, manifest


@pytest.fixture
def valid_semantic_adjudication_bundle_payload(_semantic_preflight_chain):
    bundle, _manifest = _semantic_preflight_chain
    return bundle.model_dump(mode="json")


@pytest.fixture
def valid_semantic_adjudication_bundle_manifest_payload(_semantic_preflight_chain):
    _bundle, manifest = _semantic_preflight_chain
    return manifest.model_dump(mode="json")
