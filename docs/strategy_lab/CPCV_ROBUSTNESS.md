# CPCV-inspired robustness layer

**Scope:** Stronger-than-walk-forward combinatorial checks on **local filtered bars**. **Research only.** **Not a profitability guarantee.**

## Model

Contracts: `strategy_validator/contracts/strategy_cpcv.py`  
Engine: `strategy_validator/research/strategy_cpcv.py`  
Artifact per strategy: `cpcv_result.json` beside `robustness_result.json`.

## Batch configuration

Each candidate may set `robustness_mode` to `walk_forward`, `cpcv`, or `both` (default `both`). When sample size is insufficient, CPCV returns `NOT_APPLICABLE` with warnings so walk-forward can still govern the row.

## Metrics

Bounded path count, purge/embargo spacing, PBO-like rank-stability heuristic, DSR-like score with trials penalty.

## Read-plane / UI

Strategy rows expose `cpcv_robustness_gate_status`; inspector links `cpcv_artifact_path` / digest.

## Limitations

This is an approximation of CPCV-style discipline, not a full academic implementation.

## Next graduation step

Pair CPCV artifacts with governed local bar provenance and explicit PIT manifests before any external promotion narrative.
