import pytest
import json
import os
import sqlite3
from datetime import datetime, timezone
from strategy_validator.core.enums import RuntimeMode, PromotionState
from strategy_validator.validator.observability import (
    compute_heartbeat,
    compute_health,
    export_operational_state,
    get_runtime_blocker_summaries,
    generate_decision_telemetry
)
from strategy_validator.validator.readiness import perform_readiness_check
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.experiments import ExperimentManifest, AdjudicationDecision, GateResult
from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest, Evidence, EvidenceType
from strategy_validator.contracts.execution import ExecutionRealismResult, MarketDataProvenance

@pytest.fixture
def prod_env(monkeypatch):
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "c:/absolute/production/ledger.sqlite3")

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64, data_snapshot_hash="b" * 64, universe_hash="c" * 64,
        feature_graph_hash="d" * 64, parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1", cost_model_version="v1", calendar_version="v1"
    )

def _exp(eid: str) -> ExperimentManifest:
    bundle = EvidenceBundle(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="portfolio"
    )
    return ExperimentManifest(
        experiment_id=eid,
        strategy_name="test_strat",
        version="1.0",
        proposer_id="user_1",
        evidence_bundle=bundle,
        state=PromotionState.QUARANTINED
    )

@pytest.mark.constitutional
class TestObservabilityHardening:
    def test_heartbeat_determinism(self):
        h1 = compute_heartbeat()
        h2 = compute_heartbeat()
        
        # Timestamps will differ, but config/schema/mode should be stable
        assert h1.runtime_mode == h2.runtime_mode
        assert h1.config_fingerprint == h2.config_fingerprint
        assert h1.schema_version == h2.schema_version

    def test_heartbeat_reflects_config_mutation(self, monkeypatch):
        f1 = compute_heartbeat().config_fingerprint
        
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        f2 = compute_heartbeat().config_fingerprint
        
        assert f1 != f2

    def test_blocked_readiness_disallows_adjudication(self, monkeypatch):
        # Trigger an unsafe path block
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "relative/path")
        
        heartbeat = compute_heartbeat()
        assert heartbeat.readiness_status == "BLOCKED"
        assert heartbeat.adjudication_allowed is False
        
        health = compute_health()
        assert health.status == "UNHEALTHY"
        assert "UNSAFE_LEDGER_PATH" in str(health.issues) or "LEDGER_ACCESS_FAILED" in str(health.issues)

    def test_blocker_summaries_provide_remediation_hints(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "relative/path")
        
        summaries = get_runtime_blocker_summaries()
        assert len(summaries) > 0
        s = summaries[0]
        assert s.severity == "CRITICAL"
        assert s.remediation_hint is not None

    def test_json_export_is_well_formed(self):
        export = export_operational_state(format="json")
        data = json.loads(export)
        
        assert "heartbeat" in data
        assert "health" in data
        assert data["heartbeat"]["runtime_mode"] in ("DEV", "PRODUCTION", "TEST")

    def test_decision_telemetry_captures_production_impact(self):
        # Create a decision that was downgraded by production policy
        # We'll use the model directly to test the generator
        decision = AdjudicationDecision(
            decided_at=datetime.now(timezone.utc),
            previous_state=PromotionState.QUARANTINED,
            new_state=PromotionState.INVALID,
            gate_results=[GateResult(gate_name="BenchmarkSuccess", passed=True)],
            summary_notes=["STRICT_PRODUCTION_BLOCKER: PROMOTABLE rejected due to provisional data."],
            runtime_mode=RuntimeMode.PRODUCTION,
            config_fingerprint="abc123456789",
            execution_report=ExecutionRealismResult(
                impact_model_mode="NONLINEAR_HEURISTIC",
                market_data_provenance=MarketDataProvenance(
                    liquidity_source_mode="PROVISIONAL",
                    borrow_source_mode="NONE",
                    fallback_applied=True,
                    fallback_reason="TEST_FALLBACK",
                    liquidity_freshness_status="STALE",
                    borrow_freshness_status="FRESH",
                    liquidity_provider_status="STALE",
                    borrow_provider_status="SUCCESS",
                ),
            ),
        )

        telemetry = generate_decision_telemetry(decision, "EXP-1")
        assert telemetry.final_promotion_state == PromotionState.INVALID
        assert telemetry.production_policy_impacted is True
        assert telemetry.market_data_source_modes["liquidity"] == "PROVISIONAL"
        assert telemetry.market_data_source_modes["borrow"] == "NONE"
        assert telemetry.market_data_fallback_applied is True
        assert telemetry.market_data_fallback_reason == "TEST_FALLBACK"
        assert telemetry.liquidity_freshness_status == "STALE"
        assert telemetry.borrow_freshness_status == "FRESH"
        assert telemetry.impact_model_mode == "NONLINEAR_HEURISTIC"

    def test_decision_telemetry_includes_gate_failures(self):
        decision = AdjudicationDecision(
            decided_at=datetime.now(timezone.utc),
            previous_state=PromotionState.QUARANTINED,
            new_state=PromotionState.REJECTED,
            gate_results=[
                GateResult(gate_name="BenchmarkSuccess", passed=False, reason="FAILED"),
                GateResult(gate_name="RobustnessAudit", passed=True)
            ]
        )
        
        telemetry = generate_decision_telemetry(decision, "EXP-FAIL")
        assert "BenchmarkSuccess" in telemetry.canonical_gate_failures
        assert "RobustnessAudit" not in telemetry.canonical_gate_failures
