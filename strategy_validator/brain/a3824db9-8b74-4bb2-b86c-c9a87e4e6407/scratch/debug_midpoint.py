from strategy_validator.validator.orchestrator import _select_promotion_state_with_provenance
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest, Evidence, SemanticArtifact
from strategy_validator.core.enums import EvidenceType, PromotionState
from datetime import datetime, timezone

def _repro():
    return ReproducibilityManifest(
        code_hash="a"*64, data_snapshot_hash="b"*64, universe_hash="c"*64,
        feature_graph_hash="d"*64, parameter_manifest_hash="e"*64,
        benchmark_version="bench-v1", cost_model_version="cost-v1", calendar_version="cal-v1"
    )

def _passing_bundle():
    b = EvidenceBundle(reproducibility=_repro(), benchmark_rung="L1", search_breadth=5)
    b.dsr_estimate = 0.5
    b.pbo_estimate = 0.1
    b.cpcv_passed = True
    b.cpcv_folds = 5
    b.cpcv_path_coverage = 1.0
    b.cpcv_path_stability = 0.1
    b.decoy_survival_passed = True
    b.decoy_suite_version = "decoy-v1"
    b.decoy_coverage = 1.0
    b.incrementality_significant = True
    b.incrementality_p_value = 0.001
    return b

def _ev(experiment_id="EXP-MID", **payload):
    # Baseline passing evidence defaults
    defaults = {
        "pit_integrity_ok": True,
        "benchmark_passed": True,
        "benchmark_delta": 0.02,
        "benchmark_id": "SPY",
        "benchmark_version": "bench-v1",
    }
    defaults.update(payload)
    return Evidence(
        evidence_id="e1", experiment_id=experiment_id, evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc), payload=defaults,
        source_module="tests", checksum="0"*64
    )

exp = ExperimentManifest(
    experiment_id="EXP-MID", strategy_name="s", version="1", proposer_id="p", evidence_bundle=_passing_bundle()
)
# Midpoint only
evidence = [_ev("EXP-MID", midpoint_only=True)]
exp.evidence_bundle.evidence_items.extend(evidence)

state, decision = _select_promotion_state_with_provenance(exp, PromotionState.INVALID)

print(f"Final State: {state}")
for gr in decision.gate_results:
    print(f"Gate: {gr.gate_name}, Passed: {gr.passed}, Reason: {gr.reason}, Note: {gr.note}")
