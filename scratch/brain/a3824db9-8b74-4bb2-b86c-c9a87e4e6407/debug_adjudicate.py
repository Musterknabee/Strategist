from strategy_validator.validator.orchestrator import _select_promotion_state_with_provenance
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, ReproducibilityManifest, Evidence
from strategy_validator.core.enums import EvidenceType, PromotionState
from datetime import datetime, timezone

def _repro():
    return ReproducibilityManifest(
        code_hash="a"*64, data_snapshot_hash="b"*64, universe_hash="c"*64,
        feature_graph_hash="d"*64, parameter_manifest_hash="e"*64,
        benchmark_version="bench-v1", cost_model_version="cost-v1", calendar_version="cal-v1"
    )

def _bundle():
    return EvidenceBundle(reproducibility=_repro(), benchmark_rung="L1", search_breadth=5)

def _ev(experiment_id="EXP-1", **payload):
    return Evidence(
        evidence_id="e1", experiment_id=experiment_id, evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc), payload=payload,
        source_module="tests", checksum="0"*64
    )

exp = ExperimentManifest(
    experiment_id="EXP-CON", strategy_name="s", version="1", proposer_id="p", evidence_bundle=_bundle()
)
# Add evidence to bundle
exp.evidence_bundle.evidence_items.append(
    _ev("EXP-CON", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")
)

# All basic gates pass, but DSR/PBO missing
state, decision = _select_promotion_state_with_provenance(exp, PromotionState.INVALID)

print(f"Final State: {state}")
for gr in decision.gate_results:
    # Use .dict() or getattr to handle Pydantic model
    print(f"Gate: {gr.gate_name}, Passed: {gr.passed}, Reason: {gr.reason}, Note: {gr.note}")
