"""Shared pytest fixtures for strategy-validator tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
)
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


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
